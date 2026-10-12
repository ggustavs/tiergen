"""Against the system libvirt: a clone of the Windows template up on a bridge of its own,
reached through the guest agent, and down without a trace.

Skipped without libvirt, the ``tiergen`` pool, the Windows template
(``scripts/templates/build.py windows``) or xorriso. The host is not an agent host, since
the Windows agent does not exist yet: this is the template's test, through the backend's
own domain definition, virtio disk and NIC, and clock measurement.
"""

import shutil
import time
from pathlib import Path

import pytest

from tiergen.backends.infra.libvirt._client import LibvirtClient
from tiergen.backends.infra.libvirt.backend import POOL, LibvirtBackend, domain_name
from tiergen.interfaces import Attachment, BackendError, HostSpec, NetworkSpec, RunManifest

pytestmark = pytest.mark.vm

TEMPLATE = "template-windows-agent.qcow2"
POWERSHELL = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
MAC = "52:54:00:0a:00:15"


@pytest.fixture(scope="module")
def client() -> LibvirtClient:
    try:
        c = LibvirtClient()
        volumes = c.volumes(POOL)
    except BackendError as err:
        pytest.skip(str(err))
    if TEMPLATE not in volumes:
        pytest.skip("the Windows template is not in the pool")
    if shutil.which("xorriso") is None:
        pytest.skip("xorriso is not installed")
    return c


def test_a_windows_clone_boots_on_virtio_and_answers_through_its_agent(
    client: LibvirtClient, tmp_path: Path
) -> None:
    lan = NetworkSpec("lan", "10.0.0.0/24", "10.0.0.1", "data", True, "tg-wintest-lan")
    ws = HostSpec(
        "hq/ws[0]",
        "workstation",
        "windows",
        "hq-ws-0",
        "windows-agent",
        (),
        (),
        (Attachment("lan", "10.0.0.21", MAC),),
    )
    manifest = RunManifest("wintest", "libvirt", (lan,), (ws,))
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    backend = LibvirtBackend(agent_timeout_s=600)
    name = domain_name("wintest", ws.instance)
    try:
        began = time.monotonic()
        state = backend.up(manifest, run_dir, start=False)
        host = state.hosts[ws.instance]
        assert host.clock_offset_s is not None
        assert abs(host.clock_offset_s) < 2.0, "the guest's clock, through the agent"
        assert MAC in client.guest_interfaces(name), "the virtio NIC with its planned MAC"
        done = client.guest_exec(
            name,
            POWERSHELL,
            [
                "-NoProfile",
                "-Command",
                'C:\\Python312\\python.exe -c "import sys, httpx; print(sys.version.split()[0])";'
                " (Get-Service Sysmon64).Status",
            ],
        )
        transcript = client.guest_read(name, "C:\\tiergen-build\\provision.log").decode(
            "utf-8", "replace"
        )
        assert "QEMU-GA Running" in transcript, transcript[-2000:]
        assert done.exit_code == 0, (done.err, transcript[-2000:])
        assert done.out.split() == ["3.12.10", "Running"]
        print(
            f"windows clone up and answering in {time.monotonic() - began:.0f} s, "
            f"offset {host.clock_offset_s:+.3f} s"
        )
    finally:
        backend.down(manifest)
    assert name not in client.domains()
    assert not [v for v in client.volumes(POOL) if v.startswith("tiergen-wintest-")]
    assert not [n for n in client.networks() if n.startswith("tiergen-wintest-")]
