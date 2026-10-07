import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from tiergen.backends.attrib._base import Event, EventKind, join, read_events
from tiergen.core.codec import CodecError, to_json
from tiergen.core.events import FiveTuple
from tiergen.core.records import AttributionKey

WS, WEB, ATK = 1001, 1002, 1003  # container cgroup ids
CONTAINERS = {WS: "lab/ws[0]", WEB: "lab/web[0]", ATK: "lab/atk[0]"}


BASE = Event("connect", 0, 0, 0, 7, 7, "tcp", "10.0.0.2", 40000, "10.0.0.80", 80, 0)


def ev(kind: EventKind, ts: int, cg: int, container: int, **fields: Any) -> Event:
    return replace(BASE, ev=kind, ts_ns=ts, cg=cg, container_cg=container, **fields)


def test_a_connect_is_ended_by_its_close_and_the_responder_is_a_record_of_its_own() -> None:
    events = [
        ev("start", 10**18, 0, 0, proto="other", src="", dst="", sport=0, dport=0),
        ev("connect", 10**18, 5001, WS, sk=0xAA),
        ev(
            "accept",
            10**18 + 1000,
            6001,
            WEB,
            src="10.0.0.80",
            sport=80,
            dst="10.0.0.2",
            dport=40000,
            sk=0xBB,
            tgid=9,
        ),
        ev("close", 10**18 + 2 * 10**9, 5001, WS, sk=0xAA),
        ev("connect", 10**18 + 3 * 10**9, 5002, WS, sk=0xCC, dport=443),
    ]
    joined = join(events, CONTAINERS)
    assert joined.dropped == {}
    first, second, third = joined.records
    assert first.instance == "lab/ws[0]"
    assert first.principal == AttributionKey("linux", "cgroup:5001")
    assert first.five_tuple == FiveTuple("10.0.0.2", 40000, "10.0.0.80", 80, "tcp")
    assert (first.start, first.end, first.tgid) == (10**9, 10**9 + 2.0, 7)
    assert second.instance == "lab/web[0]"
    assert second.five_tuple == first.five_tuple  # the same connection, seen from the responder
    assert second.principal == AttributionKey("linux", "cgroup:6001")
    assert second.tgid == 9
    assert third.end == third.start  # never seen closing


def test_udp_and_raw_packets_are_records_on_their_own_and_strangers_are_dropped() -> None:
    events = [
        ev("udp_send", 10**18, 5001, WS, proto="udp", dport=53),
        ev(
            "udp_recv",
            10**18 + 5,
            5001,
            WS,
            proto="udp",
            src="10.0.0.53",
            sport=53,
            dst="10.0.0.2",
            dport=50000,
        ),
        *(
            ev("packet", 10**18 + i, 7001, ATK, src="10.0.0.9", sport=61000, dport=20 + i, tgid=0)
            for i in range(3)
        ),
        ev("packet", 10**18, 9999, 4242, src="10.0.0.1", dport=22),
        ev("connect", 10**18, 9998, 4243, sk=0x11),
    ]
    joined = join(events, CONTAINERS)
    assert joined.dropped == {"packet": 1, "connect": 1}
    send, recv, *packets = joined.records
    assert send.five_tuple == FiveTuple("10.0.0.2", 40000, "10.0.0.80", 53, "udp")
    assert recv.five_tuple == FiveTuple("10.0.0.2", 50000, "10.0.0.53", 53, "udp")
    assert [p.five_tuple.resp_port for p in packets] == [20, 21, 22]
    assert all(p.instance == "lab/atk[0]" and p.tgid == 0 and p.end == p.start for p in packets)


def test_event_lines_read_back_and_a_bad_line_is_an_error(tmp_path: Path) -> None:
    events = [ev("connect", 10**18, 5001, WS, sk=1), ev("close", 10**18 + 1, 5001, WS, sk=1)]
    path = tmp_path / "events.jsonl"
    path.write_text("".join(json.dumps(to_json(e)) + "\n" for e in events) + "\n")
    assert list(read_events(path)) == events
    path.write_text('{"ev": "connect"}\n')
    with pytest.raises(CodecError):
        list(read_events(path))
