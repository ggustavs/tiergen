import io
import json
import tarfile
from collections.abc import Sequence
from pathlib import Path

import pytest

from tiergen.backends.infra.libvirt._client import Exec
from tiergen.backends.infra.libvirt.backend import (
    POOL,
    IsoWriter,
    LibvirtBackend,
    derived_mac,
    domain_name,
    domain_xml,
    template_volume,
)
from tiergen.backends.infra.libvirt.iso import write_iso
from tiergen.interfaces import (
    Attachment,
    BackendError,
    HostSpec,
    NetworkSpec,
    RouteSpec,
    RunManifest,
)

LAN = NetworkSpec("lan", "10.0.0.0/24", "10.0.0.1", "data", True, "tg-lan")
MGMT = NetworkSpec("mgmt", "10.9.0.0/16", "10.9.0.1", "management", False, "tg-mgmt")
WS = HostSpec(
    "lab/ws[0]",
    "ws",
    "linux",
    "lab-ws-0",
    "tiergen/base-linux",
    ("tiergen-agent", "/tiergen/run/program.lab-ws-0.json", "--go", "/tiergen/go"),
    (),
    (Attachment("lan", "10.0.0.2", "3c:ec:ef:00:00:02"), Attachment("mgmt", "10.9.0.2")),
    routes=(RouteSpec("10.0.1.0/24", "10.0.0.80"),),
    agent=True,
    gate="/tiergen/go",
)
DC = HostSpec(
    "hq/dc[0]",
    "dc",
    "windows",
    "hq-dc-0",
    "win2022-dc",
    (),
    (),
    (Attachment("lan", "10.0.0.10", "00:15:5d:00:00:0a"),),
)
MANIFEST = RunManifest("r", "libvirt", (LAN, MGMT), (WS, DC))


class FakeClient:
    def __init__(self, bridges: set[str] | None = None, templates: Sequence[str] = ()) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.bridges = bridges or set()
        self.volumes_: list[str] = list(templates)
        self.networks_: list[str] = []
        self.domains_: dict[str, str] = {}
        self.xml: dict[str, str] = {}
        self.uploaded: dict[str, bytes] = {}
        self.written: list[tuple[str, str, bytes]] = []
        self.exec_results: dict[str, Exec] = {}
        self.files: dict[tuple[str, str], bytes] = {}
        self.time = 1_000_000.0

    def ensure_pool(self, name: str, path: str) -> None:
        self.calls.append(("pool", name, path))

    def volumes(self, pool: str) -> list[str]:
        return sorted(self.volumes_)

    def volume_path(self, pool: str, name: str) -> str:
        return f"/pool/{name}"

    def upload(self, pool: str, name: str, source: Path, fmt: str) -> None:
        self.calls.append(("upload", name, fmt))
        self.volumes_.append(name)
        self.uploaded[name] = source.read_bytes()

    def clone(self, pool: str, name: str, backing: str, capacity_gib: int) -> None:
        self.calls.append(("clone", name, backing, capacity_gib))
        self.volumes_.append(name)

    def delete_volume(self, pool: str, name: str) -> None:
        self.calls.append(("rm-vol", name))
        self.volumes_.remove(name)

    def bridge_exists(self, bridge: str) -> bool:
        return bridge in self.bridges

    def create_network(self, name: str, bridge: str) -> None:
        self.calls.append(("net", name, bridge))
        self.networks_.append(name)

    def networks(self) -> list[str]:
        return sorted(self.networks_)

    def destroy_network(self, name: str) -> None:
        self.calls.append(("rm-net", name))
        self.networks_.remove(name)

    def ensure_network(self, name: str) -> None:
        self.calls.append(("net-up", name))

    def create_domain(self, xml: str) -> str:
        name = xml.split("<name>")[1].split("</name>")[0]
        description = xml.split("<description>")[1].split("</description>")[0]
        self.calls.append(("domain", name))
        self.domains_[name] = description
        self.xml[name] = xml
        return f"uuid-{name}"

    def domains(self) -> dict[str, str]:
        return dict(self.domains_)

    def destroy_domain(self, name: str) -> None:
        self.calls.append(("rm-domain", name))
        del self.domains_[name]

    def agent_ready(self, domain: str, timeout_s: float) -> bool:
        self.calls.append(("ping", domain))
        return True

    def guest_exec(
        self, domain: str, path: str, args: Sequence[str] = (), timeout_s: float = 300.0
    ) -> Exec:
        self.calls.append(("exec", domain, path, tuple(args)))
        return self.exec_results.get(domain, Exec(0, "agent started\n", ""))

    def guest_write(self, domain: str, path: str, data: bytes) -> None:
        self.calls.append(("write", domain, path))
        self.written.append((domain, path, data))

    def guest_read(self, domain: str, path: str) -> bytes:
        self.calls.append(("read", domain, path))
        return self.files[(domain, path)]

    def guest_time(self, domain: str) -> float:
        return self.time - 0.25  # the guest runs a quarter second behind

    def guest_interfaces(self, domain: str) -> dict[str, list[str]]:
        return {}


