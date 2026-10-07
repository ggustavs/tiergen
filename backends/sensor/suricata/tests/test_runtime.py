"""The Suricata adapter over canned eve.json from a real run; the image runs in the daemon test."""

from pathlib import Path

import pytest

from tiergen.backends.sensor._base import SensorError
from tiergen.backends.sensor.suricata.runtime import Suricata, conn_state
from tiergen.core.codec import JsonValue
from tiergen.core.events import AppEvent, ConnEvent, SensorFlowId
from tiergen.core.ir import SensorSpec

SAMPLES = Path(__file__).with_name("samples")
SPEC = SensorSpec(
    "suricata", "suricata", "7.0.7", "linux_slice.suricata", "offline", ("APP_EVENTS",), "label"
)


def test_flow_records_are_the_core_and_app_layer_events_hang_under_them() -> None:
    sensor = Suricata(SPEC, "lan-span")
    events = list(sensor.ingest(SAMPLES))
    conns = [e for e in events if isinstance(e, ConnEvent)]
    apps = [e for e in events if isinstance(e, AppEvent)]
    assert len(conns) == 5
    web = next(c for c in conns if c.five_tuple.resp_port == 80 and c.state == "closed")
    assert web.five_tuple.orig_addr == "10.20.0.2"
    assert web.five_tuple.proto == "tcp"
    assert (web.orig_bytes, web.resp_bytes, web.orig_pkts, web.resp_pkts) == (546, 597, 6, 4)
    assert web.duration == pytest.approx(0.000914, abs=1e-6)
    assert web.start == pytest.approx(1791388330.257141, abs=1e-5)
    refused = [c for c in conns if c.five_tuple.orig_addr == "10.20.0.3"]
    assert len(refused) == 3
    assert {c.state for c in refused} == {"rejected"}
    assert all(c.orig_pkts == 1 and c.resp_pkts == 1 for c in refused)
    udp = next(c for c in conns if c.five_tuple.proto == "udp")
    assert udp.state in ("attempted", "closed")
    [http] = apps
    assert http.flow == web.flow
    assert http.flow == SensorFlowId("suricata", "lan-span", str(web.raw["flow_id"]))
    assert (http.protocol, http.index) == ("http", 0)
    assert http.fields["user_agent"] == "python-httpx/0.28.1"
    assert http.fields["uri"] == "/news"
    assert http.fields["host"] == "10.20.0.80"
    assert sensor.flow_key(http) == web.flow
    assert sensor.image == "jasonish/suricata:7.0.7"
    assert sensor.command("c.pcapng", "s.yaml") == [
        "suricata",
        "-r",
        "/pcap/c.pcapng",
        "-c",
        "/config/s.yaml",
        "-l",
        "/out",
    ]


def test_tcp_states_from_the_flags() -> None:
    def tcp(**flags: JsonValue) -> dict[str, JsonValue]:
        return {"proto": "TCP", "tcp": dict(flags)}

    assert conn_state(tcp(syn=True, tcp_flags_tc="00")) == "attempted"
    assert conn_state(tcp(syn=True, rst=True, ack=True, tcp_flags_tc="14")) == "rejected"
    assert conn_state(tcp(syn=True, rst=True, ack=True, tcp_flags_tc="1a")) == "reset"
    assert conn_state(tcp(syn=True, fin=True, ack=True, tcp_flags_tc="1b")) == "closed"
    assert conn_state(tcp(syn=True, ack=True, tcp_flags_tc="12")) == "established"
    assert conn_state({"proto": "UDP", "flow": {"pkts_toclient": 0}}) == "attempted"
    assert conn_state({"proto": "UDP", "flow": {"pkts_toclient": 2}}) == "closed"


def test_no_eve_json_is_an_error_naming_the_sensor(tmp_path: Path) -> None:
    with pytest.raises(SensorError, match=r"eve\.json"):
        list(Suricata(SPEC, "p").ingest(tmp_path))
