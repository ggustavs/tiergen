"""Two sets of streams compared on section 9's metrics, with permutation p-values.

Each statistic is a distance between the two samples: Wasserstein-1 and Kolmogorov-Smirnov
on the inter-event gaps, Jensen-Shannon between the mark mixes, a G statistic over the
transition counts, and the hourly rate error. The p-value permutes host labels, never
events, so the null is "these hosts are exchangeable", which is the question. Rounds are
few hundred; a p-value is then ``(exceedances + 1) / (rounds + 1)``.
"""

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import tzinfo
from math import comb

import numpy as np

from tiergen.stats.streams import Floats, Stream, hourly, mix, pooled_gaps, transitions

Statistic = Callable[[Sequence[Stream], Sequence[Stream]], float]


@dataclass(frozen=True, slots=True)
class TestResult:
    """``hosts`` and ``events`` are the two samples' sizes. ``splits`` is how many ways the
    hosts can be relabelled: the smallest p-value a permutation can reach is about one over
    it, so below ``1 / alpha`` splits the test cannot reject at all."""

    name: str
    statistic: float
    p_value: float
    hosts: tuple[int, int]
    events: tuple[int, int]
    splits: int

    def can_reject(self, alpha: float) -> bool:
        """Whether a p-value below ``alpha`` is reachable: the identity relabelling always
        counts, so the smallest p is about ``1 / splits`` and must sit strictly below."""
        return 1 / self.splits < alpha


def splits(n_a: int, n_b: int) -> int:
    return comb(n_a + n_b, n_a)


def _cdfs(x: Floats, y: Floats) -> tuple[Floats, Floats, Floats]:
    support = np.sort(np.concatenate([x, y]))
    fx = np.searchsorted(np.sort(x), support, side="right") / len(x)
    fy = np.searchsorted(np.sort(y), support, side="right") / len(y)
    return support, fx, fy


def wasserstein(x: Floats, y: Floats) -> float:
    """W1 between two empirical distributions: the area between their CDFs."""
    if len(x) == 0 or len(y) == 0:
        return math.nan
    support, fx, fy = _cdfs(x, y)
    return float(np.sum(np.abs(fx[:-1] - fy[:-1]) * np.diff(support)))


def ks(x: Floats, y: Floats) -> float:
    if len(x) == 0 or len(y) == 0:
        return math.nan
    _, fx, fy = _cdfs(x, y)
    return float(np.max(np.abs(fx - fy)))


def jensen_shannon(p: dict[str, int], q: dict[str, int]) -> float:
    """Base-2 Jensen-Shannon divergence between two count distributions; in [0, 1]."""
    keys = sorted(set(p) | set(q))
    a = np.asarray([p.get(k, 0) for k in keys], dtype=np.float64)
    b = np.asarray([q.get(k, 0) for k in keys], dtype=np.float64)
    if a.sum() == 0 or b.sum() == 0:
        return math.nan
    a, b = a / a.sum(), b / b.sum()
    m = (a + b) / 2

    def kl(u: Floats) -> float:
        mask = u > 0
        return float(np.sum(u[mask] * np.log2(u[mask] / m[mask])))

    return (kl(a) + kl(b)) / 2


def g_statistic(p: dict[tuple[str, str], int], q: dict[tuple[str, str], int]) -> float:
    """G for homogeneity of two count tables over the union of their cells."""
    keys = sorted(set(p) | set(q))
    table = np.asarray([[p.get(k, 0) for k in keys], [q.get(k, 0) for k in keys]], dtype=np.float64)
    total = table.sum()
    if total == 0 or table.sum(axis=1).min() == 0:
        return math.nan
    expected = np.outer(table.sum(axis=1), table.sum(axis=0)) / total
    mask = table > 0
    return float(2 * np.sum(table[mask] * np.log(table[mask] / expected[mask])))


def gap_wasserstein(a: Sequence[Stream], b: Sequence[Stream]) -> float:
    return wasserstein(pooled_gaps(a), pooled_gaps(b))


def gap_ks(a: Sequence[Stream], b: Sequence[Stream]) -> float:
    return ks(pooled_gaps(a), pooled_gaps(b))


def mix_js(a: Sequence[Stream], b: Sequence[Stream]) -> float:
    return jensen_shannon(mix(a), mix(b))


def transition_g(a: Sequence[Stream], b: Sequence[Stream]) -> float:
    return g_statistic(transitions(a), transitions(b))


def rate_error(tz: tzinfo) -> Statistic:
    """Mean absolute difference of the hourly rates over the hours both observed, relative
    to the second sample's mean rate, so it is scale-free."""

    def statistic(a: Sequence[Stream], b: Sequence[Stream]) -> float:
        ca, ea = hourly(a, tz)
        cb, eb = hourly(b, tz)
        both = (ea > 0) & (eb > 0)
        if not both.any() or eb.sum() == 0:
            return math.nan
        ra, rb = ca[both] / ea[both], cb[both] / eb[both]
        scale = cb.sum() / eb.sum()
        return float(np.mean(np.abs(ra - rb)) / scale) if scale > 0 else math.nan

    return statistic


def statistics(tz: tzinfo) -> dict[str, Statistic]:
    """The shipped statistics by name; the rate error needs the network's local time."""
    return {
        "gap_wasserstein": gap_wasserstein,
        "gap_ks": gap_ks,
        "mix_js": mix_js,
        "transition_g": transition_g,
        "rate_error": rate_error(tz),
    }


def permutation_p(
    statistic: Statistic,
    a: Sequence[Stream],
    b: Sequence[Stream],
    rng: np.random.Generator,
    rounds: int = 500,
) -> tuple[float, float]:
    """The observed statistic and its p-value under host-label permutation. A statistic
    that is ``nan`` on the observed samples gives ``nan``."""
    observed = statistic(a, b)
    if math.isnan(observed):
        return observed, math.nan
    pool = [*a, *b]
    exceed = 0
    for _ in range(rounds):
        order = rng.permutation(len(pool))
        left = [pool[int(i)] for i in order[: len(a)]]
        right = [pool[int(i)] for i in order[len(a) :]]
        value = statistic(left, right)
        if not math.isnan(value) and value >= observed:
            exceed += 1
    return observed, (exceed + 1) / (rounds + 1)


def run_test(
    name: str,
    statistic: Statistic,
    a: Sequence[Stream],
    b: Sequence[Stream],
    rng: np.random.Generator,
    rounds: int = 500,
) -> TestResult:
    observed, p = permutation_p(statistic, a, b, rng, rounds)
    return TestResult(
        name,
        observed,
        p,
        (len(a), len(b)),
        (sum(len(s) for s in a), sum(len(s) for s in b)),
        splits(len(a), len(b)),
    )
