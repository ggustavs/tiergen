"""Dwell times and the rate curve: how operational time becomes wall time.

A behaviour's process runs in operational time. The rate curve, hourly multipliers over a
day or a week in the network's local time, and the schedule's ``set_rate`` factor set the
speed at which operational time passes: at multiplier 2 a dwell takes half as long on the
wall, at 0 the process is frozen until the hour changes. This is a time change of the whole
process, so expected invocations per wall hour follow the curve, which is how section 9 of
the design denotes a scenario.
"""

from datetime import datetime, timedelta
from random import Random

from tiergen.core.ir import Distribution

HOUR = 3600.0


def dwell(random: Random, d: Distribution) -> float:
    """One holding time in operational seconds, drawn from ``random``."""
    params = d.params
    assert not isinstance(params, str)  # load_program held this
    if d.family == "exponential":
        return random.expovariate(1.0 / params[0])
    if d.family == "lognormal":
        return random.lognormvariate(params[0], params[1])
    if d.family == "weibull":
        shape, scale = params
        return random.weibullvariate(scale, shape)
    return random.choice(params)


def multiplier(curve: tuple[float, ...] | None, local: datetime) -> float:
    """The curve's entry for a local time: by hour for 24 entries, by weekday and hour for
    168, Monday's first hour first. No curve is a flat 1."""
    if curve is None:
        return 1.0
    if len(curve) == 24:
        return curve[local.hour]
    return curve[local.weekday() * 24 + local.hour]


def advance(
    operational: float,
    t: float,
    limit: float,
    start: datetime,
    curve: tuple[float, ...] | None,
    factor: float,
) -> tuple[float, float]:
    """Wall seconds from scenario time ``t`` until ``operational`` seconds have passed at
    the curve's speed times ``factor``, and the operational seconds that did pass, which is
    less than asked when ``limit`` wall seconds come first. ``start`` is the scenario's
    start in the network's local time; the curve is read against it."""
    elapsed = 0.0
    left = operational
    while left > 0 and elapsed < limit:
        local = start + timedelta(seconds=t + elapsed)
        rate = factor * multiplier(curve, local)
        into_hour = local.minute * 60 + local.second + local.microsecond / 1e6
        boundary = min(HOUR - into_hour, limit - elapsed)
        if rate > 0 and left / rate <= boundary:
            elapsed += left / rate
            left = 0.0
        else:
            elapsed += boundary
            left -= boundary * rate
    return elapsed, operational - max(left, 0.0)
