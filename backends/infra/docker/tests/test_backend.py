"""The backend's logic against a fake daemon: order of operations, labels, cleanup."""

from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from tiergen.backends.infra.docker._client import CgroupNs
from tiergen.backends.infra.docker.backend import (
    QUIESCE,
    DockerBackend,
    container_name,
    network_name,
)
from tiergen.interfaces import (
    Attachment,
    BackendError,
    HostSpec,
    NetworkSpec,
    RouteSpec,
    RunManifest,
)

MANIFEST = RunManifest(
    "r",
    "docker",
    (
        NetworkSpec("lan", "10.0.0.0/24", "10.0.0.1", "data", True, "tg-lan"),
        NetworkSpec("mgmt", "10.9.0.0/24", "10.9.0.1", "management", False, "tg-mgmt"),
    ),
    (
        HostSpec(
            "lab/ws[0]",
            "ws",
            "linux",
            "lab-ws-0",
            "img",
            ("sleep", "infinity"),
            ("NET_RAW",),
            (Attachment("lan", "10.0.0.2", "3c:ec:ef:00:00:02"), Attachment("mgmt", "10.9.0.2")),
            (RouteSpec("10.0.1.0/24", "10.0.0.80"),),
        ),
        HostSpec(
            "lab/web[0]",
            "web",
            "linux",
            "lab-web-0",
            "img",
            (),
            (),
            (Attachment("lan", "10.0.0.80"), Attachment("mgmt", "10.9.0.3")),
            (),
            True,
        ),
    ),
)
AGENT = HostSpec(
    "lab/atk[0]",
    "atk",
    "linux",
    "lab-atk-0",
    "tiergen/base-linux",
    ("tiergen-agent", "/tiergen/run/program.lab-atk-0.json"),
    ("NET_RAW",),
    (Attachment("lan", "10.0.0.9"),),
    agent=True,
)


class FakeClient:
    def __init__(
        self, fail_on: str | None = None, userns: tuple[int, int] | None = (100000, 100000)
    ) -> None:
        self.calls: list[tuple[object, ...]] = []
        self._userns = userns
        self.live_containers: dict[str, dict[str, str]] = {}
        self.live_networks: dict[str, dict[str, str]] = {}
        self.fail_on = fail_on

    def ensure_image(self, image: str) -> None:
        self.calls.append(("image", image))

    def userns(self) -> tuple[int, int] | None:
        return self._userns

    def image_id(self, tag: str) -> str | None:
        self.calls.append(("image-id", tag))
        return None

    def build_image(self, tag: str, context: Path) -> str:
        self.calls.append(("build", tag, sorted(p.name for p in context.iterdir())))
        return "sha256:built"

    def create_network(
        self,
        name: str,
        cidr: str,
        gateway: str,
        internal: bool,
        bridge: str,
        labels: Mapping[str, str],
    ) -> None:
        self.calls.append(("network", name, cidr, gateway, internal, bridge))
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
        mac: str | None,
        hostname: str,
        sysctls: Mapping[str, str],
        mounts: Sequence[tuple[Path, str, bool]],
        cgroupns: CgroupNs | None,
    ) -> str:
        if self.fail_on == name:
            raise BackendError(f"image {image!r} is not available")
        self.calls.append(
            (
                "create",
                name,
                image,
                tuple(command),
                tuple(cap_add),
                network,
                address,
                mac,
                hostname,
                dict(sysctls),
                tuple((str(s), t, ro) for s, t, ro in mounts),
                cgroupns,
            )
        )
        self.live_containers[name] = dict(labels)
        return f"id-{name}"

    def connect(self, container: str, network: str, address: str, mac: str | None) -> None:
        self.calls.append(("connect", container, network, address, mac))

    def start(self, container: str) -> None:
        self.calls.append(("start", container))

    def exec(self, container: str, command: Sequence[str]) -> None:
        self.calls.append(("exec", container, tuple(command)))

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

    def run_helper(
        self, image: str, command: Sequence[str], network: str, cap_add: Sequence[str]
    ) -> str:
        self.calls.append(("helper", image, tuple(command), network, tuple(cap_add)))
        return ""

    def start_helper(
        self,
        name: str,
        image: str,
        command: Sequence[str],
        labels: Mapping[str, str],
        mounts: Sequence[tuple[Path, str, bool]],
    ) -> str:
        self.calls.append(("start-helper", name, image, tuple(command)))
        return f"id-{name}"

    def stop_helper(self, name: str, timeout: float = 10.0) -> None:
        self.calls.append(("stop-helper", name))

    def pid(self, container: str) -> int:
        return 1

    def logs(self, container: str) -> str:
        return ""


