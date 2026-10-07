"""Zeek over a capture: ``zeek -r`` in the pinned image, then its logs as events.

``conn.log`` is the required core, one ``ConnEvent`` per record with ``uid`` as the flow
id. The per-protocol logs are ``AppEvent``s under the same ``uid``: ``http.log``,
``ssl.log`` (with ``x509.log`` joined by certificate id where present), ``dns.log``,
``ssh.log`` and ``smb_mapping.log``, each mapped to the capability schemas' field names.
Both of Zeek's log formats are read. A configuration that does not load a protocol's
scripts simply has no such log, and then no such events.
"""

from collections.abc import Iterator
from pathlib import Path

from tiergen.backends.sensor._base import SensorError, read_zeek_log
from tiergen.backends.sensor._base.runtime import ContainerSensor
from tiergen.core.codec import JsonValue
from tiergen.core.events import AppEvent, ConnEvent, ConnState, Event, FiveTuple

STATES: dict[str, ConnState] = {
    "S0": "attempted",
    "S1": "established",
    "S2": "established",
    "S3": "established",
    "SF": "closed",
    "REJ": "rejected",
    "RSTO": "reset",
    "RSTR": "reset",
    "RSTOS0": "reset",
    "RSTRH": "reset",
    "SH": "other",
    "SHR": "other",
    "OTH": "other",
}
"""Zeek's ``conn_state`` to the common vocabulary."""

APP_LOGS: dict[str, tuple[str, dict[str, str]]] = {
    "http": (
        "http",
        {
            "user_agent": "user_agent",
            "method": "method",
            "host": "host",
            "uri": "uri",
            "status_code": "status_code",
        },
    ),
    "ssl": (
        "tls",
        {
            "server_name": "server_name",
            "version": "version",
            "ja3": "ja3",
            "ja4": "ja4",
            "subject": "subject",
            "issuer": "issuer",
        },
    ),
    "dns": ("dns", {"query": "query", "qtype": "qtype_name", "rcode": "rcode_name"}),
    "ssh": ("ssh", {"client": "client", "server": "server"}),
    "smb_mapping": ("smb", {"path": "path", "share_type": "share_type"}),
}
"""Log name to the protocol vocabulary and the schema field to Zeek column mapping."""


def _int(value: JsonValue) -> int | None:
    return int(value) if isinstance(value, int | float) and not isinstance(value, bool) else None


def _float(value: JsonValue) -> float | None:
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else None


class Zeek(ContainerSensor):
    repository = "zeek/zeek"

    def command(self, pcap: str, config: str) -> list[str]:
        return ["sh", "-c", f"cd /out && exec zeek -C -r /pcap/{pcap} /config/{config}"]

    def ingest(self, native_logs: Path) -> Iterator[Event]:
        conn = native_logs / "conn.log"
        if not conn.is_file():
            raise SensorError(f"{conn} is missing: zeek wrote no conn.log; see reporter.log there")
        for r in read_zeek_log(conn):
            state = r.get("conn_state")
            yield ConnEvent(
                self.flow(str(r["uid"])),
                FiveTuple(
                    str(r["id.orig_h"]),
                    int(str(r["id.orig_p"])),
                    str(r["id.resp_h"]),
                    int(str(r["id.resp_p"])),
                    str(r["proto"]),
                ),
                float(str(r["ts"])),
                _float(r.get("duration")),
                _int(r.get("orig_bytes")),
                _int(r.get("resp_bytes")),
                _int(r.get("orig_pkts")),
                _int(r.get("resp_pkts")),
                STATES.get(str(state), "other"),
                r,
            )
        indexes: dict[str, int] = {}
        for log, (protocol, columns) in APP_LOGS.items():
            path = native_logs / f"{log}.log"
            if not path.is_file():
                continue
            for r in read_zeek_log(path):
                uid = str(r["uid"])
                index = indexes.get(uid, 0)
                indexes[uid] = index + 1
                fields = {
                    name: r[column] for name, column in columns.items() if r.get(column) is not None
                }
                yield AppEvent(self.flow(uid), index, float(str(r["ts"])), protocol, fields, r)
