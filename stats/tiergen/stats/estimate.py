"""Estimators with intervals: transition rows, dwell families, hourly rates.

Dwell families are the IR's: exponential, lognormal and Weibull by maximum likelihood,
chosen by AIC, with the empirical family as what remains when none fits. Intervals come
from the binomial (Wilson) for probabilities and from a bootstrap over hosts for anything
else, so a host's internal dependence widens them as it should.
"""

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import tzinfo

import numpy as np

from tiergen.stats.streams import Floats, Stream, hourly, transitions

Z95 = 1.959963984540054


@dataclass(frozen=True, slots=True)
class Interval:
    low: float
    high: float

    def __contains__(self, value: float) -> bool:
        return self.low <= value <= self.high


def wilson(successes: int, trials: int, z: float = Z95) -> Interval:
    """The Wilson score interval for a proportion; the whole unit interval for no trials."""
    if trials == 0:
        return Interval(0.0, 1.0)
    p = successes / trials
    denominator = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denominator
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return Interval(max(0.0, centre - half), min(1.0, centre + half))


@dataclass(frozen=True, slots=True)
class TransitionEstimate:
    """Counts and maximum-likelihood probabilities over ``states``, row by row, with a
    Wilson interval per cell; a row never left has no estimate (``nan``)."""

    states: tuple[str, ...]
    counts: tuple[tuple[int, ...], ...]
    probabilities: tuple[tuple[float, ...], ...]
    intervals: tuple[tuple[Interval, ...], ...]

    def row_total(self, i: int) -> int:
        return sum(self.counts[i])


def transition_matrix(found: Sequence[Stream], states: Sequence[str]) -> TransitionEstimate:
    pairs = transitions(found)
    index = {s: i for i, s in enumerate(states)}
    counts = [[0] * len(states) for _ in states]
    for (a, b), n in pairs.items():
        if a in index and b in index:
            counts[index[a]][index[b]] += n
    probabilities: list[tuple[float, ...]] = []
    intervals: list[tuple[Interval, ...]] = []
    for row in counts:
        total = sum(row)
        probabilities.append(tuple(n / total if total else math.nan for n in row))
        intervals.append(tuple(wilson(n, total) for n in row))
    return TransitionEstimate(
        tuple(states), tuple(tuple(r) for r in counts), tuple(probabilities), tuple(intervals)
    )


@dataclass(frozen=True, slots=True)
class Dwell:
    """A fitted dwell family in the IR's parameterisation: ``(mean)``, ``(mu, sigma)``,
    ``(shape, scale)``, or every sample for ``empirical``."""

    family: str
    params: tuple[float, ...]
    loglik: float
    n: int

    @property
    def aic(self) -> float:
        k = {"exponential": 1, "lognormal": 2, "weibull": 2}.get(self.family, self.n)
        return 2 * k - 2 * self.loglik

    @property
    def mean(self) -> float:
        if self.family == "exponential":
            return self.params[0]
        if self.family == "lognormal":
            mu, sigma = self.params
            return math.exp(mu + sigma * sigma / 2)
        if self.family == "weibull":
            shape, scale = self.params
            return scale * math.gamma(1 + 1 / shape)
        return float(np.mean(self.params)) if self.params else math.nan


def fit_exponential(x: Floats) -> Dwell:
    mean = float(np.mean(x))
    return Dwell("exponential", (mean,), -len(x) * (math.log(mean) + 1), len(x))


def fit_lognormal(x: Floats) -> Dwell:
    logs = np.log(x)
    mu, sigma = float(np.mean(logs)), float(np.std(logs))
    if sigma == 0.0:
        return Dwell("lognormal", (mu, 0.0), -math.inf, len(x))
    loglik = -float(np.sum(logs)) - len(x) * math.log(sigma * math.sqrt(2 * math.pi)) - len(x) / 2
    return Dwell("lognormal", (mu, sigma), loglik, len(x))


def fit_weibull(x: Floats, iterations: int = 100) -> Dwell:
    """Shape by Newton's method on the profile likelihood equation, scale in closed form."""
    logs = np.log(x)
    mean_log = float(np.mean(logs))
    k = 1.0
    for _ in range(iterations):
        xk = x**k
        s0, s1, s2 = float(np.sum(xk)), float(np.sum(xk * logs)), float(np.sum(xk * logs * logs))
        f = s1 / s0 - 1 / k - mean_log
        df = (s2 * s0 - s1 * s1) / (s0 * s0) + 1 / (k * k)
        step = f / df
        k_next = max(k - step, 1e-3)
        if abs(k_next - k) < 1e-10:
            k = k_next
            break
        k = k_next
    scale = float(np.mean(x**k)) ** (1 / k)
    n = len(x)
    scaled: Floats = (x / scale) ** k
    loglik = (
        n * math.log(k)
        - n * k * math.log(scale)
        + (k - 1) * float(np.sum(logs))
        - float(np.sum(scaled))
    )
    return Dwell("weibull", (k, scale), loglik, n)


FAMILIES: dict[str, Callable[[Floats], Dwell]] = {
    "exponential": fit_exponential,
    "lognormal": fit_lognormal,
    "weibull": fit_weibull,
}


def fit_dwell(samples: Floats, families: Sequence[str] = tuple(FAMILIES)) -> Dwell:
    """The family of least AIC among ``families``; ``empirical`` (the samples themselves)
    when there are too few samples to tell, under five, or none is positive."""
    x = np.asarray(samples, dtype=np.float64)
    x = x[x > 0]
    if len(x) < 5:
        return Dwell("empirical", tuple(float(v) for v in x), math.nan, len(x))
    fits = [FAMILIES[f](x) for f in families]
    return min(fits, key=lambda d: d.aic)


def bootstrap_interval(
    statistic: Callable[[Sequence[Stream]], float],
    found: Sequence[Stream],
    rng: np.random.Generator,
    rounds: int = 200,
    level: float = 0.95,
) -> Interval:
    """A percentile interval from resampling hosts with replacement."""
    values: list[float] = []
    n = len(found)
    for _ in range(rounds):
        picks = rng.integers(0, n, size=n)
        values.append(statistic([found[int(i)] for i in picks]))
    tail = (1 - level) / 2
    low, high = np.quantile(np.asarray(values), [tail, 1 - tail])
    return Interval(float(low), float(high))


def hourly_rate(found: Sequence[Stream], tz: tzinfo) -> Floats:
    """Events per host-hour by local hour; ``nan`` where no host was observed."""
    counts, exposure = hourly(found, tz)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(exposure > 0, counts / exposure, np.nan)