def fake_wheels(into: Path) -> None:
    (into / "tiergen_core-0.0.1-py3-none-any.whl").write_bytes(b"not really a wheel")


def fake_iso(target: Path, root: Path) -> None:
    """Stands in for xorriso: the staged tree's file list, which the real test checks."""
    target.write_text("\n".join(sorted(str(p.relative_to(root)) for p in root.rglob("*"))))


def _backend(fake: FakeClient, iso: IsoWriter = fake_iso) -> LibvirtBackend:
    return LibvirtBackend(
        lambda: fake, wheels=fake_wheels, iso=iso, pool_path="/pool", clock=lambda: fake.time
    )


def test_up_clones_templates_writes_run_isos_and_starts_domains_on_the_bridges(
    tmp_path: Path,
) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "scenario.json").write_text("{}")
    (run_dir / "program.lab-ws-0.json").write_text("{}")
    (run_dir / "models").mkdir()
    (run_dir / "models" / "x.zeek").write_text("")
    (run_dir / "out").mkdir()  # an earlier run's outputs stay out of the ISO
    fake = FakeClient(
        bridges={"tg-lan"}, templates=["template-linux-agent.qcow2", "template-win2022-dc.qcow2"]
    )
    state = _backend(fake).up(MANIFEST, run_dir, start=False)

    assert fake.calls[0] == ("pool", POOL, "/pool")
    # The LAN bridge exists (Docker's); the management bridge does not, so it is made here.
    assert ("net", "tiergen-r-mgmt", "tg-mgmt") in fake.calls
    assert not any(c[0] == "net" and c[2] == "tg-lan" for c in fake.calls)
    assert state.bridges == {"lan": "tg-lan", "mgmt": "tg-mgmt"}
    assert ("clone", "tiergen-r-lab-ws-0.qcow2", "template-linux-agent.qcow2", 20) in fake.calls
    assert ("clone", "tiergen-r-hq-dc-0.qcow2", "template-win2022-dc.qcow2", 64) in fake.calls
    assert ("upload", "tiergen-r-lab-ws-0-run.iso", "raw") in fake.calls
    xml = fake.xml["tiergen-r-lab-ws-0"]
    assert "<source bridge='tg-lan'/><mac address='3c:ec:ef:00:00:02'/>" in xml
    assert (
        f"<source bridge='tg-mgmt'/><mac address='{derived_mac('r', 'lab/ws[0]', 'mgmt')}'/>" in xml
    )
    assert "volume='tiergen-r-lab-ws-0.qcow2'" in xml
    assert "volume='tiergen-r-lab-ws-0-run.iso'" in xml
    assert "<memory unit='MiB'>2048</memory>" in xml
    assert "<memory unit='MiB'>4096</memory>" in fake.xml["tiergen-r-hq-dc-0"]
    # The disk boots before the run ISO; only the Windows guest gets Hyper-V enlightenments.
    assert xml.index("<boot order='1'/>") < xml.index("<boot order='2'/>")
    assert "<hyperv" not in xml
    assert "<hyperv mode='custom'>" in fake.xml["tiergen-r-hq-dc-0"]
    assert "<timer name='hypervclock' present='yes'/>" in fake.xml["tiergen-r-hq-dc-0"]
    assert json.loads(fake.domains_["tiergen-r-lab-ws-0"]) == {
        "tiergen.run": "r",
        "tiergen.instance": "lab/ws[0]",
    }
    assert state.hosts["lab/ws[0]"].id == "uuid-tiergen-r-lab-ws-0"
    # Every guest's clock was read; the agent host was bootstrapped, the DC left alone.
    assert state.hosts["lab/ws[0]"].clock_offset_s == pytest.approx(0.25)
    assert state.hosts["hq/dc[0]"].clock_offset_s == pytest.approx(0.25)
    execs = [c for c in fake.calls if c[0] == "exec"]
    assert len(execs) == 1
    assert execs[0][1] == "tiergen-r-lab-ws-0"
    assert "bootstrap.sh" in str(execs[0][3])
    # Nothing was released: start=False.
    assert fake.written == []


