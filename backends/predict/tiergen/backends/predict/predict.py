"""Replicated simulations, reduced to the statistics a sensor would report.

Per kind and per service (transport and responder port): connections per host-hour, and
the median and 90th percentile of the gap between a host's consecutive connections, each
as the mean over replicates with a 95% interval from the replicates' spread (a normal
approximation over the replicate means; with few replicates the interval says so by
being wide). Durations and bytes are not predicted until M3 measures the implementations.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from tiergen.core.events import ConnEvent
from tiergen.core.ir import Scenario
from tiergen.core.resolve import Resolver
from tiergen.core.resources import Resources
from tiergen.sim import simulate
from tiergen.stats import Stream, service, streams
from tiergen.stats.streams import Floats


@dataclass(frozen=True, slots=True)
class Row:
    kind: str
    service: str
    rate: float
    rate_interval: tuple[float, float]
    gap_median: float
    gap_p90: float


@dataclass(frozen=True, slots=True)
class Prediction:
    scenario: str
    replicates: int
    hours: float
    hosts: dict[str, int]
    rows: tuple[Row, ...]


def _interval(values: Sequence[float]) -> tuple[float, float]:
    if len(values) < 2:
        return (math.nan, math.nan)
    x = np.asarray(values, dtype=np.float64)
    half = 1.96 * float(np.std(x, ddof=1)) / math.sqrt(len(x))
    return (float(np.mean(x)) - half, float(np.mean(x)) + half)


def predict(
    scenario: Scenario, resources: Resources, *, replicates: int = 5, hours: float | None = None
) -> Prediction:
    hours = hours if hours is not None else scenario.duration_s / 3600
    topology = Resolver(resources).topology(scenario)
    data: set[str] = {s.name for s in topology.segments if s.plane == "data"} if topology else set()
    rates: dict[tuple[str, str], list[float]] = {}
    gaps: dict[str, list[Floats]] = {}
    hosts_of: dict[str, int] = {}
    for r in range(replicates):
        sim = simulate(scenario, resources, seed=scenario.seed + r, duration_s=hours * 3600)
        epoch = sim.records[0].start - sim.records[0].clock.monotonic if sim.records else 0.0
        window = (epoch, epoch + hours * 3600)
        kinds: dict[str, list[str]] = {}
        for instance, program in sim.programs.items():
            if program.behaviours:
                kinds.setdefault(program.kind, []).extend(
                    a for seg, a in sim.plan.addresses[instance].items() if seg in data
                )
        conns = [e for e in sim.events if isinstance(e, ConnEvent)]
        for kind, addresses in kinds.items():
            hosts_of[kind] = len(addresses)
            found: list[Stream] = streams(conns, window, service, hosts=addresses)
            exposure = len(addresses) * hours
            by_service: dict[str, int] = {}
            for s in found:
                for m in s.marks:
                    by_service[m] = by_service.get(m, 0) + 1
                if len(s) > 1:
                    gaps.setdefault(kind, []).append(np.diff(np.asarray(s.times)))
            for svc, n in by_service.items():
                rates.setdefault((kind, svc), []).append(n / exposure if exposure else math.nan)
    rows: list[Row] = []
    for (kind, svc), values in sorted(rates.items()):
        pooled = np.concatenate(gaps[kind]) if gaps.get(kind) else np.zeros(0)
        median = float(np.median(pooled)) if len(pooled) else math.nan
        p90 = float(np.quantile(pooled, 0.9)) if len(pooled) else math.nan
        while len(values) < replicates:
            values.append(0.0)
        rows.append(Row(kind, svc, float(np.mean(values)), _interval(values), median, p90))
    return Prediction(scenario.name, replicates, hours, hosts_of, tuple(rows))


def render(p: Prediction) -> str:
    lines = [
        f"# Prediction for {p.scenario}",
        "",
        f"{p.replicates} replicate(s) of {p.hours:g} h; connections per host-hour with a 95% "
        "interval over replicates; gaps between a host's consecutive connections, pooled.",
        "",
        "| kind | hosts | service | rate /host-h | 95% | gap median s | gap p90 s |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in p.rows:
        low, high = r.rate_interval
        lines.append(
            f"| {r.kind} | {p.hosts.get(r.kind, 0)} | {r.service} | {r.rate:.2f} "
            f"| ({low:.2f}, {high:.2f}) | {r.gap_median:.1f} | {r.gap_p90:.1f} |"
        )
    return "\n".join(lines) + "\n"
