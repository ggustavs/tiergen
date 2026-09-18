from dataclasses import dataclass
from typing import Literal

import pytest

from tiergen.core.codec import CodecError, JsonValue, from_json, to_json


@dataclass(frozen=True, slots=True)
class Leaf:
    tag: Literal["a", "b"]
    weight: float


@dataclass(frozen=True, slots=True)
class Node:
    name: str
    leaves: tuple[Leaf, ...]
    pair: tuple[int, str]
    table: dict[str, Leaf | None] | str
    note: str | None = None


NODE = Node("n", (Leaf("a", 1.5), Leaf("b", 2.0)), (3, "x"), {"k": Leaf("a", 0.0), "silent": None})
NODE_JSON: JsonValue = {
    "name": "n",
    "leaves": [{"tag": "a", "weight": 1.5}, {"tag": "b", "weight": 2.0}],
    "pair": [3, "x"],
    "table": {"k": {"tag": "a", "weight": 0.0}, "silent": None},
    "note": None,
}


def test_encode() -> None:
    assert to_json(NODE) == NODE_JSON


def test_decode() -> None:
    assert from_json(Node, NODE_JSON) == NODE


def test_union_is_decoded_by_shape() -> None:
    assert from_json(Node, {**_obj(NODE_JSON), "table": "res.name"}).table == "res.name"


def test_default_fills_a_missing_field() -> None:
    data = _obj(NODE_JSON)
    del data["note"]
    assert from_json(Node, data) == NODE


def test_int_is_accepted_for_float_and_becomes_float() -> None:
    leaf = from_json(Leaf, {"tag": "a", "weight": 2})
    assert leaf.weight == 2.0
    assert isinstance(leaf.weight, float)


def _obj(data: JsonValue) -> dict[str, JsonValue]:
    assert isinstance(data, dict)
    return dict(data)


@pytest.mark.parametrize(
    ("patch", "path", "fragment"),
    [
        ({"name": 1}, "name", "expected string"),
        (
            {"leaves": [{"tag": "a", "weight": 1.0}, {"tag": "c", "weight": 1.0}]},
            "leaves[1].tag",
            "one of",
        ),
        ({"leaves": [{"tag": "a"}]}, "leaves[0]", "missing field 'weight'"),
        ({"leaves": [{"tag": "a", "weight": 1.0, "extra": 0}]}, "leaves[0]", "unknown field"),
        ({"pair": [3]}, "pair", "expected 2 items"),
        ({"pair": [3.5, "x"]}, "pair[0]", "expected an integer"),
        ({"pair": [True, "x"]}, "pair[0]", "got bool"),
        ({"table": {"k": 4}}, "table['k']", "got number"),
        ({"table": []}, "table", "got array"),
    ],
)
def test_decode_errors_carry_the_path(
    patch: dict[str, JsonValue], path: str, fragment: str
) -> None:
    with pytest.raises(CodecError) as info:
        from_json(Node, {**_obj(NODE_JSON), **patch})
    assert info.value.path == path
    assert fragment in info.value.message


def test_decode_error_at_the_root() -> None:
    with pytest.raises(CodecError, match="<root>") as info:
        from_json(Node, [])
    assert info.value.path == ""


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_floats_are_rejected(bad: float) -> None:
    with pytest.raises(CodecError) as info:
        to_json(Leaf("a", bad))
    assert info.value.path == "weight"


def test_non_string_mapping_key_is_rejected() -> None:
    with pytest.raises(CodecError, match="not a string"):
        to_json({1: "x"})