def test_the_run_iso_carries_the_run_the_host_entry_the_wheels_and_the_bootstrap(
    tmp_path: Path,
) -> None:
    if not _xorriso():
        pytest.skip("xorriso is not installed")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "scenario.json").write_text('{"name": "r"}')
    (run_dir / "program.lab-ws-0.json").write_text("{}")
    (run_dir / "out").mkdir()
    (run_dir / "out" / "old.txt").write_text("stale")
    fake = FakeClient(
        bridges={"tg-lan", "tg-mgmt"},
        templates=["template-linux-agent.qcow2", "template-win2022-dc.qcow2"],
    )
    _backend(fake, iso=write_iso).up(MANIFEST, run_dir, start=False)
    iso = tmp_path / "ws.iso"
    iso.write_bytes(fake.uploaded["tiergen-r-lab-ws-0-run.iso"])
    listing = _iso_listing(iso)
    assert "/run/scenario.json" in listing
    assert "/run/program.lab-ws-0.json" in listing
    assert "/host.json" in listing
    assert "/bootstrap.sh" in listing
    assert "/wheels/tiergen_core-0.0.1-py3-none-any.whl" in listing
    assert not any(p.startswith("/run/out") for p in listing)
    host = json.loads(_iso_file(iso, "/host.json", tmp_path / "host.json"))
    assert host["program"] == "program.lab-ws-0.json"
    assert host["attachments"][0] == {
        "network": "lan",
        "address": "10.0.0.2",
        "prefix": 24,
        "mac": "3c:ec:ef:00:00:02",
    }
    assert host["attachments"][1]["prefix"] == 16
    assert host["routes"] == [{"cidr": "10.0.1.0/24", "via": "10.0.0.80"}]
    assert host["gate"] == "/tiergen/go"


def test_start_writes_the_gate_and_collect_pulls_the_outputs(tmp_path: Path) -> None:
    fake = FakeClient(
        bridges={"tg-lan", "tg-mgmt"},
        templates=["template-linux-agent.qcow2", "template-win2022-dc.qcow2"],
    )
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "scenario.json").write_text("{}")
    backend = _backend(fake)
    state = backend.up(MANIFEST, run_dir, start=False)
    backend.start(MANIFEST, state)
    assert fake.written == [("tiergen-r-lab-ws-0", "/tiergen/go", b"go\n")]
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        data = b'{"key": 1}\n'
        info = tarfile.TarInfo("./invocations.jsonl")
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    fake.files[("tiergen-r-lab-ws-0", "/tiergen/out.tgz")] = buffer.getvalue()
    fake.files[("tiergen-r-lab-ws-0", "/tiergen/bootstrap.log")] = b"agent started\n"
    backend.collect(MANIFEST, state, run_dir)
    assert (run_dir / "out" / "lab-ws-0" / "invocations.jsonl").read_text() == '{"key": 1}\n'
    assert (run_dir / "out" / "lab-ws-0" / "bootstrap.log").read_text() == "agent started\n"
    assert not (run_dir / "out" / "hq-dc-0").exists()