def test_up_creates_networks_then_containers_attached_one_network_at_a_time(
    tmp_path: Path,
) -> None:
    fake = FakeClient()
    state = DockerBackend(lambda: fake).up(MANIFEST, tmp_path)
    assert fake.calls == [
        ("image", "img"),
        ("network", "tiergen-r-lan", "10.0.0.0/24", "10.0.0.1", True, "tg-lan"),
        ("network", "tiergen-r-mgmt", "10.9.0.0/24", "10.9.0.1", False, "tg-mgmt"),
        # NET_ADMIN joins the asked-for NET_RAW because the host has a route to install.
        (
            "create",
            "tiergen-r-lab-ws-0",
            "img",
            ("sleep", "infinity"),
            ("NET_ADMIN", "NET_RAW"),
            "tiergen-r-lan",
            "10.0.0.2",
            "3c:ec:ef:00:00:02",
            "lab-ws-0",
            {},
            (),
            None,
        ),
        ("connect", "tiergen-r-lab-ws-0", "tiergen-r-mgmt", "10.9.0.2", None),
        # The forwarder gets the sysctl and nothing it did not ask for.
        (
            "create",
            "tiergen-r-lab-web-0",
            "img",
            (),
            (),
            "tiergen-r-lan",
            "10.0.0.80",
            None,
            "lab-web-0",
            {"net.ipv4.ip_forward": "1"},
            (),
            None,
        ),
        ("connect", "tiergen-r-lab-web-0", "tiergen-r-mgmt", "10.9.0.3", None),
        ("start", "tiergen-r-lab-ws-0"),
        ("exec", "tiergen-r-lab-ws-0", ("ip", "route", "add", "10.0.1.0/24", "via", "10.0.0.80")),
        ("start", "tiergen-r-lab-web-0"),
    ]
    assert state.hosts["lab/ws[0]"].id == "id-tiergen-r-lab-ws-0"
    assert state.bridges == {"lan": "tg-lan", "mgmt": "tg-mgmt"}
    assert state.images == {}
    assert fake.live_containers["tiergen-r-lab-web-0"] == {
        "tiergen.run": "r",
        "tiergen.instance": "lab/web[0]",
    }
    assert fake.live_networks["tiergen-r-lan"] == {"tiergen.run": "r", "tiergen.network": "lan"}


def test_an_agent_host_gets_the_image_the_mounts_and_its_cgroups(tmp_path: Path) -> None:
    fake = FakeClient()
    acls: list[list[str]] = []
    manifest = RunManifest("r", "docker", MANIFEST.networks[:1], (AGENT,))
    state = DockerBackend(lambda: fake, acl=lambda a: acls.append(list(a))).up(
        manifest, tmp_path / "run"
    )
    tag = fake.calls[0][1]
    assert isinstance(tag, str)
    assert tag.startswith("tiergen/base-linux:")
    assert len(tag.split(":")[1]) == 12
    # The daemon lacked it, so it was built from a context holding the Dockerfile and the
    # members; nothing else is pulled, and the id of what was built is in the state.
    assert fake.calls[1] == (
        "build",
        tag,
        ["Dockerfile", "core", "impls", "interfaces", "protocols", "runtime"],
    )
    assert ("image", "tiergen/base-linux") not in fake.calls
    assert state.images == {"tiergen/base-linux": "sha256:built"}
    create = next(c for c in fake.calls if c[0] == "create")
    assert create[2] == tag
    assert create[3] == ("tiergen-agent", "/tiergen/run/program.lab-atk-0.json")
    assert create[4] == ("NET_RAW",)  # nothing added: the remap makes the cgroups writable
    run_dir = (tmp_path / "run").resolve()
    assert create[10] == (
        (str(run_dir), "/tiergen/run", True),
        (str(run_dir / "out" / "lab-atk-0"), "/tiergen/out", False),
    )
    assert create[11] == "private"
    assert len(create) == 12
    assert (tmp_path / "run" / "out" / "lab-atk-0").is_dir()
    # The remapped root is let into the run directory to read and into its out directory to write.
    assert acls == [
        ["-R", "-m", "u:100000:rX", str(run_dir)],
        ["-m", "u:100000:rwx", str(run_dir / "out" / "lab-atk-0")],
    ]


