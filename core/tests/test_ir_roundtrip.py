"""Every IR type survives to_json, json text, and from_json unchanged."""

import json
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tiergen.core import ir
from tiergen.core.codec import from_json, to_json

names = st.text(st.characters(codec="ascii", categories=["Ll", "Nd"]), min_size=1, max_size=6)
floats = st.floats(allow_nan=False, allow_infinity=False, width=64)
weights = st.floats(min_value=0.0, max_value=1.0)


def tuples[T](items: st.SearchStrategy[T], max_size: int = 3) -> st.SearchStrategy[tuple[T, ...]]:
    return st.lists(items, max_size=max_size).map(tuple)


def or_resource[T](inline: st.SearchStrategy[T]) -> st.SearchStrategy[T | str]:
    return st.one_of(inline, names)


endpoints = st.builds(ir.Endpoint, names, st.integers(1, 65535), st.sampled_from(["tcp", "udp"]))
ties = st.builds(ir.Tie, names, names, st.sampled_from(["single", "optional", "multiple"]))
distributions = st.builds(ir.Distribution, names, or_resource(tuples(floats)))
semi_markovs = st.builds(
    ir.SemiMarkov,
    states=or_resource(tuples(names)),
    initial=or_resource(tuples(weights)),
    transitions=or_resource(tuples(tuples(weights))),
    dwell=or_resource(tuples(distributions)),
    rate=st.none() | names,
)
actions = st.builds(ir.Action, names, names)
behaviours = st.builds(
    ir.Behaviour,
    names,
    semi_markovs,
    or_resource(st.dictionaries(names, st.none() | actions, max_size=3)),
)
platforms = st.sampled_from(["linux", "windows"])
actor_kinds = st.builds(
    ir.ActorKind,
    names,
    tuples(endpoints),
    tuples(ties),
    tuples(behaviours, max_size=2),
    tuples(platforms, max_size=2),
)
hosts = st.builds(
    ir.Host, platforms, st.sampled_from(["container", "vm"]), names, st.none() | names
)
impl_selections = st.builds(
    ir.ImplSelection, names, or_resource(st.dictionaries(names, weights, max_size=3))
)
bindings = st.builds(ir.Binding, names, hosts, tuples(impl_selections))
schedule_events = st.builds(
    ir.ScheduleEvent,
    floats,
    names,
    st.sampled_from(["start", "stop", "set_rate", "run_sequence"]),
    st.none() | names | floats,
)
sensor_specs = st.builds(
    ir.SensorSpec,
    names,
    names,
    names,
    st.sampled_from(["offline", "live"]),
    tuples(names),
    st.sampled_from(["label", "fit", "both"]),
)
fit_provenances = st.builds(
    ir.FitProvenance, names, tuples(names), st.dictionaries(names, weights, max_size=3)
)
scenarios = st.builds(
    ir.Scenario,
    name=names,
    kinds=tuples(actor_kinds, max_size=2),
    instances=st.dictionaries(names, st.integers(0, 500), max_size=3),
    bindings=tuples(bindings, max_size=2),
    topology=names,
    egress=st.sampled_from(["stub", "allowlist", "none"]),
    egress_overrides=st.dictionaries(names, names, max_size=2),
    schedule=tuples(schedule_events),
    duration_s=floats,
    capture_points=tuples(names),
    sensors=tuples(sensor_specs, max_size=2),
    fit_provenance=st.none() | names | fit_provenances,
    seed=st.integers(),
    coverage_floor=weights,
)

CASES: list[tuple[type, st.SearchStrategy[Any]]] = [
    (ir.Endpoint, endpoints),
    (ir.Tie, ties),
    (ir.Distribution, distributions),
    (ir.SemiMarkov, semi_markovs),
    (ir.Action, actions),
    (ir.Behaviour, behaviours),
    (ir.ActorKind, actor_kinds),
    (ir.Host, hosts),
    (ir.ImplSelection, impl_selections),
    (ir.Binding, bindings),
    (ir.ScheduleEvent, schedule_events),
    (ir.SensorSpec, sensor_specs),
    (ir.FitProvenance, fit_provenances),
    (ir.Scenario, scenarios),
]


def test_every_ir_dataclass_has_a_case() -> None:
    declared = {
        obj for obj in vars(ir).values() if isinstance(obj, type) and obj.__module__ == ir.__name__
    }
    assert declared == {cls for cls, _ in CASES}


@pytest.mark.parametrize(("cls", "strategy"), CASES, ids=lambda case: getattr(case, "__name__", ""))
@given(data=st.data())
@settings(max_examples=50, deadline=None)
def test_round_trip(cls: type, strategy: st.SearchStrategy[Any], data: st.DataObject) -> None:
    value = data.draw(strategy)
    encoded = to_json(value)
    assert from_json(cls, encoded) == value
    assert from_json(cls, json.loads(json.dumps(encoded, allow_nan=False))) == value


@given(scenarios)
@settings(max_examples=25, deadline=None)
def test_scenario_methods_delegate_to_the_codec(scenario: ir.Scenario) -> None:
    assert ir.Scenario.from_json(scenario.to_json()) == scenario
