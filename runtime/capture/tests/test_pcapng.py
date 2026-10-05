import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tiergen.runtime.capture.pcapng import (
    Interface,
    Packet,
    PcapngError,
    insert_tags,
    read,
    tag,
    write,
)

names = st.text(st.characters(codec="ascii", categories=["Ll", "Nd"]), min_size=1, max_size=8)
interfaces = st.lists(
    st.builds(Interface, names, st.just(1), st.sampled_from([6, 9])), min_size=1, max_size=3
)
frames = st.binary(min_size=14, max_size=200)


@st.composite
def captures(draw: st.DrawFn) -> tuple[list[Interface], list[Packet]]:
    found = draw(interfaces)
    seen = draw(
        st.lists(
            st.builds(
                Packet,
                st.integers(0, len(found) - 1),
                st.integers(0, 2**62).map(lambda n: n - n % 1000),
                frames,
                st.none(),
            ),
            max_size=20,
        )
    )
    return found, seen


@settings(max_examples=60)
@given(capture=captures())
def test_what_is_written_is_read_back(capture: tuple[list[Interface], list[Packet]]) -> None:
    found, seen = capture
    with tempfile.TemporaryDirectory() as d:  # not tmp_path: hypothesis forbids function fixtures
        path = Path(d) / "c.pcapng"
        write(path, found, seen)
        assert read(path) == (found, seen)


def test_tags_go_after_the_mac_addresses_and_lengths_follow(tmp_path: Path) -> None:
    frame = bytes(range(14)) + b"payload"
    assert tag(frame, 0x0ABC)[12:16] == b"\x81\x00\x0a\xbc"
    assert tag(frame, 10)[:12] == frame[:12]
    assert tag(frame, 10)[16:] == frame[12:]
    src, dst = tmp_path / "s.pcapng", tmp_path / "t.pcapng"
    found = [Interface("eng"), Interface("sales"), Interface("mgmt")]
    seen = [
        Packet(0, 1_000_000_000, frame),
        Packet(1, 2_000_000_000, frame, original_len=1500),
        Packet(2, 3_000_000_000, frame),
    ]
    write(src, found, seen)
    assert insert_tags(src, dst, {0: 10, 1: 20}) == 2
    got_interfaces, got = read(dst)
    assert got_interfaces == found
    assert got[0].data == tag(frame, 10)
    assert got[0].wire_len == len(frame) + 4
    assert (got[1].data, got[1].original_len) == (tag(frame, 20), 1504)
    assert got[2] == seen[2]


def test_a_file_that_is_not_pcapng_is_an_error(tmp_path: Path) -> None:
    (tmp_path / "x.pcapng").write_bytes(b"\x0a\x0d\x0d\x0a\x1c\x00\x00\x00garbage!")
    with pytest.raises(PcapngError):
        read(tmp_path / "x.pcapng")


def test_a_capture_by_dumpcap_reads_back(tmp_path: Path) -> None:
    if shutil.which("dumpcap") is None:
        pytest.skip("dumpcap is not installed")
    path = tmp_path / "lo.pcapng"
    proc = subprocess.Popen(
        ["dumpcap", "-q", "-i", "lo", "-a", "duration:3", "-w", str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    time.sleep(1)
    payload = b"tiergen-capture-probe"
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.sendto(payload, ("127.0.0.1", 9))
    _, err = proc.communicate(timeout=15)
    if proc.returncode != 0:
        pytest.skip(f"dumpcap cannot capture here: {err.decode(errors='replace').strip()}")
    found, seen = read(path)
    assert [i.name for i in found] == ["lo"]
    assert any(payload in p.data for p in seen)
    assert all(p.timestamp_ns > 1_600_000_000 * 10**9 for p in seen)
