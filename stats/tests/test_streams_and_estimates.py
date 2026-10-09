import math
from collections.abc import Callable
from datetime import UTC, datetime

import numpy as np
import pytest

from tiergen.core.events import ConnEvent, FiveTuple, SensorFlowId
from tiergen.stats import (
    Stream,
    fit_dwell,
    gaps,
    hourly,
    hourly_rate,
    mix,
    streams,
    transition_matrix,
    transitions,
    wilson,
)
from tiergen.stats.estimate import fit_exponential, fit_lognormal, fit_weibull
from tiergen.stats.streams import Floats, local_tz

T0 = datetime(2026, 10, 5, 8, 0, tzinfo=UTC).timestamp()


def conn(host: str, at: float, port: int) -> ConnEvent:
    return ConnEvent(
        SensorFlowId("s", "p", f"{host}-{at}"),
        FiveTuple(host, 40000, "10.0.0.80", port, "tcp"),
        T0 + at,
        None,
        None,
        None,
        None,
        None,
        "closed",
        {},
    )


def test_streams_group_by_originator_inside_the_window_and_keep_idle_hosts() -> None:
    conns = [conn("a", 5, 80), conn("b", 1, 8080), conn("a", 2, 80), conn("a", 7200, 80)]
    found = streams(conns, (T0, T0 + 3600), hosts=["a", "b", "c"])
    assert [s.host for s in found] == ["a", "b", "c"]
    a, b, c = found
    assert a.times == (T0 + 2, T0 + 5)
    assert a.marks == ("tcp/80", "tcp/80")
    assert b.marks == ("tcp/8080",)
    assert len(c) == 0
    assert list(gaps(a)) == [3.0]
    assert mix(found) == {"tcp/80": 2, "tcp/8080": 1}
    assert transitions(found) == {("tcp/80", "tcp/80"): 1}
    assert [s.host for s in streams(conns, (T0, T0 + 3600))] == ["a", "b"]


def test_hourly_counts_and_exposure_follow_the_local_clock() -> None:
    tz = local_tz("2026-10-05T08:00:00+02:00")
    start = datetime(2026, 10, 5, 8, 30, tzinfo=tz).timestamp()
    s = Stream("a", (start + 60, start + 1800 + 60), ("x", "x"), (start, start + 3600))
    counts, exposure = hourly([s], tz)
    assert counts[8] == 1
    assert counts[9] == 1
    assert exposure[8] == pytest.approx(0.5)
    assert exposure[9] == pytest.approx(0.5)
    assert exposure.sum() == pytest.approx(1.0)
    rate = hourly_rate([s], tz)
    assert rate[8] == pytest.approx(2.0)
    assert math.isnan(rate[10])


def test_a_transition_matrix_has_rows_with_intervals_and_nan_for_unseen_rows() -> None:
    s = Stream("a", tuple(float(i) for i in range(6)), ("x", "y", "x", "y", "y", "x"), (0.0, 6.0))
    est = transition_matrix([s], ("x", "y", "z"))
    assert est.counts == ((0, 2, 0), (2, 1, 0), (0, 0, 0))
    assert est.probabilities[0] == (0.0, 1.0, 0.0)
    assert est.probabilities[1] == pytest.approx((2 / 3, 1 / 3, 0.0))
    assert all(math.isnan(p) for p in est.probabilities[2])
    assert 1 / 3 in est.intervals[1][1]
    assert est.intervals[2][0].low == 0.0
    assert est.intervals[2][0].high == 1.0


def test_wilson_covers_the_truth_at_about_its_level() -> None:
    rng = np.random.default_rng(1)
    covered = sum(0.3 in wilson(int(rng.binomial(50, 0.3)), 50) for _ in range(400))
    assert 0.90 <= covered / 400 <= 0.99


def _exponential(rng: np.random.Generator, n: int) -> Floats:
    return rng.exponential(20.0, n)


def _lognormal(rng: np.random.Generator, n: int) -> Floats:
    return rng.lognormal(2.0, 0.5, n)


def _weibull(rng: np.random.Generator, n: int) -> Floats:
    return 15.0 * rng.weibull(1.5, n)


@pytest.mark.parametrize(
    ("family", "draw", "truth"),
    [
        ("exponential", _exponential, (20.0,)),
        ("lognormal", _lognormal, (2.0, 0.5)),
        ("weibull", _weibull, (1.5, 15.0)),
    ],
)
def test_each_family_is_recovered_and_chosen_by_aic(
    family: str, draw: Callable[[np.random.Generator, int], Floats], truth: tuple[float, ...]
) -> None:
    rng = np.random.default_rng(7)
    x = draw(rng, 4000)
    fitted = fit_dwell(x)
    assert fitted.family == family
    assert fitted.params == pytest.approx(truth, rel=0.08)
    assert fitted.mean == pytest.approx(float(np.mean(x)), rel=0.05)


def test_the_likelihoods_agree_with_their_closed_forms() -> None:
    x = np.asarray([1.0, 2.0, 4.0, 8.0, 16.0])
    e = fit_exponential(x)
    assert e.loglik == pytest.approx(-5 * (math.log(6.2) + 1))
    ln = fit_lognormal(x)
    logs = np.log(x)
    mu, sigma = logs.mean(), logs.std()
    assert ln.loglik == pytest.approx(
        -logs.sum()
        - 5 * math.log(sigma * math.sqrt(2 * math.pi))
        - ((logs - mu) ** 2).sum() / (2 * sigma**2)
    )
    w = fit_weibull(x)
    k, lam = w.params
    assert w.loglik == pytest.approx(
        5 * math.log(k) - 5 * k * math.log(lam) + (k - 1) * logs.sum() - ((x / lam) ** k).sum()
    )
    assert fit_dwell(np.asarray([1.0, 2.0])).family == "empirical"
