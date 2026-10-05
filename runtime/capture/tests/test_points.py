import json
from pathlib import Path

import pytest

from tiergen.cli.main import main
from tiergen.core.codec import to_json
from tiergen.interfaces import RunState
from tiergen.runtime.capture.points import CaptureError, Point, capture_points, load_run

EXAMPLES = Path(__file__).parents[3] / "examples"


def _run(tmp_path: Path, name: str, bridges: dict[str, str]) -> Path:
    run_dir = tmp_path / name
    assert main(["build", str(EXAMPLES / name / "scenario.py"), "--out", str(run_dir)]) == 0
    state = RunState(name, "docker", bridges=bridges)
    (run_dir / "state.docker.json").write_text(json.dumps(to_json(state)))
    return run_dir


def test_linux_slice_has_one_untagged_point_on_one_bridge(tmp_path: Path) -> None:
    run = load_run(_run(tmp_path, "linux_slice", {"lan": "tg-lan", "mgmt": "tg-mgmt"}))
    assert capture_points(run.scenario, run.topology, run.bridges) == [
        Point("lan-span", ("lan",), ("tg-lan",), (None,), False)
    ]


def test_two_teams_trunk_span_is_three_tagged_segments_in_order(tmp_path: Path) -> None:
    bridges = {"core": "tg-c", "eng": "tg-e", "sales": "tg-s", "mgmt": "tg-m"}
    run = load_run(_run(tmp_path, "two_teams", bridges))
    [point] = capture_points(run.scenario, run.topology, run.bridges)
    assert point == Point(
        "core-span", ("core", "eng", "sales"), ("tg-c", "tg-e", "tg-s"), (10, 20, 30), True
    )
    assert point.vlan_by_interface == {0: 10, 1: 20, 2: 30}


def test_a_segment_without_a_bridge_or_a_run_that_is_not_up_is_an_error(tmp_path: Path) -> None:
    run = load_run(_run(tmp_path, "two_teams", {"core": "tg-c", "mgmt": "tg-m"}))
    with pytest.raises(CaptureError, match="eng, sales"):
        capture_points(run.scenario, run.topology, run.bridges)
    (tmp_path / "two_teams" / "state.docker.json").unlink()
    with pytest.raises(CaptureError, match="is the run up"):
        load_run(tmp_path / "two_teams")
