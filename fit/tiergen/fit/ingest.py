"""A sensor's events, labelled by the vocabulary into per-instance action streams.

Reads ``sensors/<name>/<point>/events.jsonl`` for every point, keeps one copy of a
connection two points both saw (same five-tuple within a millisecond), attaches each
connection's application events by flow id, and asks the vocabulary what the connection
is. The result is one stream per instance per behaviour, in time order, plus a count of
what was not mapped and why.
"""

import json
from collections import Counter
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from tiergen.core.codec import decode
from tiergen.core.events import AppEvent, ConnEvent, Event, SensorFlowId
from tiergen.fit.vocabulary import Candidate, Vocabulary
from tiergen.stats import Stream

EVENTS = "events.jsonl"
MANY_GAP_S = 1.0
"""Connections of a many-connection action closer than this are one invocation."""


@dataclass(frozen=True, slots=True)
class Unmapped:
    """Connections the vocabulary could not place, by reason, and the originators of the
    ``unknown originator`` ones with their counts."""

    by_reason: dict[str, int] = field(default_factory=dict[str, int])
    originators: dict[str, int] = field(default_factory=dict[str, int])


@dataclass(frozen=True, slots=True)
class Labelled:
    """``streams`` by ``(kind, behaviour)``, one ``Stream`` per instance, marks being
    state names; ``window`` is the span the events cover; ``app_coverage`` is the share of
    HTTP connections that carried an application event."""

    streams: dict[tuple[str, str], list[Stream]]
    window: tuple[float, float]
    connections: int
    unmapped: Unmapped
    app_coverage: float | None


def read_events(run_dir: Path, sensor: str) -> Iterator[Event]:
    root = run_dir / "sensors" / sensor
    paths = sorted(root.glob(f"*/{EVENTS}"))
    if not paths:
        raise FileNotFoundError(f"{root}: no {EVENTS} under any capture point")
    for path in paths:
        with path.open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield decode(ConnEvent | AppEvent, json.loads(line))


def _dedupe(conns: Iterable[ConnEvent]) -> list[ConnEvent]:
    seen: set[tuple[str, int, str, int, str, int]] = set()
    kept: list[ConnEvent] = []
    for c in sorted(conns, key=lambda c: c.start):
        f = c.five_tuple
        key = (f.orig_addr, f.orig_port, f.resp_addr, f.resp_port, f.proto, round(c.start * 1000))
        if key not in seen:
            seen.add(key)
            kept.append(c)
    return kept


def label(
    events: Iterable[Event], vocab: Vocabulary, window: tuple[float, float] | None = None
) -> Labelled:
    conns: list[ConnEvent] = []
    apps: dict[SensorFlowId, list[AppEvent]] = {}
    for e in events:
        if isinstance(e, ConnEvent):
            conns.append(e)
        else:
            apps.setdefault(e.flow, []).append(e)
    conns = _dedupe(conns)
    if window is None:
        window = (conns[0].start, conns[-1].start + 1e-3) if conns else (0.0, 0.0)
    by_instance: dict[tuple[str, str, str], list[tuple[float, str, bool]]] = {}
    reasons = Counter[str]()
    originators = Counter[str]()
    http = with_app = 0
    for c in conns:
        if not window[0] <= c.start < window[1]:
            continue
        mine = apps.get(c.flow, [])
        if c.five_tuple.resp_port in (80, 8080, 8000, 443) or any(
            a.protocol == "http" for a in mine
        ):
            http += 1
            with_app += bool(mine)
        found = vocab.match(c, mine)
        if isinstance(found, str):
            reasons[found] += 1
            if found == "unknown originator":
                originators[c.five_tuple.orig_addr] += 1
            continue
        by_instance.setdefault((found.kind, found.behaviour, found.instance), []).append(
            (c.start, found.state, found.many)
        )
    streams: dict[tuple[str, str], list[Stream]] = {}
    for candidates in vocab.by_address.values():
        for cand in candidates:
            streams.setdefault((cand.kind, cand.behaviour), [])
    for (kind, behaviour, instance), events_ in sorted(by_instance.items()):
        events_.sort()
        kept: list[tuple[float, str]] = []
        for t, state, many in events_:
            if many and kept and kept[-1][1] == state and t - kept[-1][0] < MANY_GAP_S:
                continue
            kept.append((t, state))
        streams.setdefault((kind, behaviour), []).append(
            Stream(instance, tuple(t for t, _ in kept), tuple(s for _, s in kept), window)
        )
    # Every instance with a candidate for the behaviour is a stream, active or not.
    seen = {(k, b, s.host) for (k, b), ss in streams.items() for s in ss}
    for candidates in vocab.by_address.values():
        for cand in candidates:
            key = (cand.kind, cand.behaviour)
            if (cand.kind, cand.behaviour, cand.instance) not in seen:
                seen.add((cand.kind, cand.behaviour, cand.instance))
                streams[key].append(Stream(cand.instance, (), (), window))
    for ss in streams.values():
        ss.sort(key=lambda s: s.host)
    return Labelled(
        streams,
        window,
        len(conns),
        Unmapped(dict(sorted(reasons.items())), dict(originators.most_common())),
        (with_app / http) if http else None,
    )


def candidates_of(vocab: Vocabulary, kind: str, behaviour: str) -> list[Candidate]:
    found: dict[str, Candidate] = {}
    for candidates in vocab.by_address.values():
        for c in candidates:
            if (c.kind, c.behaviour) == (kind, behaviour):
                found.setdefault(c.state, c)
    return list(found.values())
