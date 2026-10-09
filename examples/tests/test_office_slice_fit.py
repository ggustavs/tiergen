"""The round trip on the simulator: office_slice generated, fitted, compared through the
projection. The real run does the same by hand (examples/README.md)."""

from pathlib import Path

import pytest

from tiergen.core.loader import load_scenario
from tiergen.core.resources import DirResources
from tiergen.fit import fit_run, projection
from tiergen.sim import simulate, write

EXAMPLES = Path(__file__).parent.parent
MEANS = [45.0, 8.0, 2.718281828**2.125, 12.0 * 0.9027]  # idle, web_get, news, files


def test_office_slice_is_recovered_from_its_own_simulation(tmp_path: Path) -> None:
    scenario = load_scenario(EXAMPLES / "office_slice" / "scenario.py")
    resources = DirResources(EXAMPLES / "office_slice" / "models")
    write(simulate(scenario, resources, duration_s=2 * 3600), tmp_path / "run")
    summary = fit_run(tmp_path / "run", "sim", tmp_path / "out")
    office = next(f for f in summary.fits if (f.kind, f.behaviour) == ("workstation", "office"))
    assert office.states == ("web_get", "news", "files")
    assert office.instances == 5
    ws = next(k for k in scenario.kinds if k.name == "workstation")
    b = ws.behaviours[0]
    p = b.process
    assert not isinstance(p.states, str)
    assert not isinstance(p.initial, str)
    assert not isinstance(p.transitions, str)
    assert not isinstance(b.action_map, str)
    truth = projection(p.states, p.initial, p.transitions, b.action_map, MEANS)
    for i in range(3):
        for j in range(3):
            assert office.transitions.probabilities[i][j] == pytest.approx(
                truth.transitions[i][j], abs=0.08
            ), (i, j)
    for i, d in enumerate(office.dwell):
        assert d.mean == pytest.approx(MEANS[i + 1] + truth.silent_mean[i], rel=0.2), office.states[
            i
        ]
    observed = [h for h, seen in enumerate(office.curve.observed) if seen]
    assert observed == [8, 9]
    assert summary.labelled.unmapped.by_reason == {}
