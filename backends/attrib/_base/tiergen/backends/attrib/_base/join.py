"""From the collector's events to ``AttributionRecord``s.

A ``connect`` or ``accept`` opens a record on its socket; the ``close`` with the same socket
ends it; what never closed ends where it began, which the record's reader can tell from
``end == start``. UDP exchanges and raw packets are records on their own. The instance is
the container's, from the cgroup the collector was told about; an event from any other
cgroup is dropped and counted, never guessed at.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace

from tiergen.backends.attrib._base.events import Event
from tiergen.core.events import FiveTuple
from tiergen.core.records import AttributionKey
from tiergen.interfaces import AttributionRecord

NS = 1_000_000_000


@dataclass(frozen=True, slots=True)
class Joined:
    """The records, and how many events of each kind named no container of the run."""

    records: list[AttributionRecord]
    dropped: dict[str, int] = field(default_factory=dict[str, int])


def _five(e: Event) -> FiveTuple:
    """The local side originates a connect, a UDP send and an egress packet; the remote
    side originates what was accepted or received."""
    if e.ev in ("accept", "udp_recv"):
        return FiveTuple(e.dst, e.dport, e.src, e.sport, e.proto)
    return FiveTuple(e.src, e.sport, e.dst, e.dport, e.proto)


def join(events: Iterable[Event], containers: Mapping[int, str]) -> Joined:
    """``containers`` maps a container's cgroup id to its instance id."""
    records: list[AttributionRecord] = []
    pending: dict[int, int] = {}  # socket -> index into records of the open connection
    dropped: dict[str, int] = {}
    for e in events:
        if e.ev == "start":
            continue
        if e.ev == "close":
            opened = pending.pop(e.sk, None)
            if opened is not None:
                records[opened] = replace(records[opened], end=e.ts_ns / NS)
            continue
        instance = containers.get(e.container_cg)
        if instance is None:
            dropped[e.ev] = dropped.get(e.ev, 0) + 1
            continue
        record = AttributionRecord(
            instance,
            AttributionKey("linux", f"cgroup:{e.cg}"),
            _five(e),
            e.ts_ns / NS,
            e.ts_ns / NS,
            e.tgid,
        )
        if e.ev in ("connect", "accept") and e.sk:
            pending[e.sk] = len(records)
        records.append(record)
    return Joined(records, dropped)
