"""Recovery: the fit of a simulated run against the scenario that generated it."""

import json
import shutil
from datetime import datetime
from pathlib import Path

import pytest

from tiergen.check import run_checks
from tiergen.cli.main import main
from tiergen.core.codec import from_json
from tiergen.core.ir import Scenario
from tiergen.core.loader import load_scenario
from tiergen.core.resources import DictResources, DirResources
from tiergen.fit import Fitted, fit_run, projection
from tiergen.fit.behaviour import fit_behaviour, operational
from tiergen.impls._base import load_impls
from tiergen.interfaces.registry import load_infra, load_sensors
from tiergen.sim import simulate, write
from tiergen.stats import Stream
from tiergen.stats.harness import Harness, office
from tiergen.stats.streams import local_tz

EXAMPLES = Path(__file__).parents[2] / "examples"
CURVE = [0.2] * 8 + [1.0] * 10 + [0.2] * 6
TRUTH_NO_IDLE = ((0.2, 0.5, 0.3), (0.4, 0.2, 0.4), (0.5, 0.3, 0.2))


def _fit(h: Harness, tmp_path: Path, *, hours: float) -> Fitted:
    sim = simulate(h.scenario, DictResources(h.resources), duration_s=hours * 3600)
    write(sim, tmp_path / "run")
    summary = fit_run(tmp_path / "run", "sim", tmp_path / "out")
    [fitted] = summary.fits
    assert summary.labelled.unmapped.by_reason == {}
    return fitted


def test_the_observable_chain_is_recovered_without_a_silent_state(tmp_path: Path) -> None:
    f = _fit(office(10, idle=False), tmp_path, hours=8.0)
    assert f.states == ("web_get", "wiki_get", "api_get")
    assert f.instances == 10
    covered = sum(
        TRUTH_NO_IDLE[i][j] in f.transitions.intervals[i][j] for i in range(3) for j in range(3)
    )
    assert covered >= 8, f.transitions
    assert all(
        abs(f.transitions.probabilities[i][j] - TRUTH_NO_IDLE[i][j]) < 0.05
        for i in range(3)
        for j in range(3)
    )
    assert [d.family for d in f.dwell] == ["exponential", "lognormal", "weibull"]
    assert f.dwell[0].params[0] == pytest.approx(10.0, rel=0.1)
    assert f.dwell[1].params == pytest.approx((2.0, 0.5), abs=0.1)
    assert f.dwell[2].params == pytest.approx((1.5, 15.0), rel=0.15)
    assert f.initial == (1.0, 0.0, 0.0)
    observed = [v for v, seen in zip(f.curve.values, f.curve.observed, strict=True) if seen]
    assert len(observed) == 8
    assert min(observed) > 0.85


def test_a_silent_state_is_recovered_through_the_projection(tmp_path: Path) -> None:
    h = office(10, idle=True)
    f = _fit(h, tmp_path, hours=8.0)
    p = next(k for k in h.scenario.kinds if k.name == "workstation").behaviours[0]
    process = p.process
    assert not isinstance(process.states, str)
    assert not isinstance(process.initial, str)
    assert not isinstance(process.transitions, str)
    assert not isinstance(process.dwell, str)
    assert not isinstance(p.action_map, str)
    means = [60.0, 10.0, 7.389 * 1.133, 15.0 * 0.9027]  # exp, lognormal(2, .5), weibull(1.5, 15)
    truth = projection(process.states, process.initial, process.transitions, p.action_map, means)
    assert truth.states == f.states
    assert all(
        abs(f.transitions.probabilities[i][j] - truth.transitions[i][j]) < 0.06
        for i in range(3)
        for j in range(3)
    ), (f.transitions.probabilities, truth.transitions)
    assert f.initial == pytest.approx(truth.initial, abs=0.2)
    for i, d in enumerate(f.dwell):
        expected = means[i + 1] + truth.silent_mean[i]
        assert d.mean == pytest.approx(expected, rel=0.15), (f.states[i], d, expected)


def test_the_rate_curve_is_recovered_over_a_day_and_the_dwell_with_it(tmp_path: Path) -> None:
    f = _fit(office(5, idle=False, rate=CURVE), tmp_path, hours=24.0)
    assert all(f.curve.observed)
    for hour, value in enumerate(f.curve.values):
        assert value == pytest.approx(CURVE[hour], abs=0.15), hour
    assert f.dwell[0].family == "exponential"
    assert f.dwell[0].params[0] == pytest.approx(10.0, rel=0.15)


def test_what_the_data_do_not_determine_is_a_named_placeholder() -> None:
    tz = local_tz("2026-10-05T08:00:00+02:00")
    start = datetime(2026, 10, 5, 8, 0, tzinfo=tz).timestamp()
    streams = [Stream("h", (start + 10.0,), ("a",), (start, start + 600.0))]
    f = fit_behaviour("k", "b", ("a", "b"), streams, tz)
    assert f.rows() == ((0.5, 0.5), (0.5, 0.5))
    assert [d.family for d in f.distributions()] == ["exponential", "exponential"]
    assert f.distributions()[0].params == (600.0,)
    assert f.placeholders == (
        "transitions from a never observed: uniform row",
        "transitions from b never observed: uniform row",
        "dwell of a never observed: exponential with the window's length as mean",
        "dwell of b never observed: exponential with the window's length as mean",
    )


def test_operational_time_follows_the_curve_hour_by_hour() -> None:
    tz = local_tz("2026-10-05T08:00:00+02:00")
    start = datetime(2026, 10, 5, 7, 30, tzinfo=tz).timestamp()
    curve = [0.5] * 8 + [1.0] * 16
    assert operational(start, start + 3600, curve, tz) == pytest.approx(1800 * 0.5 + 1800 * 1.0)


def test_the_fitted_scenario_passes_the_checks_and_the_command_writes_it(tmp_path: Path) -> None:
    scenario = load_scenario(EXAMPLES / "linux_slice" / "scenario.py")
    models = EXAMPLES / "linux_slice" / "models"
    sim = simulate(scenario, DirResources(models), duration_s=1800)
    write(sim, tmp_path / "run")
    out = tmp_path / "out"
    shutil.copytree(models, out)
    assert main(["fit", str(tmp_path / "run"), "--sensor", "sim", "--out", str(out)]) == 0
    for name in (
        "workstation.browse.states",
        "workstation.browse.transitions",
        "workstation.browse.dwell",
        "workstation.browse.rate",
        "workstation.browse.action_map",
        "attacker.recon.states",
        "fit_provenance",
    ):
        assert (out / f"{name}.json").is_file(), name
    assert json.loads((out / "workstation.browse.states.json").read_text()) == ["web_get"]
    report = (out / "fit-report.md").read_text()
    assert "## workstation / browse" in report
    assert "## attacker / recon" in report
    fitted = from_json(Scenario, json.loads((out / "scenario_fitted.json").read_text()))
    assert fitted.name == "linux_slice_fitted"
    assert fitted.fit_provenance is None, "a simulation is no sensor, so no provenance"
    assert (out / "fit_provenance.json").is_file()
    found = run_checks(fitted, DirResources(out), load_impls(), load_sensors(), load_infra())
    assert [d for d in found if d.severity == "error"] == []
    assert main(["fit", str(tmp_path / "run"), "--sensor", "nope", "--out", str(out)]) == 2
