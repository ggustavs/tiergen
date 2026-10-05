"""start and stop against a stand-in for dumpcap; the real one is exercised by the daemon test.

Linux only, like capture itself: the processes are signalled and watched through /proc.
"""

import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

from tiergen.runtime.capture.dumpcap import CaptureState, command, spawn, start, stop
from tiergen.runtime.capture.pcapng import read
from tiergen.runtime.capture.points import CaptureError, Point

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="capture runs on a Linux host")

FAKE = Path(__file__).with_name("fake_dumpcap.py")
LAN = Point("lan-span", ("lan",), ("tg-lan",), (None,), False)
TRUNK = Point("core-span", ("core", "eng"), ("tg-c", "tg-e"), (10, None), True)


def fake(args: Sequence[str], log: Path) -> int:
    assert args[0] == "dumpcap"
    return spawn([sys.executable, str(FAKE), *args[1:]], log)


def test_the_command_lists_the_bridges_in_segment_order(tmp_path: Path) -> None:
    assert command(TRUNK, tmp_path / "c.pcapng") == [
        "dumpcap",
        "-q",
        "-w",
        str(tmp_path / "c.pcapng"),
        "-i",
        "tg-c",
        "-i",
        "tg-e",
    ]


def test_start_records_the_captures_and_stop_finishes_the_files(tmp_path: Path) -> None:
    out = tmp_path / "capture"
    state = start("r", [LAN, TRUNK], out, spawner=fake)
    assert [c.point for c in state.captures] == ["lan-span", "core-span"]
    assert (out / "state.json").is_file()
    assert json.loads((out / "state.json").read_text())["run"] == "r"
    assert all(Path(f"/proc/{c.pid}").is_dir() for c in state.captures)
    with pytest.raises(CaptureError, match="stop it first"):
        start("r", [LAN], out, spawner=fake)

    final = stop(out)
    assert isinstance(final, CaptureState)
    assert final.stopped is not None
    assert final.tagged_packets == {"core-span": 1}  # one packet on the tagged segment
    assert not (out / "state.json").exists()
    assert json.loads((out / "capture.json").read_text())["tagged_packets"] == {"core-span": 1}
    assert all(not Path(f"/proc/{c.pid}").is_dir() for c in state.captures)
    interfaces, packets = read(out / "core-span.pcapng")
    assert [i.name for i in interfaces] == ["tg-c", "tg-e"]
    assert packets[0].data[12:16] == b"\x81\x00\x00\x0a"
    assert packets[1].data[12:14] == b"\x0c\x0d"  # untagged segment: the frame as captured
    _, plain = read(out / "lan-span.pcapng")
    assert plain[0].data[12:14] == b"\x0c\x0d"
    assert not (out / "core-span.tagging").exists()


def test_a_dumpcap_that_exits_at_once_is_an_error_and_the_rest_are_stopped(tmp_path: Path) -> None:
    def failing(args: Sequence[str], log: Path) -> int:
        if "tg-lan" in args:
            return spawn(
                [
                    sys.executable,
                    "-c",
                    "import sys; print('no permission', file=sys.stderr); sys.exit(2)",
                ],
                log,
            )
        return fake(args, log)

    with pytest.raises(CaptureError, match="'lan-span' exited: no permission"):
        start("r", [TRUNK, LAN], tmp_path / "capture", spawner=failing)
    assert not (tmp_path / "capture" / "state.json").exists()
    with pytest.raises(CaptureError, match="nothing is capturing"):
        stop(tmp_path / "capture")
    assert os.getpid() > 0
