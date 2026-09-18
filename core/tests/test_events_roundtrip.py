import json
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tiergen.core.codec import CodecError, JsonValue, from_json, to_json
from tiergen.core.events import AppEvent, ConnEvent, FiveTuple, SensorFlowId
from tiergen.core.labels import Label

names = st.text(st.characters(codec="ascii", categories=["Ll", "Nd"]), min_size=1, max_size=6)
finite = st.floats(allow_nan=False, allow_infinity=False)
counts = st.none() | st.integers(0, 2**40)
json_values: st.SearchStrategy[JsonValue] = st.recursive(
    st.none() | st.booleans() | st.integers() | finite | names,
    lambda inner: st.lists(inner, max_size=3) | st.dictionaries(names, inner, max_size=3),
    max_leaves=8,
)
records = st.dictionaries(names, json_values, max_size=3)

flow_ids = st.builds(SensorFlowId, names, names)
five_tuples = st.builds(
    FiveTuple, names, st.integers(0, 65535), names, st.integers(0, 65535), names
)
conn_events = st.builds(
    ConnEvent,
    flow=flow_ids,
    five_tuple=five_tuples,
    start=finite,
    duration=st.none() | finite,
    orig_bytes=counts,
    resp_bytes=counts,
    orig_pkts=counts,
    resp_pkts=counts,
    state=st.sampled_from(["attempted", "established", "closed", "reset", "rejected", "other"]),
    raw=records,
)
app_events = st.builds(AppEvent, flow_ids, st.integers(0, 10_000), finite, names, records, records)
labels = st.builds(
    Label,
    names,
    names,
    names,
    names,
    names,
    names,
    st.none() | names,
    names,
    st.sampled_from(["succeeded", "failed"]),
)

CASES: list[tuple[type, st.SearchStrategy[Any]]] = [
    (SensorFlowId, flow_ids),
    (FiveTuple, five_tuples),
    (ConnEvent, conn_events),
    (AppEvent, app_events),
    (Label, labels),
]


@pytest.mark.parametrize(("cls", "strategy"), CASES, ids=lambda case: getattr(case, "__name__", ""))
@given(data=st.data())
@settings(max_examples=50, deadline=None)
def test_round_trip(cls: type, strategy: st.SearchStrategy[Any], data: st.DataObject) -> None:
    value = data.draw(strategy)
    encoded = to_json(value)
    assert from_json(cls, encoded) == value
    assert from_json(cls, json.loads(json.dumps(encoded, allow_nan=False))) == value


def test_passthrough_still_refuses_non_finite_floats() -> None:
    event = to_json(AppEvent(SensorFlowId("zeek", "C1"), 0, 0.0, "http", {}, {}))
    assert isinstance(event, dict)
    event["raw"] = {"rtt": [1.0, float("inf")]}
    with pytest.raises(CodecError) as info:
        from_json(AppEvent, event)
    assert info.value.path == "raw['rtt'][1]"
