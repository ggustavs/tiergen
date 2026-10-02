from datetime import datetime
from random import Random

from agent_support import START

from tiergen.core.ir import Distribution
from tiergen.runtime.agent_linux.sampling import advance, dwell, multiplier


def test_every_family_draws_a_non_negative_time_deterministically() -> None:
    for d in (
        Distribution("exponential", (20.0,)),
        Distribution("lognormal", (1.0, 0.5)),
        Distribution("weibull", (1.5, 10.0)),
        Distribution("empirical", (1.0, 2.0, 3.0)),
    ):
        a = [dwell(Random(3), d) for _ in range(3)]
        assert a == [dwell(Random(3), d) for _ in range(3)]
        assert all(x >= 0 for x in a)
    assert dwell(Random(1), Distribution("empirical", (4.0,))) == 4.0


def test_the_curve_is_indexed_by_hour_or_by_weekday_and_hour() -> None:
    monday_8 = datetime.fromisoformat(START)
    assert multiplier(None, monday_8) == 1.0
    assert multiplier(tuple(float(h) for h in range(24)), monday_8) == 8.0
    assert multiplier(tuple(float(i) for i in range(168)), monday_8) == 8.0
    assert multiplier(tuple(float(i) for i in range(168)), monday_8.replace(day=6)) == 32.0


def test_advance_is_a_time_change_of_operational_time() -> None:
    start = datetime.fromisoformat(START)
    assert advance(10.0, 0.0, 1e9, start, None, 1.0) == (10.0, 10.0)
    assert advance(10.0, 0.0, 1e9, start, None, 2.0) == (5.0, 10.0)
    # Frozen for the first two hours, then at speed 1.
    curve = tuple(0.0 if h < 10 else 1.0 for h in range(24))
    assert advance(10.0, 0.0, 1e9, start, curve, 1.0) == (7210.0, 10.0)
    # Cut short by the limit: what passed is what was consumed.
    assert advance(10.0, 0.0, 4.0, start, None, 1.0) == (4.0, 4.0)
    assert advance(10.0, 0.0, 4.0, start, None, 0.5) == (4.0, 2.0)
    # Starting mid-hour at speed 0.5 and crossing into an hour at speed 2.
    curve = tuple(2.0 if h == 9 else 0.5 for h in range(24))
    wall, done = advance(1800.0, 3000.0, 1e9, start, curve, 1.0)
    assert done == 1800.0
    assert abs(wall - (600 + (1800 - 300) / 2)) < 1e-6
