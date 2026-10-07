"""The collector's event line, as data.

Every event carries the cgroup of the task or socket that caused it (``cg``), the cgroup of
the container it ran in (``container_cg``, the ancestor at the containers' depth), the
process, and the local and remote endpoints: ``src`` is the local side for ``connect``,
``udp_send`` and ``packet`` and the remote side's peer for ``accept`` and ``udp_recv``, as
the kernel hook saw them. Timestamps are nanoseconds since the epoch on the capture host's
clock; the collector adds the boot-time offset before printing. ``sk`` identifies the
socket so a ``close`` can end what a ``connect`` or ``accept`` began.
"""

import json
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from tiergen.core.codec import from_json

EventKind = Literal["start", "connect", "accept", "close", "udp_send", "udp_recv", "packet"]


@dataclass(frozen=True, slots=True)
class Event:
    ev: EventKind
    ts_ns: int
    cg: int
    container_cg: int
    pid: int
    tgid: int
    proto: str
    src: str
    sport: int
    dst: str
    dport: int
    sk: int = 0


def read_events(path: Path) -> Iterator[Event]:
    """The events in a file the collector wrote, in order; a bad line is a ``CodecError``."""
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield from_json(Event, json.loads(line))
