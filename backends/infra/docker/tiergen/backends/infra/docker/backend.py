"""The Docker backend: a run manifest's networks and containers on the local Linux daemon.

Images are pulled first, so a missing one fails before anything exists. Everything created
carries ``tiergen.run=<run>``, so ``down`` finds it without any state and
cleans up after a failed ``up``. A container is created attached to its first network at
its planned address, then connected to each further network; attaching one at a time is
what makes the interface order inside the container follow the manifest.
"""

from collections.abc import Callable

from tiergen.backends.infra.docker._client import Client, DaemonClient
from tiergen.interfaces import HostSpec, RunManifest

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

    def up(self, manifest: RunManifest) -> None:
        client = self._connect()
        run = {RUN_LABEL: manifest.run}
        try:
            for image in sorted({h.image for h in manifest.hosts}):
                client.ensure_image(image)
            for net in manifest.networks:
                client.create_network(
                    network_name(manifest.run, net.name),
                    net.cidr,
                    net.gateway,
                    net.internal,
                    {**run, NETWORK_LABEL: net.name},
                )
            for host in manifest.hosts:
                self._create(client, manifest.run, host)
            for host in manifest.hosts:
                client.start(container_name(manifest.run, host.instance))
        except Exception:
            self._remove(client, manifest.run)
            raise

    def down(self, manifest: RunManifest) -> None:
        self._remove(self._connect(), manifest.run)

    @staticmethod
    def _create(client: Client, run: str, host: HostSpec) -> None:
        first, *rest = host.attachments
        name = container_name(run, host.instance)
        client.create_container(
            name,
            host.image,
            host.command,
            host.cap_add,
            {RUN_LABEL: run, INSTANCE_LABEL: host.instance},
            network_name(run, first.network),
            first.address,
        )
        for attachment in rest:
            client.connect(name, network_name(run, attachment.network), attachment.address)

    @staticmethod
    def _remove(client: Client, run: str) -> None:
        labels = {RUN_LABEL: run}
        for name in client.containers(labels):
            client.remove_container(name)
        for name in client.networks(labels):
            client.remove_network(name)
