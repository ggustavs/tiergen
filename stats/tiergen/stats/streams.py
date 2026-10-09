"""One stream per host: what a sensor's connections become before any statistic.

A stream is a host's connections in time order, each reduced to a mark: the service it
went to (``tcp/80``) or, once the fit has a vocabulary, the action. Hosts are the units
that permutation and bootstrap resample, because the events of one host are a path of one
process and not independent draws. ``window`` is the interval the host was observed over,
which the rates need and the events alone cannot say.
"""

from collections import Counter
from collections.abc import Callable, Collection, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, tzinfo

import numpy as np
from numpy.typing import NDArray

from tiergen.core.events import ConnEvent

Floats = NDArray[np.float64]
HOUR = 3600.0


@dataclass(frozen=True, slots=True)
class Stream:
    """``times`` sorted, seconds since the epoch; ``marks`` aligned with them."""

    host: str
    times: tuple[float, ...]
    marks: tuple[str, ...]
    window: tuple[float, float]

    def __len__(self) -> int:
        return len(self.times)


def service(conn: ConnEvent) -> str:
    return f"{conn.five_tuple.proto}/{conn.five_tuple.resp_port}"


def streams(
    conns: Iterable[ConnEvent],
    window: tuple[float, float],
    mark: Callable[[ConnEvent], str] = service,
    hosts: Collection[str] | None = None,
) -> list[Stream]:
    """The connections inside ``window`` grouped by originator. ``hosts`` names the
    originators to report, so a host that did nothing is a stream with no events rather
    than no stream; without it, every originator seen is a host."""
    found: dict[str, list[tuple[float, str]]] = {h: [] for h in hosts} if hosts else {}
    for conn in conns:
        if window[0] <= conn.start < window[1]:
            host = conn.five_tuple.orig_addr
            if hosts is None or host in found:
                found.setdefault(host, []).append((conn.start, mark(conn)))
    out: list[Stream] = []
    for host in sorted(found):
        events = sorted(found[host])
        out.append(Stream(host, tuple(t for t, _ in events), tuple(m for _, m in events), window))
    return out


def gaps(stream: Stream) -> Floats:
    """Seconds between consecutive events of one host."""
    return np.diff(np.asarray(stream.times, dtype=np.float64))


def pooled_gaps(found: Sequence[Stream]) -> Floats:
    parts = [gaps(s) for s in found if len(s) > 1]
    return np.concatenate(parts) if parts else np.zeros(0, dtype=np.float64)


def mix(found: Sequence[Stream]) -> dict[str, int]:
    """Events by mark over every host."""
    counts = Counter[str]()
    for s in found:
        counts.update(s.marks)
    return dict(sorted(counts.items()))


def transitions(found: Sequence[Stream]) -> dict[tuple[str, str], int]:
    """Consecutive mark pairs within each host, counted over every host."""
    counts = Counter[tuple[str, str]]()
    for s in found:
        counts.update(zip(s.marks, s.marks[1:], strict=False))
    return dict(sorted(counts.items()))


def hourly(found: Sequence[Stream], tz: tzinfo) -> tuple[Floats, Floats]:
    """Events by local hour of day, and host-hours observed by local hour, over every host:
    the ratio is the rate, and an hour no host was observed in has no rate."""
    counts = np.zeros(24, dtype=np.float64)
    exposure = np.zeros(24, dtype=np.float64)
    for s in found:
        for t in s.times:
            counts[datetime.fromtimestamp(t, tz).hour] += 1
        at, end = s.window
        while at < end:
            local = datetime.fromtimestamp(at, tz)
            into = local.minute * 60 + local.second + local.microsecond / 1e6
            step = min(HOUR - into, end - at)
            exposure[local.hour] += step / HOUR
            at += step
    return counts, exposure


def local_tz(start: str) -> tzinfo:
    """The timezone a scenario's ``start`` is written in: the network's local time."""
    tz = datetime.fromisoformat(start).tzinfo
    if tz is None:
        raise ValueError(f"{start!r} carries no UTC offset; the local hour is undefined")
    return tz
