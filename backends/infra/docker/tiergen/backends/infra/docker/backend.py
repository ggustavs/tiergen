"""The Docker backend: a run manifest's networks and containers on the local Linux daemon.

Images are pulled first, so a missing one fails before anything exists. Everything created
carries ``tiergen.run=<run>``, so ``down`` finds it without any state and
cleans up after a failed ``up``. A container is created attached to its first network at
its planned address, then connected to each further network; attaching one at a time is
what makes the interface order inside the container follow the manifest. Routes are
installed with ``ip route add`` once the container runs, and a forwarder gets
``net.ipv4.ip_forward`` set; both were tried against the daemon before this was written.
"""

from collections.abc import Callable

from tiergen.backends.infra.docker._client import Client, DaemonClient
from tiergen.interfaces import HostSpec, HostState, RunManifest, RunState

RUN_LABEL = "tiergen.run"
INSTANCE_LABEL = "tiergen.instance"
NETWORK_LABEL = "tiergen.network"


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

    def up(self, manifest: RunManifest) -> RunState:
        client = self._connect()
        run = {RUN_LABEL: manifest.run}
        state = RunState(manifest.run, self.id)
        try:
            for image in sorted({h.image for h in manifest.hosts}):
                client.ensure_image(image)
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
                state.hosts[host.instance] = self._create(client, manifest.run, host)
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
    def _create(client: Client, run: str, host: HostSpec) -> HostState:
        first, *rest = host.attachments
        name = container_name(run, host.instance)
        # Installing a route needs NET_ADMIN inside the container; forwarding needs the sysctl.
        cap_add = sorted({*host.cap_add, *(("NET_ADMIN",) if host.routes else ())})
        sysctls = {"net.ipv4.ip_forward": "1"} if host.forwards else {}
        container_id = client.create_container(
            name,
            host.image,
            host.command,
            cap_add,
            {RUN_LABEL: run, INSTANCE_LABEL: host.instance},
            network_name(run, first.network),
            first.address,
            first.mac,
            host.hostname,
            sysctls,
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
