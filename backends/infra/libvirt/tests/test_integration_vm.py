"""Against the system libvirt: a Linux guest up on a bridge of its own, driven through the
guest agent, and down without a trace.

Skipped without libvirt, the ``tiergen`` pool or the Linux template
(``scripts/templates/build.py linux``). Builds ``linux_slice`` for its programs and hands
the libvirt backend a manifest of one workstation; the web server it would browse is not
there, so its invocations fail, which is fine: this is the backend's test, not the
scenario's.
"""

import json
import re
import shutil
import time
from pathlib import Path

import pytest

from tiergen.backends.infra.libvirt._client import LibvirtClient
from tiergen.backends.infra.libvirt.backend import POOL, LibvirtBackend, derived_mac, domain_name
from tiergen.cli.main import main
from tiergen.core.codec import from_json
from tiergen.interfaces import BackendError, NetworkSpec, RunManifest

EXAMPLES = Path(__file__).parents[4] / "examples"
pytestmark = pytest.mark.vm


@pytest.fixture(scope="module")
def client() -> LibvirtClient:
    try:
        c = LibvirtClient()
    except BackendError as err:
        pytest.skip(str(err))
    try:
        volumes = c.volumes(POOL)
    except BackendError as err:
        pytest.skip(str(err))
    if "template-linux-agent.qcow2" not in volumes:
        pytest.skip("the Linux agent template is not in the pool")
    if shutil.which("xorriso") is None:
        pytest.skip("xorriso is not installed")
    return c


def test_a_linux_guest_comes_up_on_its_bridge_holds_at_its_gate_and_goes_down(
    client: LibvirtClient, tmp_path: Path
) -> None:
    run_dir = tmp_path / "r"
    assert (
        main(["build", str(EXAMPLES / "linux_slice" / "scenario.py"), "--out", str(run_dir)]) == 0
    )
    docker = from_json(RunManifest, json.loads((run_dir / "manifest.docker.json").read_text()))
    ws = next(h for h in docker.hosts if h.kind == "workstation")
    networks = tuple(
        NetworkSpec(n.name, n.cidr, n.gateway, n.plane, n.internal, f"tg-vmtest-{n.name}")
        for n in docker.networks
        if n.name in {a.network for a in ws.attachments}
    )
    manifest = RunManifest("vmtest", "libvirt", networks, (ws,))
    backend = LibvirtBackend()
    name = domain_name("vmtest", ws.instance)
    try:
        began = time.monotonic()
        state = backend.up(manifest, run_dir, start=False)
        assert name in client.domains()
        assert set(client.networks()) >= {f"tiergen-vmtest-{n.name}" for n in networks}
        host = state.hosts[ws.instance]
        assert host.clock_offset_s is not None
        assert abs(host.clock_offset_s) < 2.0, "the guest's clock, through the agent"
        # The bootstrap gave each interface its planned address, by MAC.
        seen = client.guest_interfaces(name)
        for a in ws.attachments:
            mac = a.mac or derived_mac("vmtest", ws.instance, a.network)
            assert a.address in seen.get(mac.lower(), []), (a, seen)
        # The agent holds at its gate until start.
        bootstrap_log = client.guest_read(name, "/tiergen/bootstrap.log").decode()
        agent_log = client.guest_read(name, "/tiergen/out/agent.log").decode()
        assert "holding at /tiergen/go" in agent_log, (bootstrap_log, agent_log)
        assert "released" not in agent_log
        backend.start(manifest, state)
        deadline = time.monotonic() + 30
        while "released" not in agent_log and time.monotonic() < deadline:
            time.sleep(1)
            agent_log = client.guest_read(name, "/tiergen/out/agent.log").decode()
        assert "released" in agent_log
        assert re.search(r"behaviour 'browse' runs as \d+", agent_log)
        backend.collect(manifest, state, run_dir)
        out = run_dir / "out" / "lab-workstation-0"
        assert (out / "agent.log").is_file()
        assert (out / "bootstrap.log").is_file()
        print(f"guest up, bootstrapped, released and collected in {time.monotonic() - began:.0f} s")
    finally:
        backend.down(manifest)
    assert name not in client.domains()
    assert not [v for v in client.volumes(POOL) if v.startswith("tiergen-vmtest-")]
    assert not [n for n in client.networks() if n.startswith("tiergen-vmtest-")]