def test_without_the_remap_agent_hosts_are_refused_before_anything_exists(
    tmp_path: Path,
) -> None:
    fake = FakeClient(userns=None)
    manifest = RunManifest("r", "docker", MANIFEST.networks[:1], (AGENT,))
    with pytest.raises(BackendError, match=r"4\.19"):
        DockerBackend(lambda: fake, acl=lambda a: None).up(manifest, tmp_path)
    assert fake.calls == []
    assert fake.live_containers == {}
    # Hosts from custom images need no remap.
    state = DockerBackend(lambda: fake).up(MANIFEST, tmp_path)
    assert set(state.hosts) == {"lab/ws[0]", "lab/web[0]"}


def test_quiesce_turns_segmentation_off_inside_every_host(tmp_path: Path) -> None:
    fake = FakeClient()
    backend = DockerBackend(lambda: fake, acl=lambda a: None)
    manifest = RunManifest("r", "docker", MANIFEST.networks, (*MANIFEST.hosts, AGENT))
    state = backend.up(manifest, tmp_path / "run")
    fake.calls.clear()
    backend.quiesce(manifest, state)
    helpers = [c for c in fake.calls if c[0] == "helper"]
    assert [c[3] for c in helpers] == [
        "container:tiergen-r-lab-ws-0",
        "container:tiergen-r-lab-web-0",
        "container:tiergen-r-lab-atk-0",
    ]
    image = helpers[0][1]
    assert isinstance(image, str)
    assert image.startswith("tiergen/base-linux:")
    assert all(c[2] == ("sh", "-c", QUIESCE) and c[4] == ("NET_ADMIN",) for c in helpers)
    assert ("image-id", image) in fake.calls  # found or built, never pulled


def test_down_removes_containers_before_networks_and_nothing_else(tmp_path: Path) -> None:
    fake = FakeClient()
    fake.live_networks["other"] = {"tiergen.run": "someone-else"}
    backend = DockerBackend(lambda: fake)
    backend.up(MANIFEST, tmp_path)
    fake.calls.clear()
    backend.down(MANIFEST)
    assert fake.calls == [
        ("rm", "tiergen-r-lab-ws-0"),
        ("rm", "tiergen-r-lab-web-0"),
        ("rm-net", "tiergen-r-lan"),
        ("rm-net", "tiergen-r-mgmt"),
    ]
    assert list(fake.live_networks) == ["other"]


def test_a_failed_up_removes_what_it_had_created_and_re_raises(tmp_path: Path) -> None:
    fake = FakeClient(fail_on="tiergen-r-lab-web-0")
    with pytest.raises(BackendError, match="not available"):
        DockerBackend(lambda: fake).up(MANIFEST, tmp_path)
    assert fake.live_containers == {}
    assert fake.live_networks == {}
    assert ("rm", "tiergen-r-lab-ws-0") in fake.calls


def test_names_are_daemon_unique_and_keep_the_instance_recoverable() -> None:
    assert network_name("linux_slice", "lan") == "tiergen-linux_slice-lan"
    assert (
        container_name("linux_slice", "lab/web_server[0]") == "tiergen-linux_slice-lab-web_server-0"
    )
