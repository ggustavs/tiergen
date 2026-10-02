"""The backend's logic against a fake daemon: order of operations, labels, cleanup."""

from collections.abc import Mapping, Sequence

import pytest

from tiergen.backends.infra.docker.backend import DockerBackend, container_name, network_name
from tiergen.interfaces import Attachment, BackendError, HostSpec, NetworkSpec, RunManifest

MANIFEST = RunManifest(
    "r",
    "docker",
    (
        NetworkSpec("lan", "10.0.0.0/24", "10.0.0.1", "data", True),
        NetworkSpec("mgmt", "10.9.0.0/24", "10.9.0.1", "management", False),
    ),
    (
        HostSpec(
            "lab/ws[0]",
            "ws",
            "img",
            ("sleep", "infinity"),
            ("NET_RAW",),
            (Attachment("lan", "10.0.0.2"), Attachment("mgmt", "10.9.0.2")),
        ),
        HostSpec(
            "lab/web[0]",
            "web",
            "img",
            (),
            (),
            (Attachment("lan", "10.0.0.80"), Attachment("mgmt", "10.9.0.3")),
        ),
    ),
)


class FakeClient:
    def __init__(self, fail_on: str | None = None) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.live_containers: dict[str, dict[str, str]] = {}
        self.live_networks: dict[str, dict[str, str]] = {}
        self.fail_on = fail_on

    def ensure_image(self, image: str) -> None:
        self.calls.append(("image", image))

    def create_network(
        self, name: str, cidr: str, gateway: str, internal: bool, labels: Mapping[str, str]
    ) -> None:
        self.calls.append(("network", name, cidr, gateway, internal))
        self.live_networks[name] = dict(labels)

    def create_container(
        self,
        name: str,
        image: str,
        command: Sequence[str],
        cap_add: Sequence[str],
        labels: Mapping[str, str],
        network: str,
        address: str,
    ) -> None:
        if self.fail_on == name:
            raise BackendError(f"image {image!r} is not available")
        self.calls.append(("create", name, image, tuple(command), tuple(cap_add), network, address))
        self.live_containers[name] = dict(labels)

    def connect(self, container: str, network: str, address: str) -> None:
        self.calls.append(("connect", container, network, address))

    def start(self, container: str) -> None:
        self.calls.append(("start", container))

    def containers(self, labels: Mapping[str, str]) -> list[str]:
        return [n for n, held in self.live_containers.items() if labels.items() <= held.items()]

    def networks(self, labels: Mapping[str, str]) -> list[str]:
        return [n for n, held in self.live_networks.items() if labels.items() <= held.items()]

    def remove_container(self, name: str) -> None:
        self.calls.append(("rm", name))
        self.live_containers.pop(name, None)

    def remove_network(self, name: str) -> None:
        self.calls.append(("rm-net", name))
        self.live_networks.pop(name, None)

    def addresses(self, container: str) -> dict[str, str]:
        return {}


def test_up_creates_networks_then_containers_attached_one_network_at_a_time() -> None:
    fake = FakeClient()
    DockerBackend(lambda: fake).up(MANIFEST)
    assert fake.calls == [
        ("image", "img"),
        ("network", "tiergen-r-lan", "10.0.0.0/24", "10.0.0.1", True),
        ("network", "tiergen-r-mgmt", "10.9.0.0/24", "10.9.0.1", False),
        (
            "create",
            "tiergen-r-lab-ws-0",
            "img",
            ("sleep", "infinity"),
            ("NET_RAW",),
            "tiergen-r-lan",
            "10.0.0.2",
        ),
        ("connect", "tiergen-r-lab-ws-0", "tiergen-r-mgmt", "10.9.0.2"),
        ("create", "tiergen-r-lab-web-0", "img", (), (), "tiergen-r-lan", "10.0.0.80"),
        ("connect", "tiergen-r-lab-web-0", "tiergen-r-mgmt", "10.9.0.3"),
        ("start", "tiergen-r-lab-ws-0"),
        ("start", "tiergen-r-lab-web-0"),
    ]
    assert fake.live_containers["tiergen-r-lab-web-0"] == {
        "tiergen.run": "r",
        "tiergen.instance": "lab/web[0]",
    }
    assert fake.live_networks["tiergen-r-lan"] == {"tiergen.run": "r", "tiergen.network": "lan"}


def test_down_removes_containers_before_networks_and_nothing_else() -> None:
    fake = FakeClient()
    fake.live_networks["other"] = {"tiergen.run": "someone-else"}
    backend = DockerBackend(lambda: fake)
    backend.up(MANIFEST)
    fake.calls.clear()
    backend.down(MANIFEST)
    assert fake.calls == [
        ("rm", "tiergen-r-lab-ws-0"),
        ("rm", "tiergen-r-lab-web-0"),
        ("rm-net", "tiergen-r-lan"),
        ("rm-net", "tiergen-r-mgmt"),
    ]
    assert list(fake.live_networks) == ["other"]


def test_a_failed_up_removes_what_it_had_created_and_re_raises() -> None:
    fake = FakeClient(fail_on="tiergen-r-lab-web-0")
    with pytest.raises(BackendError, match="not available"):
        DockerBackend(lambda: fake).up(MANIFEST)
    assert fake.live_containers == {}
    assert fake.live_networks == {}
    assert ("rm", "tiergen-r-lab-ws-0") in fake.calls


def test_names_are_daemon_unique_and_keep_the_instance_recoverable() -> None:
    assert network_name("linux_slice", "lan") == "tiergen-linux_slice-lan"
    assert (
        container_name("linux_slice", "lab/web_server[0]") == "tiergen-linux_slice-lab-web_server-0"
    )
