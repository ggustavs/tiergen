"""Statistics over event streams, every one of them validated on the simulator.

Three layers. ``streams`` turns connections into one stream per host, the unit of
dependence everything below resamples. ``estimate`` fits transition rows, dwell families
and hourly rates with intervals. ``two_sample`` compares two sets of streams on section 9's
metrics with host-level permutation p-values. ``calibrate`` measures each test's type-I
rate and power on the harness scenarios, and ``report`` prints a verdict beside the power
that was measured, so a test that cannot tell never reads as a pass. Nothing here uses an
asymptotic distribution: inference is by permutation and bootstrap over hosts, which is
what the dependence within a host calls for.
"""

from tiergen.stats.calibrate import Calibration, calibrate, markdown, power_for
from tiergen.stats.estimate import (
    Dwell,
    Interval,
    TransitionEstimate,
    bootstrap_interval,
    fit_dwell,
    hourly_rate,
    transition_matrix,
    wilson,
)
from tiergen.stats.report import Row, render, report
from tiergen.stats.streams import Stream, gaps, hourly, mix, service, streams, transitions
from tiergen.stats.two_sample import Statistic, TestResult, permutation_p, run_test, statistics

__all__ = [
    "Calibration",
    "Dwell",
    "Interval",
    "Row",
    "Statistic",
    "Stream",
    "TestResult",
    "TransitionEstimate",
    "bootstrap_interval",
    "calibrate",
    "fit_dwell",
    "gaps",
    "hourly",
    "hourly_rate",
    "markdown",
    "mix",
    "permutation_p",
    "power_for",
    "render",
    "report",
    "run_test",
    "service",
    "statistics",
    "streams",
    "transition_matrix",
    "transitions",
    "wilson",
]
