"""Against a real daemon: linux_slice up, browsing and scanning, and down without a trace.

Skipped when no daemon is reachable. Runs the whole example, so it also builds the agent
image the first time, which takes a few minutes.
"""

import json
import os
import subprocess
import time
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path

import pytest

from tiergen.backends.infra.docker._client import DaemonClient
from tiergen.backends.infra.docker.backend import DockerBackend, container_name, network_name
from tiergen.cli.main import main
from tiergen.core.codec import from_json
from tiergen.core.records import InvocationRecord
from tiergen.interfaces import BackendError, RunManifest
from tiergen.runtime.agent_linux.records import read_records

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


def _release(out: Path, image: str) -> None:
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
            "2",
            "-delete",
        ],
        check=True,
        capture_output=True,
    )


def test_linux_slice_runs_its_behaviours_and_goes_down_without_a_trace(
    run_dir: Path, manifest: RunManifest, daemon: DaemonClient
) -> None:
    plan = json.loads((run_dir / "addresses.json").read_text())
    backend = DockerBackend()
    state = backend.up(manifest, run_dir)
    try:
        assert state.images["tiergen/base-linux"].startswith("sha256:")
        run = {"tiergen.run": manifest.run}
        assert sorted(daemon.containers(run)) == sorted(
            container_name(manifest.run, h.instance) for h in manifest.hosts
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
            lambda rs: any(r.outcome == "succeeded" for r in rs),
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
        assert first.principal.principal.startswith("cgroup:/tiergen/lab-workstation[0]-browse#"), (
            ws_log
        )
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
        # The agents' files belong to the remapped root and are readable by the user through
        # the ACL up set; the directories are the user's own.
        assert (out / "lab-web_server-0" / "http.nginx" / "access.log").stat().st_uid != os.getuid()
        assert (out / "lab-web_server-0").stat().st_uid == os.getuid()
    finally:
        backend.down(manifest)
        _release(run_dir / "out", state.images["tiergen/base-linux"])
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
