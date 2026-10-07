"""Against a real daemon: linux_slice up, browsing and scanning, and down without a trace.

Skipped when no daemon is reachable. Runs the whole example, so it also builds the agent
image the first time, which takes a few minutes.
"""

import json
import os
import re
import shutil
import socket
import struct
import subprocess
import time
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path

import pytest

from tiergen.backends.attrib._base import read_events
from tiergen.backends.attrib.linux_ebpf.backend import LinuxEbpf, helper_name, spec
from tiergen.backends.infra.docker import image
from tiergen.backends.infra.docker._client import DaemonClient
from tiergen.backends.infra.docker.backend import DockerBackend, container_name, network_name
from tiergen.cli.main import main
from tiergen.core.codec import decode, from_json, to_json
from tiergen.core.events import AppEvent, ConnEvent
from tiergen.core.records import InvocationRecord
from tiergen.interfaces import BackendError, RunManifest, RunState
from tiergen.runtime.agent_linux.records import read_records
from tiergen.runtime.capture.pcapng import Packet, read

EXAMPLES = Path(__file__).parents[4] / "examples"
pytestmark = pytest.mark.docker


@pytest.fixture(scope="module")
def daemon() -> DaemonClient:
    try:
        client = DaemonClient()
    except BackendError as err:
        pytest.skip(str(err))
    if client.userns() is None:
        pytest.skip("the daemon runs without a user-namespace remap (design decision 4.19)")
    return client


@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    assert (
        main(["build", str(EXAMPLES / "linux_slice" / "scenario.py"), "--out", str(tmp_path / "r")])
        == 0
    )
    return tmp_path / "r"


@pytest.fixture
def manifest(run_dir: Path, daemon: DaemonClient) -> Iterator[RunManifest]:
    m = from_json(RunManifest, json.loads((run_dir / "manifest.docker.json").read_text()))
    yield m
    DockerBackend().down(m)


def _docker(*args: str) -> str:
    return subprocess.run(["docker", *args], check=True, capture_output=True, text=True).stdout


def _wait(
    path: Path, wanted: Callable[[list[InvocationRecord]], bool], seconds: float
) -> list[InvocationRecord]:
    deadline = time.monotonic() + seconds
    while True:
        records = read_records(path) if path.is_file() else []
        if wanted(records) or time.monotonic() > deadline:
            return records
        time.sleep(2)


def _release(out: Path, image: str, depth: int = 2) -> None:
    """What the agents wrote belongs to the remapped root, which the user cannot delete
    inside the agents' own directories; a container as that root removes it, leaving the
    instance directories, which are the user's, empty."""
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{out}:/o",
            image,
            "find",
            "/o",
            "-mindepth",
            str(depth),
            "-delete",
        ],
        check=True,
        capture_output=True,
    )


def _tcp(packets: list[Packet]) -> list[tuple[str, str, int, int]]:
    """(source, destination, destination port, TCP flags) of every IPv4 TCP packet."""
    found: list[tuple[str, str, int, int]] = []
    for p in packets:
        d = p.data
        if len(d) < 34 or d[12:14] != b"\x08\x00" or d[23] != 6:
            continue
        ihl = (d[14] & 0x0F) * 4
        tcp = 14 + ihl
        if len(d) < tcp + 14:
            continue
        dport = struct.unpack_from(">H", d, tcp + 2)[0]
        found.append((socket.inet_ntoa(d[26:30]), socket.inet_ntoa(d[30:34]), dport, d[tcp + 13]))
    return found


