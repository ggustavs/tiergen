from dataclasses import replace

import pytest
from hypothesis import given
from hypothesis import strategies as st
from support import good, only

from tiergen.core import ir


def _with(*events: ir.ScheduleEvent) -> ir.Scenario:
    return replace(good(), schedule=events)


@pytest.mark.parametrize(
    ("event", "path", "fragment"),
    [
        (ir.ScheduleEvent(3601, "cli", "start", "surf"), "schedule[0].at_s", "outside the run"),
        (ir.ScheduleEvent(-1, "cli", "start", "surf"), "schedule[0].at_s", "outside the run"),
        (ir.ScheduleEvent(0, "ghost", "start", "surf"), "schedule[0].target", "not a kind"),
        (ir.ScheduleEvent(0, "cli[3]", "start", "surf"), "schedule[0].target", "3 instances"),
        (ir.ScheduleEvent(0, "cli[x]", "start", "surf"), "schedule[0].target", "neither"),
        (ir.ScheduleEvent(0, "cli", "start", "sleep"), "schedule[0].arg", "no behaviour 'sleep'"),
        (ir.ScheduleEvent(0, "cli", "stop", None), "schedule[0].arg", "name of a behaviour"),
        (ir.ScheduleEvent(0, "cli", "set_rate", "fast"), "schedule[0].arg", "non-negative"),
        (ir.ScheduleEvent(0, "cli", "set_rate", -0.5), "schedule[0].arg", "non-negative"),
        (
            ir.ScheduleEvent(0, "cli", "run_sequence", 3.0),
            "schedule[0].arg",
            "adapter:catalog-entry",
        ),
    ],
)
def test_ill_formed_events(event: ir.ScheduleEvent, path: str, fragment: str) -> None:
    [d] = only("C12", _with(event))
    assert (d.severity, d.path) == ("error", path)
    assert fragment in d.message


def test_instance_selector_in_range_and_boundary_times_pass() -> None:
    events = (
        ir.ScheduleEvent(0, "cli[0]", "start", "surf"),
        ir.ScheduleEvent(3600, "cli[2]", "stop", "surf"),
    )
    assert only("C12", _with(*events)) == []


@given(at_s=st.floats(allow_nan=False, allow_infinity=False))
def test_time_is_rejected_exactly_when_outside_the_run(at_s: float) -> None:
    found = only("C12", _with(ir.ScheduleEvent(at_s, "cli", "start", "surf")))
    assert bool(found) == (not 0 <= at_s <= 3600)
