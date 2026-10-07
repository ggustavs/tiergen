"""Suricata over a capture: ``suricata -r`` in the pinned image, then ``eve.json`` as events.

``event_type: flow`` records are the required core, one ``ConnEvent`` each with ``flow_id``
as the flow id; the application-layer events (``http``, ``tls``, ``dns``, ``ssh``, ``smb``)
are ``AppEvent``s under the same ``flow_id``, mapped to the capability schemas' field names.
A record's ``timestamp`` is when Suricata wrote it, so the connection's own ``flow.start``
and ``flow.end`` give the interval.
"""

import json
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import cast

from tiergen.backends.sensor._base import SensorError
from tiergen.backends.sensor._base.runtime import ContainerSensor
from tiergen.core.codec import JsonValue
from tiergen.core.events import AppEvent, ConnEvent, ConnState, Event, FiveTuple

APP_EVENTS: dict[str, tuple[str, dict[str, tuple[str, ...]]]] = {
    "http": (
        "http",
        {
            "user_agent": ("http_user_agent",),
            "method": ("http_method",),
            "host": ("hostname",),
            "uri": ("url",),
            "status_code": ("status",),
        },
    ),
    "tls": (
        "tls",
        {
            "server_name": ("sni",),
            "version": ("version",),
            "ja3": ("ja3", "hash"),
            "ja4": ("ja4",),
            "subject": ("subject",),
            "issuer": ("issuerdn",),
            "fingerprint": ("fingerprint",),
        },
    ),
    "dns": ("dns", {"query": ("rrname",), "qtype": ("rrtype",), "rcode": ("rcode",)}),
    "ssh": (
        "ssh",
        {"client": ("client", "software_version"), "server": ("server", "software_version")},
    ),
    "smb": ("smb", {"dialect": ("dialect",), "command": ("command",)}),
}
"""Event type to the protocol vocabulary and the schema field to the path under the event's
own object (``http``, ``tls``, …) in ``eve.json``."""


def _epoch(stamp: str) -> float:
    """Suricata's ``2026-10-07T15:52:10.257141+0000`` as seconds since the epoch."""
    return datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()


def conn_state(record: dict[str, JsonValue]) -> ConnState:
    """From the flow's state and, for TCP, the flags each side sent.

    A TCP flow that saw only the client's SYN never got anywhere; one the server answered
    with RST and no SYN-ACK was refused; FIN from either side closed it; RST after it was
    up reset it; anything else still open is established. Other transports have no
    handshake: both directions seen is as closed as they get, one direction is attempted.
    """
    flow = cast(dict[str, JsonValue], record.get("flow") or {})
    tcp = cast(dict[str, JsonValue], record.get("tcp") or {})
    if record.get("proto") == "TCP":
        to_client = int(str(tcp.get("tcp_flags_tc") or "0"), 16)
        if tcp.get("fin"):
            return "closed"
        if tcp.get("rst"):
            return "rejected" if to_client & 0x12 != 0x12 else "reset"
        if tcp.get("syn") and to_client == 0:
            return "attempted"
        return "established" if tcp.get("ack") else "other"
    return "closed" if int(str(flow.get("pkts_toclient") or 0)) > 0 else "attempted"


def _dig(obj: JsonValue, path: tuple[str, ...]) -> JsonValue:
    for key in path:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    return obj


class Suricata(ContainerSensor):
    repository = "jasonish/suricata"

    def command(self, pcap: str, config: str) -> list[str]:
        return ["suricata", "-r", f"/pcap/{pcap}", "-c", f"/config/{config}", "-l", "/out"]

    def ingest(self, native_logs: Path) -> Iterator[Event]:
        eve = native_logs / "eve.json"
        if not eve.is_file():
            raise SensorError(f"{eve} is missing: suricata wrote no eve.json; see its log there")
        indexes: dict[str, int] = {}
        with eve.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r: dict[str, JsonValue] = json.loads(line)
                kind = str(r.get("event_type"))
                if "flow_id" not in r:
                    continue
                native = str(r["flow_id"])
                if kind == "flow":
                    flow = cast(dict[str, JsonValue], r["flow"])
                    start = _epoch(str(flow["start"]))
                    end = _epoch(str(flow["end"])) if flow.get("end") else None
                    yield ConnEvent(
                        self.flow(native),
                        FiveTuple(
                            str(r["src_ip"]),
                            int(str(r.get("src_port", 0))),
                            str(r["dest_ip"]),
                            int(str(r.get("dest_port", 0))),
                            str(r["proto"]).lower(),
                        ),
                        start,
                        None if end is None else end - start,
                        int(str(flow["bytes_toserver"])),
                        int(str(flow["bytes_toclient"])),
                        int(str(flow["pkts_toserver"])),
                        int(str(flow["pkts_toclient"])),
                        conn_state(r),
                        r,
                    )
                elif kind in APP_EVENTS:
                    protocol, paths = APP_EVENTS[kind]
                    body = r.get(kind)
                    index = indexes.get(native, 0)
                    indexes[native] = index + 1
                    found = {name: _dig(body, path) for name, path in paths.items()}
                    fields: dict[str, JsonValue] = {
                        name: value for name, value in found.items() if value is not None
                    }
                    yield AppEvent(
                        self.flow(native), index, _epoch(str(r["timestamp"])), protocol, fields, r
                    )
