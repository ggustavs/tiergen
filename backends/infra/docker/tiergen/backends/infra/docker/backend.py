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
``run/out/<instance>`` read-write at ``/tiergen/out``, and a private cgroup namespace. Its
agent holds at the manifest's gate until ``start`` creates it with an ``exec``, since the
collector attaches to the container's cgroup, which exists only once the container runs. It
needs the daemon's user-namespace remap (design decision 4.19): under it the daemon mounts
the container's cgroup filesystem writable and owned by the container's root, so the
agent's cgroup per invocation costs no capability; without it ``up`` refuses. The remapped
root is a host uid the run directory must let in, which ``up`` does with ACLs.
"""

from collections.abc import Callable, Sequence
from pathlib import Path

from tiergen.backends.infra.docker import image
from tiergen.backends.infra.docker._client import CgroupNs, Client, DaemonClient, setfacl
from tiergen.core.program import flat_id
from tiergen.interfaces import BackendError, HostSpec, HostState, RunManifest, RunState

RUN_LABEL = "tiergen.run"
INSTANCE_LABEL = "tiergen.instance"
NETWORK_LABEL = "tiergen.network"
RUN_MOUNT = "/tiergen/run"
OUT_MOUNT = "/tiergen/out"
QUIESCE = "for d in /sys/class/net/eth*; do ethtool -K $(basename $d) tso off gso off tx off; done"
"""What makes a container put wire-sized, correctly checksummed frames on its bridge.
Measured 2026-10-05: a 20 MB HTTP transfer captured on the bridge showed 65 KB frames until
TSO and GSO were off on the sending container's own interface (1514 bytes after); the
host-side veths and the bridge made no difference, so they are left alone. Measured
2026-10-07: with checksum offload still on, frames leave the veth with checksums never
computed, and Zeek silently drops them (its own warning says so); ``tx off`` has the kernel
compute them before the frame leaves."""
NEEDS_REMAP = (
    "the daemon runs without a user-namespace remap, which agent hosts need (design "
    'decision 4.19): set "userns-remap" in daemon.json and restart the daemon'
)


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

    def up(self, manifest: RunManifest, run_dir: Path, start: bool = True) -> RunState:
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
            tags[image.NAME] = image.ensure(client, image.agent(), state)
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
            if start:
                self._start(client, manifest, state)
        except Exception:
            self._remove(client, manifest.run)
            raise
        return state

    def start(self, manifest: RunManifest, state: RunState) -> None:
        self._start(self._connect(), manifest, state)

    def down(self, manifest: RunManifest) -> None:
        self._remove(self._connect(), manifest.run)

    def quiesce(self, manifest: RunManifest, state: RunState) -> None:
        """TSO and GSO off on every interface of every host, through a helper from the agent
        image that joins the host's network namespace with ``NET_ADMIN``."""
        client = self._connect()
        tag = image.ensure(client, image.agent(), state)
        for host in manifest.hosts:
            name = container_name(manifest.run, host.instance)
            client.run_helper(tag, ["sh", "-c", QUIESCE], f"container:{name}", ["NET_ADMIN"])

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
    def _start(client: Client, manifest: RunManifest, state: RunState) -> None:
        """Create each agent's gate inside its container; the agent is waiting on it."""
        for host in manifest.hosts:
            if host.gate is not None:
                client.exec(state.hosts[host.instance].name, ["touch", host.gate])

    @staticmethod
    def _remove(client: Client, run: str) -> None:
        labels = {RUN_LABEL: run}
        for name in client.containers(labels):
            client.remove_container(name)
        for name in client.networks(labels):
            client.remove_network(name)
