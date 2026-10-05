"""The Docker backend: a run manifest's networks and containers on the local Linux daemon.

Images are pulled first, so a missing one fails before anything exists. Everything created
carries ``tiergen.run=<run>``, so ``down`` finds it without any state and
cleans up after a failed ``up``. A container is created attached to its first network at
its planned address, then connected to each further network; attaching one at a time is
what makes the interface order inside the container follow the manifest. Routes are
installed with ``ip route add`` once the container runs, and a forwarder gets
``net.ipv4.ip_forward`` set; both were tried against the daemon before this was written.

An agent host runs the agent image, built here from the workspace when the daemon lacks
it, with the run directory mounted read-only at ``/tiergen/run``, its own
``run/out/<instance>`` read-write at ``/tiergen/out``, and a private cgroup namespace. It
needs the daemon's user-namespace remap (design decision 4.19): under it the daemon mounts
the container's cgroup filesystem writable and owned by the container's root, so the
agent's cgroup per invocation costs no capability; without it ``up`` refuses. The remapped
root is a host uid the run directory must let in, which ``up`` does with ACLs.
"""

import subprocess
import tempfile
from collections.abc import Callable, Sequence
from pathlib import Path

from tiergen.backends.infra.docker import image
from tiergen.backends.infra.docker._client import CgroupNs, Client, DaemonClient
from tiergen.core.program import flat_id
from tiergen.interfaces import BackendError, HostSpec, HostState, RunManifest, RunState

RUN_LABEL = "tiergen.run"
INSTANCE_LABEL = "tiergen.instance"
NETWORK_LABEL = "tiergen.network"
RUN_MOUNT = "/tiergen/run"
OUT_MOUNT = "/tiergen/out"
NEEDS_REMAP = (
    "the daemon runs without a user-namespace remap, which agent hosts need (design "
    'decision 4.19): set "userns-remap" in daemon.json and restart the daemon'
)


def setfacl(args: Sequence[str]) -> None:
    """Run ``setfacl`` with ``args``; the stdlib has no ACL calls."""
    try:
        subprocess.run(["setfacl", *args], check=True, capture_output=True, text=True)
    except FileNotFoundError as err:
        raise BackendError(
            "setfacl is not installed (package acl); agent hosts need it to be let into the "
            "run directory"
        ) from err
    except subprocess.CalledProcessError as err:
        raise BackendError(f"setfacl {' '.join(args)} failed: {err.stderr.strip()}") from err


def network_name(run: str, network: str) -> str:
    return f"tiergen-{run}-{network}"


def container_name(run: str, instance: str) -> str:
    """``lab/web_server[0]`` becomes ``tiergen-<run>-lab-web_server-0``; the real id is a label."""
    flat = instance.replace("/", "-").replace("[", "-").replace("]", "")
    return f"tiergen-{run}-{flat}"


class DockerBackend:
    id = "docker"

    def __init__(
        self,
        client: Callable[[], Client] = DaemonClient,
        acl: Callable[[Sequence[str]], None] = setfacl,
    ) -> None:
        self._connect = client
        self._acl = acl

    def up(self, manifest: RunManifest, run_dir: Path) -> RunState:
        client = self._connect()
        run = {RUN_LABEL: manifest.run}
        state = RunState(manifest.run, self.id)
        tags: dict[str, str] = {}
        uid: int | None = None
        if any(h.agent for h in manifest.hosts):
            ids = client.userns()
            if ids is None:
                raise BackendError(NEEDS_REMAP)
            uid = ids[0]
            # The remapped root reads the programs and models; it writes only under out/.
            self._acl(["-R", "-m", f"u:{uid}:rX", str(run_dir.resolve())])
            tags[image.NAME] = self._agent_image(client, state)
        try:
            for name in sorted({h.image for h in manifest.hosts if h.image not in tags}):
                client.ensure_image(name)
            for net in manifest.networks:
                client.create_network(
                    network_name(manifest.run, net.name),
                    net.cidr,
                    net.gateway,
                    net.internal,
                    net.bridge,
                    {**run, NETWORK_LABEL: net.name},
                )
                state.bridges[net.name] = net.bridge
            for host in manifest.hosts:
                state.hosts[host.instance] = self._create(
                    client, manifest.run, host, tags.get(host.image, host.image), run_dir, uid
                )
            for host in manifest.hosts:
                name = container_name(manifest.run, host.instance)
                client.start(name)
                for route in host.routes:
                    client.exec(name, ["ip", "route", "add", route.cidr, "via", route.via])
        except Exception:
            self._remove(client, manifest.run)
            raise
        return state

    def down(self, manifest: RunManifest) -> None:
        self._remove(self._connect(), manifest.run)

    @staticmethod
    def _agent_image(client: Client, state: RunState) -> str:
        """The agent image's tag for this workspace, built if the daemon lacks it."""
        with tempfile.TemporaryDirectory(prefix="tiergen-image-") as tmp:
            ctx = image.context(Path(tmp))
            tag = image.tag(ctx)
            found = client.image_id(tag)
            state.images[image.NAME] = found if found is not None else client.build_image(tag, ctx)
        return tag

    def _create(
        self, client: Client, run: str, host: HostSpec, img: str, run_dir: Path, uid: int | None
    ) -> HostState:
        first, *rest = host.attachments
        name = container_name(run, host.instance)
        # Installing a route needs NET_ADMIN inside the container; forwarding needs the sysctl.
        cap_add = {*host.cap_add, *(("NET_ADMIN",) if host.routes else ())}
        sysctls = {"net.ipv4.ip_forward": "1"} if host.forwards else {}
        mounts: list[tuple[Path, str, bool]] = []
        cgroupns: CgroupNs | None = None
        if host.agent:
            assert uid is not None  # up checked the remap before creating anything
            out = run_dir.resolve() / "out" / flat_id(host.instance)
            out.mkdir(parents=True, exist_ok=True)
            self._acl(["-m", f"u:{uid}:rwx", str(out)])
            mounts = [(run_dir.resolve(), RUN_MOUNT, True), (out, OUT_MOUNT, False)]
            cgroupns = "private"
        container_id = client.create_container(
            name,
            img,
            host.command,
            sorted(cap_add),
            {RUN_LABEL: run, INSTANCE_LABEL: host.instance},
            network_name(run, first.network),
            first.address,
            first.mac,
            host.hostname,
            sysctls,
            mounts,
            cgroupns,
        )
        for attachment in rest:
            client.connect(
                name, network_name(run, attachment.network), attachment.address, attachment.mac
            )
        return HostState(name, container_id)

    @staticmethod
    def _remove(client: Client, run: str) -> None:
        labels = {RUN_LABEL: run}
        for name in client.containers(labels):
            client.remove_container(name)
        for name in client.networks(labels):
            client.remove_network(name)