def test_linux_slice_runs_its_behaviours_and_goes_down_without_a_trace(
    run_dir: Path, manifest: RunManifest, daemon: DaemonClient
) -> None:
    if shutil.which("dumpcap") is None:
        pytest.skip("dumpcap is not installed")
    plan = json.loads((run_dir / "addresses.json").read_text())
    # Both images first, so the collector and the capture start seconds after the hosts,
    # before the attacker's scan at 30 s; building them here can take minutes.
    image.ensure(daemon, image.agent(), RunState("prebuild", "docker"))
    image.ensure(daemon, spec(), RunState("prebuild", "docker"))
    backend = DockerBackend()
    state = backend.up(manifest, run_dir)
    try:
        # What tiergen infra up would have written; capture start reads it.
        (run_dir / "state.docker.json").write_text(json.dumps(to_json(state)))
        assert main(["attrib", "start", str(run_dir)]) == 0
        assert main(["capture", "start", str(run_dir)]) == 0
        captured_from = time.time()
        assert state.images["tiergen/base-linux"].startswith("sha256:")
        run = {"tiergen.run": manifest.run}
        # The hosts, plus the attribution collector, which carries the run's label too.
        assert sorted(daemon.containers(run)) == sorted(
            [
                *(container_name(manifest.run, h.instance) for h in manifest.hosts),
                helper_name(manifest.run),
            ]
        )
        for host in manifest.hosts:
            got = daemon.addresses(container_name(manifest.run, host.instance))
            want = {
                network_name(manifest.run, n): a
                for n, a in plan["addresses"][host.instance].items()
            }
            assert got == want, host.instance
        lan = json.loads(_docker("network", "inspect", network_name(manifest.run, "lan")))[0]
        assert lan["Internal"] is True
        assert lan["IPAM"]["Config"][0] == {"Subnet": "10.20.0.0/24", "Gateway": "10.20.0.1"}

        # The workstation browses the web server; the attacker scans it once recon starts.
        out = run_dir / "out"
        browsed = _wait(
            out / "lab-workstation-0" / "invocations.jsonl",
            lambda rs: any(r.outcome == "succeeded" and r.start > captured_from for r in rs),
            120,
        )
        assert browsed, (out / "lab-workstation-0" / "agent.log").read_text()
        first = browsed[0]
        assert (first.key.behaviour, first.key.action, first.key.impl) == (
            "browse",
            "web_get",
            "http.httpx",
        )
        assert first.key.invocation == "lab/workstation[0]/browse#1"
        assert first.key.targets == ("lab/web_server[0]",)
        assert first.principal.platform == "linux"
        ws_log = (out / "lab-workstation-0" / "agent.log").read_text()
        assert re.fullmatch(r"cgroup:\d+", first.principal.principal), ws_log
        scanned = _wait(
            out / "lab-attacker-0" / "invocations.jsonl",
            lambda rs: any(r.outcome == "succeeded" for r in rs),
            120,
        )
        assert scanned, (out / "lab-attacker-0" / "agent.log").read_text()
        assert scanned[0].key.action == "syn_scan"
        assert scanned[0].key.impl == "scan.nmap"
        access = (out / "lab-web_server-0" / "http.nginx" / "access.log").read_text()
        assert plan["addresses"]["lab/workstation[0]"]["lan"] in access
        assert "GET /" in access
        web_log = (out / "lab-web_server-0" / "agent.log").read_text()
        assert "http.nginx serves http/80, https/443" in web_log

        # The capture point saw the browsing and the scan, in wire-sized frames.
        assert main(["capture", "stop", str(run_dir)]) == 0
        capture = run_dir / "capture"
        assert not (capture / "state.json").exists()
        summary = json.loads((capture / "capture.json").read_text())
        assert [c["point"] for c in summary["captures"]] == ["lan-span"]
        interfaces, packets = read(capture / "lan-span.pcapng")
        assert [i.name for i in interfaces] == [state.bridges["lan"]]
        ws = plan["addresses"]["lab/workstation[0]"]["lan"]
        web = plan["addresses"]["lab/web_server[0]"]["lan"]
        atk = plan["addresses"]["lab/attacker[0]"]["lan"]
        tcp = _tcp(packets)
        assert any(src == ws and dst == web and port == 80 for src, dst, port, _ in tcp)
        syns = {
            port
            for src, dst, port, flags in tcp
            if src == atk and dst == web and flags & 0x12 == 0x02
        }
        assert len(syns) > 100, "the SYN scan of ports 1-1024 is in the capture"
        assert max(len(p.data) for p in packets) <= 1514
        clocks = json.loads((capture / "offsets.json").read_text())
        assert clocks == {
            h.instance: {"offset_s": 0.0, "method": "shared-kernel"} for h in manifest.hosts
        }
        assert (
            "dumpcap"
            not in subprocess.run(
                ["pgrep", "-af", "lan-span.pcapng"], capture_output=True, text=True
            ).stdout
        )
        # The agents' files belong to the remapped root and are readable by the user through
        # the ACL up set; the directories are the user's own.
        assert (out / "lab-web_server-0" / "http.nginx" / "access.log").stat().st_uid != os.getuid()
        assert (out / "lab-web_server-0").stat().st_uid == os.getuid()
        assert main(["attrib", "stop", str(run_dir)]) == 0
        # Both sensors read the capture at their pinned versions and agree on what they saw.
        assert main(["sensors", "run", str(run_dir)]) == 0
        for name in ("zeek", "suricata"):
            lines = (
                (run_dir / "sensors" / name / "lan-span" / "events.jsonl").read_text().splitlines()
            )
            seen = [decode(ConnEvent | AppEvent, json.loads(line)) for line in lines]
            conns = [e for e in seen if isinstance(e, ConnEvent)]
            apps = [e for e in seen if isinstance(e, AppEvent)]
            assert conns, name
            assert all(c.flow.sensor == name and c.flow.capture_point == "lan-span" for c in conns)
            browsing = [
                c for c in conns if (c.five_tuple.orig_addr, c.five_tuple.resp_addr) == (ws, web)
            ]
            assert browsing, name
            assert all(c.five_tuple.resp_port == 80 for c in browsing), name
            assert {c.state for c in browsing} <= {"closed", "established"}, name
            refused = [c for c in conns if c.five_tuple.orig_addr == atk and c.state == "rejected"]
            assert len(refused) > 100, name
            http = [a for a in apps if a.protocol == "http"]
            assert http, name
            assert all(str(a.fields.get("user_agent", "")).startswith("python-httpx") for a in http)
            assert all(a.flow in {c.flow for c in browsing} for a in http), name
            digest = json.loads((run_dir / "sensors" / name / "image.json").read_text())["digest"]
            assert "@sha256:" in digest, name
        # The kernel saw the browsing from the workstation's invocation cgroups and the scan
        # from the attacker's, and every invocation that succeeded has a record inside it.
        events = list(read_events(run_dir / "attrib" / "events.jsonl"))
        assert events[0].ev == "start"
        ws_ids = {int(r.principal.principal.split(":")[1]) for r in browsed}
        connects = [e for e in events if e.ev == "connect" and e.cg in ws_ids]
        assert connects, [e for e in events if e.ev == "connect"][:5]
        assert all((e.src, e.dst, e.dport) == (ws, web, 80) for e in connects), connects[:3]
        atk_ids = {int(r.principal.principal.split(":")[1]) for r in scanned}
        atk_packets = [e for e in events if e.ev == "packet" and e.cg in atk_ids]
        probed = {e.dport for e in atk_packets if e.dst == web}
        assert len(probed) > 100, "the scan is attributed to the attacker"
        records = list(LinuxEbpf().records(run_dir))
        assert {r.instance for r in records} >= {"lab/workstation[0]", "lab/attacker[0]"}
        for invocation in [*browsed, *scanned]:
            if invocation.outcome != "succeeded":
                continue
            assert any(
                r.principal == invocation.principal
                and invocation.start - 1 <= r.start <= invocation.end + 1
                for r in records
            ), invocation.key.invocation
    finally:
        backend.down(manifest)
        _release(run_dir / "out", state.images["tiergen/base-linux"])
        if (run_dir / "sensors").is_dir():
            _release(run_dir / "sensors", state.images["tiergen/base-linux"], depth=3)
    assert daemon.containers(run) == []
    assert daemon.networks(run) == []


