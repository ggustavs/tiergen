"""The Docker backend: a run manifest's networks and containers on the local Linux daemon.

Images are pulled first, so a missing one fails before anything exists. Everything created
carries ``tiergen.run=<run>``, so ``down`` finds it without any state and
cleans up after a failed ``up``. A container is created attached to its first network at
its planned address, then connected to each further network; attaching one at a time is
what makes the interface order inside the container follow the manifest. Routes are
installed with ``ip route add`` once the container runs, and a forwarder gets
``net.ipv4.ip_forward`` set; both were tried against the daemon before this was written.

An agent host runs the agent image, built here from the workspace when the daemon lacks
it, with the run directory mounted read-only at ``/tiergen/run`` and its own
``run/out/<instance>`` read-write at ``/tiergen/out``, a private cgroup namespace,
``SYS_ADMIN`` and no AppArmor confinement, which is what a cgroup per invocation costs
(section 10 of the design): the daemon's default profile denies every mount, the remount
of the cgroup filesystem included, on hosts that have AppArmor.
"""

import tempfile
from collections.abc import Callable
from pathlib import Path

from tiergen.backends.infra.docker import image
from tiergen.backends.infra.docker._client import CgroupNs, Client, DaemonClient
from tiergen.core.program import flat_id
from tiergen.interfaces import HostSpec, HostState, RunManifest, RunState

RUN_LABEL = "tiergen.run"
INSTANCE_LABEL = "tiergen.instance"
NETWORK_LABEL = "tiergen.network"
RUN_MOUNT = "/tiergen/run"
OUT_MOUNT = "/tiergen/out"
AGENT_SECURITY = ("apparmor=unconfined",)


def network_name(run: str, network: str) -> str:
    return f"tiergen-{run}-{network}"


def container_name(run: str, instance: str) -> str:
    """``lab/web_server[0]`` becomes ``tiergen-<run>-lab-web_server-0``; the real id is a label."""
    flat = instance.replace("/", "-").replace("[", "-").replace("]", "")
    return f"tiergen-{run}-{flat}"


class DockerBackend:
    id = "docker"

    def __init__(self, client: Callable[[], Client] = DaemonClient) -> None:
        self._connect = client

    def up(self, manifest: RunManifest, run_dir: Path) -> RunState:
        client = self._connect()
        run = {RUN_LABEL: manifest.run}
        state = RunState(manifest.run, self.id)
        tags: dict[str, str] = {}
        if any(h.agent for h in manifest.hosts):
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
                    client, manifest.run, host, tags.get(host.image, host.image), run_dir
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

    @staticmethod
    def _create(client: Client, run: str, host: HostSpec, img: str, run_dir: Path) -> HostState:
        first, *rest = host.attachments
        name = container_name(run, host.instance)
        # Installing a route needs NET_ADMIN inside the container; forwarding needs the sysctl.
        cap_add = {*host.cap_add, *(("NET_ADMIN",) if host.routes else ())}
        sysctls = {"net.ipv4.ip_forward": "1"} if host.forwards else {}
        mounts: list[tuple[Path, str, bool]] = []
        cgroupns: CgroupNs | None = None
        security_opt: tuple[str, ...] = ()
        if host.agent:
            out = run_dir.resolve() / "out" / flat_id(host.instance)
            out.mkdir(parents=True, exist_ok=True)
            mounts = [(run_dir.resolve(), RUN_MOUNT, True), (out, OUT_MOUNT, False)]
            cap_add.add("SYS_ADMIN")
            cgroupns = "private"
            security_opt = AGENT_SECURITY
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
            security_opt,
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