def test_down_removes_the_run_s_domains_volumes_and_networks_and_nothing_else(
    tmp_path: Path,
) -> None:
    fake = FakeClient(
        bridges={"tg-lan"}, templates=["template-linux-agent.qcow2", "template-win2022-dc.qcow2"]
    )
    fake.domains_["other"] = json.dumps({"tiergen.run": "other"})
    fake.volumes_.append("tiergen-other-x.qcow2")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "scenario.json").write_text("{}")
    backend = _backend(fake)
    backend.up(MANIFEST, run_dir, start=False)
    fake.calls.clear()
    backend.down(MANIFEST)
    assert sorted(c for c in fake.calls if c[0] == "rm-domain") == [
        ("rm-domain", "tiergen-r-hq-dc-0"),
        ("rm-domain", "tiergen-r-lab-ws-0"),
    ]
    assert sorted(fake.volumes_) == [
        "template-linux-agent.qcow2",
        "template-win2022-dc.qcow2",
        "tiergen-other-x.qcow2",
    ]
    assert fake.networks_ == []
    assert "other" in fake.domains_


def test_a_missing_template_is_refused_before_anything_exists(tmp_path: Path) -> None:
    fake = FakeClient(bridges={"tg-lan", "tg-mgmt"}, templates=["template-linux-agent.qcow2"])
    with pytest.raises(BackendError, match=r"template-win2022-dc\.qcow2.*missing"):
        _backend(fake).up(MANIFEST, tmp_path, start=False)
    assert [c for c in fake.calls if c[0] != "pool"] == []


def test_a_failed_bootstrap_takes_the_run_down_and_says_why(tmp_path: Path) -> None:
    fake = FakeClient(
        bridges={"tg-lan", "tg-mgmt"},
        templates=["template-linux-agent.qcow2", "template-win2022-dc.qcow2"],
    )
    fake.exec_results["tiergen-r-lab-ws-0"] = Exec(1, "", "mount: no such device\n")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "scenario.json").write_text("{}")
    with pytest.raises(BackendError, match="bootstrap failed \\(1\\): mount: no such device"):
        _backend(fake).up(MANIFEST, run_dir, start=False)
    assert fake.domains_ == {}
    assert sorted(fake.volumes_) == ["template-linux-agent.qcow2", "template-win2022-dc.qcow2"]


def test_names_and_macs_are_stable() -> None:
    assert domain_name("linux_slice", "lab/web_server[0]") == "tiergen-linux_slice-lab-web_server-0"
    assert template_volume("tiergen/base-linux", "linux") == "template-linux-agent.qcow2"
    assert template_volume("win2022-dc", "windows") == "template-win2022-dc.qcow2"
    mac = derived_mac("r", "lab/ws[0]", "mgmt")
    assert mac.startswith("52:54:00:")
    assert mac == derived_mac("r", "lab/ws[0]", "mgmt")
    assert mac != derived_mac("r", "lab/ws[1]", "mgmt")


def _xorriso() -> bool:
    import shutil

    return shutil.which("xorriso") is not None


def _iso_listing(iso: Path) -> list[str]:
    import subprocess

    done = subprocess.run(
        ["xorriso", "-indev", str(iso), "-find", "/", "-type", "f"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip().strip("'") for line in done.stdout.splitlines() if line.startswith("'")]


def _iso_file(iso: Path, path: str, into: Path) -> str:
    import subprocess

    subprocess.run(
        ["xorriso", "-indev", str(iso), "-osirrox", "on", "-extract", path, str(into)],
        capture_output=True,
        text=True,
        check=True,
    )
    return into.read_text()


def test_a_build_display_keeps_the_devices_where_a_run_has_them() -> None:
    """The template build's video card has a slot of its own, so the root ports, and the
    NIC behind the first of them, are where a run's domain without a display puts them."""
    built = domain_xml(
        "b", "d", "windows", "t.qcow2", ("a.iso", "b.iso"), (), nat="default", display=True
    )
    run = domain_xml(
        "r", "d", "windows", "c.qcow2", ("run.iso",), [("tg-lan", "52:54:00:00:00:01")]
    )
    assert (
        "<video><model type='vga'/><address type='pci' domain='0x0000' bus='0x00' slot='0x0a'"
        in built
    )
    assert "<video" not in run
    assert built.count("<disk type='volume' device='cdrom'>") == 2
    assert "<target dev='sdb' bus='sata'/>" in built