def test_a_failed_up_leaves_nothing_behind(
    run_dir: Path, manifest: RunManifest, daemon: DaemonClient
) -> None:
    broken_hosts = (
        *manifest.hosts[:-1],
        replace(manifest.hosts[-1], image="tiergen/does-not-exist:never"),
    )
    broken = RunManifest(manifest.run, manifest.backend, manifest.networks, broken_hosts)
    with pytest.raises(BackendError, match="not available"):
        DockerBackend().up(broken, run_dir)
    run = {"tiergen.run": manifest.run}
    assert daemon.containers(run) == []
    assert daemon.networks(run) == []


@pytest.fixture
def two_teams(tmp_path: Path, daemon: DaemonClient) -> Iterator[tuple[Path, RunManifest]]:
    """two_teams' Docker half: file servers, attacker and core_router. The VMs are libvirt's."""
    run_dir = tmp_path / "t"
    assert main(["build", str(EXAMPLES / "two_teams" / "scenario.py"), "--out", str(run_dir)]) == 0
    m = from_json(RunManifest, json.loads((run_dir / "manifest.docker.json").read_text()))
    yield run_dir, m
    DockerBackend().down(m)


def test_routed_traffic_crosses_the_core_router(
    two_teams: tuple[Path, RunManifest], daemon: DaemonClient
) -> None:
    run_dir, manifest = two_teams
    state = DockerBackend().up(manifest, run_dir)
    eng_fs = container_name(manifest.run, "corp/eng/file_server[0]")
    sales_fs = container_name(manifest.run, "corp/sales/file_server[0]")
    sales_addr = daemon.addresses(sales_fs)[network_name(manifest.run, "sales")]
    assert sales_addr.startswith("10.32.0.")
    # The route to sales is installed, via the router's address on eng.
    routes = _docker("exec", eng_fs, "ip", "route")
    assert "10.32.0.0/24 via 10.31.0." in routes
    # Nothing listens on sales' file server, so a connection is refused, not timed out: the
    # packet got there and back through core_router. A refusal is immediate; an unreachable
    # address waits for the timeout.
    probe = (
        "import socket,sys,time\nt=time.monotonic();s=socket.socket();s.settimeout(3)\n"
        f"try:\n s.connect(('{sales_addr}',445));r='open'\n"
        "except ConnectionRefusedError: r='refused'\nexcept OSError: r='unreachable'\n"
        "print(r, round(time.monotonic()-t,3))"
    )
    result = subprocess.run(
        ["docker", "exec", eng_fs, "python3", "-c", probe], capture_output=True, text=True
    )
    verdict, elapsed = result.stdout.split()
    assert verdict == "refused", result
    assert float(elapsed) < 1.0, result
    router = container_name(manifest.run, "corp/core_router[0]")
    forward = _docker("exec", router, "cat", "/proc/sys/net/ipv4/ip_forward")
    assert forward.strip() == "1"
    # The bridges carry the names build fixed, and the run state says which.
    links = subprocess.run(["ip", "-o", "link"], capture_output=True, text=True).stdout
    assert all(bridge in links for bridge in state.bridges.values())
    assert set(state.hosts) == {h.instance for h in manifest.hosts}
    DockerBackend().down(manifest)
