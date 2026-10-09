"""One behaviour's observable chain, dwells and rate curve from its instances' streams.

The acting states are the behaviour's, in the program's order. Transitions are counted
over consecutive actions within each instance and pooled over the kind's instances; the
initial distribution is the first action of each instance. The rate curve is events per
host-hour by local hour, normalised to its peak, over the hours the run covered; the
others are unfitted and filled with the covered hours' mean, which the report says. A
state's dwell is the gap from one of its actions to the instance's next, moved onto the
operational clock by the fitted curve (section 4.19: wall seconds in an hour count for
that hour's multiplier), then fitted by family.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta, tzinfo

import numpy as np

from tiergen.core.ir import Distribution
from tiergen.stats import Dwell, Interval, TransitionEstimate, fit_dwell, transition_matrix, wilson
from tiergen.stats.streams import HOUR, Floats, Stream, hourly


@dataclass(frozen=True, slots=True)
class Curve:
    """Multipliers by local hour, peak 1; ``observed`` flags the hours with exposure."""

    values: tuple[float, ...]
    observed: tuple[bool, ...]
    counts: tuple[float, ...]
    exposure: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class Fitted:
    """``placeholders`` names what the data did not determine and what stands in for it in
    the resources: a transition row never left is uniform, a dwell never observed is
    exponential with the window's length as its mean, the one bound the data give."""

    kind: str
    behaviour: str
    states: tuple[str, ...]
    initial: tuple[float, ...]
    initial_intervals: tuple[Interval, ...]
    transitions: TransitionEstimate
    dwell: tuple[Dwell, ...]
    curve: Curve
    instances: int
    events: int
    placeholders: tuple[str, ...]

    def distributions(self) -> tuple[Distribution, ...]:
        hours = sum(self.curve.exposure) / max(self.instances, 1)
        window = max(1.0, hours * HOUR)
        return tuple(
            Distribution("exponential", (float(window),))
            if d.n == 0
            else Distribution(d.family, d.params)
            for d in self.dwell
        )

    def rows(self) -> tuple[tuple[float, ...], ...]:
        n = len(self.states)
        return tuple(
            tuple(1.0 / n for _ in row) if self.transitions.row_total(i) == 0 else row
            for i, row in enumerate(self.transitions.probabilities)
        )


def fit_curve(streams: Sequence[Stream], tz: tzinfo) -> Curve:
    counts, exposure = hourly(streams, tz)
    observed = exposure > 0
    with np.errstate(divide="ignore", invalid="ignore"):
        rate = np.where(observed, counts / np.where(observed, exposure, 1.0), np.nan)
    peak = float(np.nanmax(rate)) if observed.any() and float(np.nanmax(rate)) > 0 else 1.0
    values = rate / peak
    fill = float(np.nanmean(values)) if observed.any() else 1.0
    values = np.where(observed, values, fill)
    return Curve(
        tuple(float(v) for v in values),
        tuple(bool(o) for o in observed),
        tuple(float(c) for c in counts),
        tuple(float(e) for e in exposure),
    )


def operational(start: float, end: float, curve: Sequence[float], tz: tzinfo) -> float:
    """Operational seconds between two wall times under ``curve``, hour by hour."""
    total = 0.0
    at = start
    while at < end:
        local = datetime.fromtimestamp(at, tz)
        into = local.minute * 60 + local.second + local.microsecond / 1e6
        step = min(HOUR - into, end - at)
        total += step * curve[local.hour]
        at += step
    return total


def _gaps_by_state(
    streams: Sequence[Stream], states: Sequence[str], curve: Sequence[float], tz: tzinfo
) -> dict[str, Floats]:
    found: dict[str, list[float]] = {s: [] for s in states}
    for stream in streams:
        for i in range(len(stream) - 1):
            state = stream.marks[i]
            if state in found:
                found[state].append(operational(stream.times[i], stream.times[i + 1], curve, tz))
    return {s: np.asarray(v, dtype=np.float64) for s, v in found.items()}


def fit_behaviour(
    kind: str, behaviour: str, states: Sequence[str], streams: Sequence[Stream], tz: tzinfo
) -> Fitted:
    curve = fit_curve(streams, tz)
    transitions = transition_matrix(streams, states)
    firsts = [s.marks[0] for s in streams if len(s)]
    initial = tuple(firsts.count(s) / len(firsts) if firsts else math.nan for s in states)
    intervals = tuple(wilson(firsts.count(s), len(firsts)) for s in states)
    gaps = _gaps_by_state(streams, states, curve.values, tz)
    dwell = tuple(fit_dwell(gaps[s]) for s in states)
    placeholders = [
        f"transitions from {s} never observed: uniform row"
        for i, s in enumerate(states)
        if transitions.row_total(i) == 0
    ] + [
        f"dwell of {s} never observed: exponential with the window's length as mean"
        for s, d in zip(states, dwell, strict=True)
        if d.n == 0
    ]
    return Fitted(
        kind,
        behaviour,
        tuple(states),
        initial,
        intervals,
        transitions,
        dwell,
        curve,
        len(streams),
        sum(len(s) for s in streams),
        tuple(placeholders),
    )


def spans_a_week(window: tuple[float, float]) -> bool:
    return window[1] - window[0] >= timedelta(days=7).total_seconds()
