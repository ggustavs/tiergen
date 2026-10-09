"""A verdict is only as good as the test's power: the report prints both."""

from collections.abc import Sequence
from dataclasses import dataclass

from tiergen.stats.calibrate import Calibration, power_for
from tiergen.stats.two_sample import TestResult


@dataclass(frozen=True, slots=True)
class Row:
    """``power`` and ``reference`` come from the calibration nearest the sample; a test
    without one says so, a p-value of ``nan`` is a test that could not run, and too few
    hosts to permute is a test that cannot reject at this level whatever it sees."""

    metric: str
    statistic: float
    p_value: float
    verdict: str
    power: float | None
    reference: str


def report(
    results: Sequence[TestResult],
    calibrations: Sequence[Calibration],
    hosts: int,
    hours: float,
    alpha: float = 0.05,
) -> list[Row]:
    """``hosts`` and ``hours`` are the sample's size, which picks the calibration."""
    rows: list[Row] = []
    for r in results:
        cal = power_for(calibrations, r.name, hosts, hours)
        if r.p_value != r.p_value:  # nan
            verdict = "not computed"
        elif not r.can_reject(alpha):
            verdict = f"too few hosts ({r.splits} splits)"
        else:
            verdict = "rejected" if r.p_value <= alpha else "not rejected"
        rows.append(
            Row(
                r.name,
                r.statistic,
                r.p_value,
                verdict,
                None if cal is None else cal.power,
                "uncalibrated"
                if cal is None
                else f"{cal.perturbation} at {cal.hosts} hosts x {cal.hours:g} h",
            )
        )
    return rows


def render(rows: Sequence[Row], title: str) -> str:
    lines = [
        f"# {title}",
        "",
        "| metric | statistic | p | verdict | power | measured at |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        power = "n/a" if r.power is None else f"{r.power:.2f}"
        lines.append(
            f"| {r.metric} | {r.statistic:.4g} | {r.p_value:.3f} | {r.verdict} | {power} "
            f"| {r.reference} |"
        )
    lines += [
        "",
        "A verdict of not rejected means only what the power column allows: at power 0.2 the "
        "test would miss most differences of the size it was calibrated on.",
    ]
    return "\n".join(lines) + "\n"
