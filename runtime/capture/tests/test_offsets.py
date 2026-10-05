import json
from pathlib import Path

from tiergen.interfaces import HostState, RunState
from tiergen.runtime.capture.offsets import ClockOffset, offsets, write_offsets


def test_container_hosts_share_the_kernel_clock_and_vms_are_unmeasured(tmp_path: Path) -> None:
    states = {
        "docker": RunState("r", "docker", hosts={"lab/ws[0]": HostState("c", "1")}),
        "libvirt": RunState("r", "libvirt", hosts={"hq/dc[0]": HostState("d", "2")}),
    }
    found = offsets(states)
    assert found == {
        "lab/ws[0]": ClockOffset(0.0, "shared-kernel"),
        "hq/dc[0]": ClockOffset(None, "unmeasured"),
    }
    write_offsets(tmp_path / "capture", found)
    data = json.loads((tmp_path / "capture" / "offsets.json").read_text())
    assert data["hq/dc[0]"] == {"offset_s": None, "method": "unmeasured"}
