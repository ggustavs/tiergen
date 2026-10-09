"""What makes a test shippable: its type-I rate and its power, measured.

A test is run on pairs of simulations of one harness scenario under different seeds (the
positive control: it must reject at the nominal rate and no more) and on pairs where the
second comes from a perturbed scenario (the negative control: it must reject often enough
to be worth running). Both rates carry Wilson intervals over the seeds. The table of every
test, perturbation and sample size is the calibration, kept with the package so a report
can print a test's power beside its verdict.
"""

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from importlib.resources import files

import numpy as np

from tiergen.core.codec import from_json, to_json
from tiergen.stats.estimate import Interval, wilson
from tiergen.stats.streams import Stream
from tiergen.stats.two_sample import Statistic, permutation_p

Generate = Callable[[int], list[Stream]]
"""Streams for a seed."""

TABLE = "calibration.json"


@dataclass(frozen=True, slots=True)
class Calibration:
    """One test at one perturbation and one sample size: ``type_i`` is the rejection rate
    under the null, ``power`` under the perturbation, over ``seeds`` pairs each."""

    test: str
    perturbation: str
    hosts: int
    hours: float
    seeds: int
    alpha: float
    type_i: float
    type_i_interval: Interval
    power: float
    power_interval: Interval


def rejection_rate(
    statistic: Statistic,
    pairs: Sequence[tuple[Sequence[Stream], Sequence[Stream]]],
    rng: np.random.Generator,
    alpha: float,
    rounds: int,
) -> tuple[float, Interval]:
    rejected = 0
    for a, b in pairs:
        _, p = permutation_p(statistic, a, b, rng, rounds)
        rejected += p <= alpha
    return rejected / len(pairs), wilson(rejected, len(pairs))


def calibrate(
    test: str,
    statistic: Statistic,
    null: Generate,
    alternative: Generate,
    *,
    perturbation: str,
    hosts: int,
    hours: float,
    seeds: int,
    rng: np.random.Generator,
    alpha: float = 0.05,
    rounds: int = 200,
) -> Calibration:
    """Seeds ``2s`` and ``2s + 1`` make a pair; the null pairs two null draws, the
    alternative pairs a null draw with a perturbed one."""
    null_pairs = [(null(2 * s), null(2 * s + 1)) for s in range(seeds)]
    alt_pairs = [(null(2 * s), alternative(2 * s + 1)) for s in range(seeds)]
    type_i, type_i_interval = rejection_rate(statistic, null_pairs, rng, alpha, rounds)
    power, power_interval = rejection_rate(statistic, alt_pairs, rng, alpha, rounds)
    return Calibration(
        test,
        perturbation,
        hosts,
        hours,
        seeds,
        alpha,
        type_i,
        type_i_interval,
        power,
        power_interval,
    )


def markdown(rows: Sequence[Calibration]) -> str:
    lines = [
        "| test | perturbation | hosts | hours | seeds | type I (95%) | power (95%) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r.test} | {r.perturbation} | {r.hosts} | {r.hours:g} | {r.seeds} "
            f"| {r.type_i:.3f} ({r.type_i_interval.low:.3f}, {r.type_i_interval.high:.3f}) "
            f"| {r.power:.2f} ({r.power_interval.low:.2f}, {r.power_interval.high:.2f}) |"
        )
    return "\n".join(lines) + "\n"


def dump(rows: Sequence[Calibration]) -> str:
    return json.dumps(to_json(list(rows)), indent=2) + "\n"


def load(text: str) -> list[Calibration]:
    return list(from_json(tuple[Calibration, ...], json.loads(text)))


def shipped() -> list[Calibration]:
    """The table kept with the package, or nothing before the first calibration."""
    path = files(__package__) / TABLE
    try:
        return load(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError):
        return []


def power_for(
    rows: Sequence[Calibration], test: str, hosts: int, hours: float
) -> Calibration | None:
    """The calibration of ``test`` at the sample size nearest ``hosts`` times ``hours`` in
    log terms, at the weakest perturbation measured there; None if the test was never
    calibrated."""
    mine = [r for r in rows if r.test == test]
    if not mine:
        return None
    size = max(hosts * hours, 1e-9)
    nearest = min(mine, key=lambda r: abs(np.log(max(r.hosts * r.hours, 1e-9) / size)))
    at_size = [r for r in mine if (r.hosts, r.hours) == (nearest.hosts, nearest.hours)]
    return min(at_size, key=lambda r: r.power)
