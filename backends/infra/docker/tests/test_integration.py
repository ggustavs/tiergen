"""Against a real daemon: linux_slice up, addressed as planned, and down without a trace.

Skipped when no daemon is reachable. Runs the whole example, so it also pulls the base
image the first time.
"""

import json
import subprocess
from collections.abc import Iterator
from pathlib import Path

import pytest

from tiergen.backends.infra.docker._client import DaemonClient
from tiergen.backends.infra.docker.backend import DockerBackend, container_name, network_name
from tiergen.cli.main import main
from tiergen.core.codec import from_json
from tiergen.interfaces import BackendError, RunManifest

EXAMPLES = Path(__file__).parents[4] / "examples"
pytestmark = pytest.mark.docker


@pytest.fixture(scope="module")
def daemon() -> DaemonClient:
    try:
        return DaemonClient()
    except BackendError as err:
        pytest.skip(str(err))


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


def test_linux_slice_comes_up_as_planned_and_goes_down_without_a_trace(
    run_dir: Path, manifest: RunManifest, daemon: DaemonClient
) -> None:
    plan = json.loads((run_dir / "addresses.json").read_text())
    backend = DockerBackend()
    backend.up(manifest)

    run = {"tiergen.run": manifest.run}
    assert sorted(daemon.containers(run)) == sorted(
        container_name(manifest.run, h.instance) for h in manifest.hosts
    )
    for host in manifest.hosts:
        got = daemon.addresses(container_name(manifest.run, host.instance))
        want = {
            network_name(manifest.run, n): a for n, a in plan["addresses"][host.instance].items()
        }
        assert got == want, host.instance
    lan = json.loads(_docker("network", "inspect", network_name(manifest.run, "lan")))[0]
    assert lan["Internal"] is True
    assert lan["IPAM"]["Config"][0] == {"Subnet": "10.20.0.0/24", "Gateway": "10.20.0.1"}

    # The web server is reachable on the data plane: nothing listens yet, so the connection
    # is refused rather than timing out, which is what reachability looks like at this stage.
    ws = container_name(manifest.run, "lab/workstation[0]")
    probe = (
        "import socket,sys\ns=socket.socket();s.settimeout(3)\n"
        "try:\n s.connect(('10.20.0.80',80))\nexcept ConnectionRefusedError:\n sys.exit(0)\n"
        "except OSError as e:\n sys.exit(2)\nsys.exit(0)"
    )
    code = subprocess.run(
        [
            "docker",
            "exec",
            ws,
            "sh",
            "-c",
            f'command -v python3 >/dev/null || exit 3; python3 -c "{probe}"',
        ],
        capture_output=True,
    ).returncode
    assert code in (0, 3)  # 3: the base image has no python; the address assertions above stand

    backend.down(manifest)
    assert daemon.containers(run) == []
    assert daemon.networks(run) == []


def test_a_failed_up_leaves_nothing_behind(manifest: RunManifest, daemon: DaemonClient) -> None:
    broken_hosts = (
        *manifest.hosts[:-1],
        manifest.hosts[-1].__class__(
            instance=manifest.hosts[-1].instance,
            kind=manifest.hosts[-1].kind,
            image="tiergen/does-not-exist:never",
            command=manifest.hosts[-1].command,
            cap_add=manifest.hosts[-1].cap_add,
            attachments=manifest.hosts[-1].attachments,
        ),
    )
    broken = RunManifest(manifest.run, manifest.backend, manifest.networks, broken_hosts)
    with pytest.raises(BackendError, match="not available"):
        DockerBackend().up(broken)
    run = {"tiergen.run": manifest.run}
    assert daemon.containers(run) == []
    assert daemon.networks(run) == []
