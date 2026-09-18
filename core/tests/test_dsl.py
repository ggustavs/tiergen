import json
from pathlib import Path

import pytest

from tiergen.core import ir
from tiergen.core.dsl import (
    action,
    at,
    binding,
    dist,
    endpoint,
    host,
    hours,
    kind,
    resource,
    scenario,
    semi_markov,
    sensor,
    tie,
)
from tiergen.core.loader import ScenarioLoadError, load_scenario


def _small() -> ir.Scenario:
    srv = kind("srv", serves=[endpoint("http", 80, "tcp")], platforms=["linux"])
    cli = kind(
        "cli",
        ties=[tie("web", srv, "multiple")],
        behaviours=[
            semi_markov(
                "surf",
                states=["idle", "get"],
                initial=[1, 0],
                transitions=[[0, 1], [1, 0]],
                dwell=[dist("exponential", [30]), dist("exponential", resource("cli.get_dwell"))],
                action_map={"idle": None, "get": action("http.get", "web")},
            )
        ],
        platforms=["linux", "windows"],
    )
    return scenario(
        "small",
        instances={cli: 3, srv: 1},
        bindings={
            srv: binding(host("linux", "container"), {"http.serve": {"http.nginx": 1}}),
            cli: binding(
                host("windows", "vm", "template:w11", manifest=None), {"http.get": resource("mix")}
            ),
        },
        topology=resource("small.topology"),
        egress="none",
        schedule=[at(hours(1), cli, "start", "surf"), at(0, "cli[2]", "stop", "surf")],
        duration_s=hours(2),
        capture_points=["span0"],
        sensors=[
            sensor(
                "zeek", "7.0", resource("small.zeek"), "offline", caps=["APP_EVENTS"], role="both"
            )
        ],
        seed=7,
    )


def test_builders_produce_ir_with_names_in_place_of_handles() -> None:
    s = _small()
    assert [k.name for k in s.kinds] == ["cli", "srv"]
    assert s.instances == {"cli": 3, "srv": 1}
    assert s.kinds[0].ties == (ir.Tie("web", "srv", "multiple"),)
    assert [b.kind for b in s.bindings] == ["srv", "cli"]
    assert s.bindings[0].impls == (ir.ImplSelection("http.serve", {"http.nginx": 1}),)
    assert s.bindings[1].impls == (ir.ImplSelection("http.get", "mix"),)
    assert s.schedule == (
        ir.ScheduleEvent(3600.0, "cli", "start", "surf"),
        ir.ScheduleEvent(0, "cli[2]", "stop", "surf"),
    )
    process = s.kinds[0].behaviours[0].process
    assert process.transitions == ((0, 1), (1, 0))
    assert process.dwell == (
        ir.Distribution("exponential", (30,)),
        ir.Distribution("exponential", "cli.get_dwell"),
    )
    assert s.coverage_floor == 0.5
    assert s.fit_provenance is None


def test_built_scenario_round_trips() -> None:
    s = _small()
    assert ir.Scenario.from_json(json.loads(json.dumps(s.to_json()))) == s


def test_two_kinds_with_one_name_are_refused() -> None:
    a = kind("same", platforms=["linux"])
    b = kind("same", platforms=["windows"])
    with pytest.raises(ValueError, match="same"):
        scenario(
            "dup",
            instances={a: 1, b: 1},
            bindings={},
            topology="t",
            egress="none",
            duration_s=1,
            capture_points=[],
            sensors=[],
            seed=0,
        )


SCENARIO_PY = """
from tiergen.core.dsl import kind, scenario

K = kind("k", platforms=["linux"])
S = scenario("from_py", instances={K: 1}, bindings={}, topology="t", egress="none",
             duration_s=1, capture_points=[], sensors=[], seed=0)
ALIAS = S
"""


def test_load_from_python_and_from_json(tmp_path: Path) -> None:
    py = tmp_path / "scenario.py"
    py.write_text(SCENARIO_PY)
    loaded = load_scenario(py)
    assert loaded.name == "from_py"

    js = tmp_path / "scenario.json"
    js.write_text(json.dumps(loaded.to_json()))
    assert load_scenario(js) == loaded


TWO_SCENARIOS = SCENARIO_PY.replace("ALIAS = S", 'T = scenario("second", **ARGS)').replace(
    'S = scenario("from_py", instances={K: 1}, bindings={}, topology="t", egress="none",\n'
    "             duration_s=1, capture_points=[], sensors=[], seed=0)",
    'ARGS = dict(instances={K: 1}, bindings={}, topology="t", egress="none",\n'
    "            duration_s=1, capture_points=[], sensors=[], seed=0)\n"
    'S = scenario("from_py", **ARGS)',
)


@pytest.mark.parametrize("body", ["x = 1\n", TWO_SCENARIOS])
def test_a_file_must_define_exactly_one_scenario(tmp_path: Path, body: str) -> None:
    py = tmp_path / "scenario.py"
    py.write_text(body)
    with pytest.raises(ScenarioLoadError):
        load_scenario(py)
