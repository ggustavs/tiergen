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
    group,
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
    lan = group("lan", instances={cli: 3, srv: 1}, attachments={cli: ["net"], srv: ["net"]})
    return scenario(
        "small",
        groups=[lan],
        bindings={
            srv: binding(
                host("linux", "container", backend="docker"), {"http.serve": {"http.nginx": 1}}
            ),
            cli: binding(
                host("windows", "vm", "template:w11", manifest=None, backend="libvirt"),
                {"http.get": resource("mix")},
            ),
        },
        topology=resource("small.topology"),
        egress="none",
        schedule=[
            at(hours(1), lan, "start", "surf", kind=cli),
            at(0, "lan/cli[2]", "stop", "surf"),
        ],
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
    [lan] = s.groups
    assert lan == ir.Group(
        "lan", None, {"cli": 3, "srv": 1}, {"cli": ("net",), "srv": ("net",)}, {"cli.web": ("lan",)}
    )
    assert s.kinds[0].ties == (ir.Tie("web", "srv", "multiple"),)
    assert [b.kind for b in s.bindings] == ["srv", "cli"]
    assert s.bindings[0].impls == (ir.ImplSelection("http.serve", {"http.nginx": 1}),)
    assert s.bindings[1].impls == (ir.ImplSelection("http.get", "mix"),)
    assert s.schedule == (
        ir.ScheduleEvent(3600.0, "lan/cli", "start", "surf"),
        ir.ScheduleEvent(0, "lan/cli[2]", "stop", "surf"),
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
            groups=[group("g", instances={a: 1, b: 1}, attachments={})],
            bindings={},
            topology="t",
            egress="none",
            duration_s=1,
            capture_points=[],
            sensors=[],
            seed=0,
        )


SCENARIO_PY = """
from tiergen.core.dsl import group, kind, scenario

K = kind("k", platforms=["linux"])
G = group("g", instances={K: 1}, attachments={})
S = scenario("from_py", groups=[G], bindings={}, topology="t", egress="none",
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
    'S = scenario("from_py", groups=[G], bindings={}, topology="t", egress="none",\n'
    "             duration_s=1, capture_points=[], sensors=[], seed=0)",
    'ARGS = dict(groups=[G], bindings={}, topology="t", egress="none",\n'
    "            duration_s=1, capture_points=[], sensors=[], seed=0)\n"
    'S = scenario("from_py", **ARGS)',
)


@pytest.mark.parametrize("body", ["x = 1\n", TWO_SCENARIOS])
def test_a_file_must_define_exactly_one_scenario(tmp_path: Path, body: str) -> None:
    py = tmp_path / "scenario.py"
    py.write_text(body)
    with pytest.raises(ScenarioLoadError):
        load_scenario(py)


def test_action_parameters_are_literals_or_choices() -> None:
    from tiergen.core.dsl import choice, choice_from

    act = action(
        "http.post_form",
        "web",
        {
            "path": choice(["/a", "/b"], [3, 1]),
            "body_bytes": 512,
            "token": choice_from("cli.tokens"),
        },
    )
    assert act.params == {
        "path": ir.Choice(("/a", "/b"), (3, 1)),
        "body_bytes": 512,
        "token": ir.ChoiceRef("cli.tokens"),
    }
    assert ir.Action("x", "y").params == {}
    assert from_json_action(act) == act


def from_json_action(act: ir.Action) -> ir.Action:
    from tiergen.core.codec import from_json, to_json

    return from_json(ir.Action, json.loads(json.dumps(to_json(act))))


def test_topology_builder_takes_handles_or_names() -> None:
    from tiergen.core.dsl import capture_point, network, topology

    lan = network("lan", "10.0.0.0/24")
    mgmt = network("mgmt", "10.9.0.0/24", "management")
    srv = kind("srv", platforms=["linux"])
    built = topology([lan, mgmt], [capture_point("span0", lan)], {"g/srv[0]": "10.0.0.10"})
    assert built == ir.Topology(
        (ir.Network("lan", "10.0.0.0/24", "data"), ir.Network("mgmt", "10.9.0.0/24", "management")),
        (ir.CapturePoint("span0", "lan"),),
        {"g/srv[0]": "10.0.0.10"},
    )
    assert topology([lan]).addresses == {}
    assert group("site", instances={srv: 1}, attachments={srv: [lan]}).ir.wiring == {}


def test_group_wiring_defaults_to_itself_only_when_it_holds_the_target() -> None:
    srv = kind("srv", platforms=["linux"])
    cli = kind(
        "cli", ties=[tie("web", srv, "multiple"), tie("dc", "dc", "single")], platforms=["linux"]
    )
    site = group("site", instances={srv: 1}, attachments={})
    team = group("team", instances={cli: 2}, attachments={}, parent=site, wiring={"cli.web": site})
    assert team.ir == ir.Group("team", "site", {"cli": 2}, {}, {"cli.web": ("site",)})
    both = group(
        "both", instances={cli: 2, srv: 1}, attachments={}, wiring={"cli.dc": [site, "site/team"]}
    )
    assert both.ir.wiring == {"cli.dc": ("site", "site/team"), "cli.web": ("both",)}


def test_at_builds_group_kind_and_instance_targets() -> None:
    k = kind("k", platforms=["linux"])
    g = group("g", instances={k: 1}, attachments={}, parent="corp")
    assert at(0, g, "start", "b").target == "corp/g"
    assert at(0, g, "start", "b", kind=k).target == "corp/g/k"
    assert at(0, g, "stop", "b", kind="k", index=0).target == "corp/g/k[0]"
