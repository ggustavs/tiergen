"""A generic JSON codec for frozen dataclasses, driven by their type annotations.

Supported annotations: ``None``, ``bool``, ``int``, ``float``, ``str``, ``Literal[...]``,
``tuple[T, ...]``, fixed-length ``tuple[A, B]``, ``dict[str, T]``, dataclasses, and unions
of these. A union is decoded by JSON shape (null, bool, number, string, array, object):
the first arm that accepts the value's shape is used, so the arms of a union should have
distinct shapes.

Decoding is strict. An unknown key, a missing field without a default, a value of the
wrong shape and a non-finite float all raise ``CodecError`` carrying the path of the
offending value, for example ``kinds[2].behaviours[0].process.dwell[1].family``.
"""

import dataclasses
import math
import types
from collections.abc import Mapping, Sequence
from functools import cache
from typing import Any, Literal, Union, cast, get_args, get_origin, get_type_hints

type JsonValue = bool | int | float | str | list[JsonValue] | dict[str, JsonValue] | None


class CodecError(ValueError):
    """A value could not be encoded or decoded. ``path`` locates it; empty means the root."""

    def __init__(self, path: str, message: str) -> None:
        super().__init__(f"{path or '<root>'}: {message}")
        self.path = path
        self.message = message


def to_json(obj: object) -> JsonValue:
    """Encode a dataclass instance, or any value built from the supported types, as JSON."""
    return _encode(obj, "")


def from_json[T](cls: type[T], data: JsonValue) -> T:
    """Decode ``data`` as an instance of the dataclass ``cls``."""
    return cast(T, _decode(cls, data, ""))


def _field(path: str, name: str) -> str:
    return f"{path}.{name}" if path else name


def _encode(obj: object, path: str) -> JsonValue:
    if obj is None or isinstance(obj, (bool, int, str)):
        return obj
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise CodecError(path, f"non-finite float {obj!r} has no JSON form")
        return obj
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {
            f.name: _encode(getattr(obj, f.name), _field(path, f.name))
            for f in dataclasses.fields(obj)
        }
    if isinstance(obj, (tuple, list)):
        items = cast(Sequence[object], obj)
        return [_encode(item, f"{path}[{i}]") for i, item in enumerate(items)]
    if isinstance(obj, Mapping):
        out: dict[str, JsonValue] = {}
        for key, value in cast(Mapping[object, object], obj).items():
            if not isinstance(key, str):
                raise CodecError(path, f"mapping key {key!r} is not a string")
            out[key] = _encode(value, f"{path}[{key!r}]")
        return out
    raise CodecError(path, f"{type(obj).__name__} has no JSON form")


def _shape(data: JsonValue) -> str:
    if data is None:
        return "null"
    if isinstance(data, bool):
        return "bool"
    if isinstance(data, (int, float)):
        return "number"
    if isinstance(data, str):
        return "string"
    if isinstance(data, list):
        return "array"
    return "object"


def _is_union(tp: Any) -> bool:
    origin = get_origin(tp)
    return origin is Union or origin is types.UnionType


def _shapes(tp: Any) -> frozenset[str]:
    """The JSON shapes a value of type ``tp`` can take."""
    if tp is None or tp is type(None):
        return frozenset({"null"})
    if tp is bool:
        return frozenset({"bool"})
    if tp is int or tp is float:
        return frozenset({"number"})
    if tp is str:
        return frozenset({"string"})
    if _is_union(tp):
        return frozenset(shape for arm in get_args(tp) for shape in _shapes(arm))
    origin = get_origin(tp)
    if origin is Literal:
        return frozenset(_shape(cast(JsonValue, value)) for value in get_args(tp))
    if origin is tuple:
        return frozenset({"array"})
    if origin is dict or dataclasses.is_dataclass(tp):
        return frozenset({"object"})
    raise TypeError(f"unsupported annotation {tp!r}")


def _describe(tp: Any) -> str:
    return getattr(tp, "__name__", None) or repr(tp)


@cache
def _hints(cls: type) -> dict[str, Any]:
    return get_type_hints(cls)


def _decode(tp: Any, data: JsonValue, path: str) -> Any:
    shape = _shape(data)
    if shape not in _shapes(tp):
        expected = " or ".join(sorted(_shapes(tp)))
        raise CodecError(path, f"expected {expected} for {_describe(tp)}, got {shape}")

    if _is_union(tp):
        arm = next(arm for arm in get_args(tp) if shape in _shapes(arm))
        return _decode(arm, data, path)
    if tp is None or tp is type(None) or tp is bool or tp is str:
        return data
    if tp is int:
        if isinstance(data, float):
            raise CodecError(path, f"expected an integer, got {data!r}")
        return data
    if tp is float:
        value = float(cast(float, data))
        if not math.isfinite(value):
            raise CodecError(path, f"non-finite float {value!r}")
        return value

    origin = get_origin(tp)
    if origin is Literal:
        allowed = get_args(tp)
        # bool is an int: compare types as well, so True does not pass for Literal[1].
        if not any(data == value and type(data) is type(value) for value in allowed):
            options = ", ".join(repr(value) for value in allowed)
            raise CodecError(path, f"expected one of {options}, got {data!r}")
        return data
    if origin is tuple:
        items = cast(list[JsonValue], data)
        args = get_args(tp)
        if len(args) == 2 and args[1] is Ellipsis:
            return tuple(_decode(args[0], item, f"{path}[{i}]") for i, item in enumerate(items))
        if len(items) != len(args):
            raise CodecError(path, f"expected {len(args)} items, got {len(items)}")
        return tuple(
            _decode(arg, item, f"{path}[{i}]")
            for i, (arg, item) in enumerate(zip(args, items, strict=True))
        )
    if origin is dict:
        _, value_type = get_args(tp)
        entries = cast(dict[str, JsonValue], data)
        return {
            key: _decode(value_type, value, f"{path}[{key!r}]") for key, value in entries.items()
        }

    return _decode_dataclass(tp, cast(dict[str, JsonValue], data), path)


def _decode_dataclass(cls: type, data: dict[str, JsonValue], path: str) -> Any:
    hints = _hints(cls)
    fields = dataclasses.fields(cls)
    unknown = sorted(set(data) - {f.name for f in fields})
    if unknown:
        raise CodecError(path, f"unknown field(s) for {cls.__name__}: {', '.join(unknown)}")
    kwargs: dict[str, Any] = {}
    for f in fields:
        if f.name in data:
            kwargs[f.name] = _decode(hints[f.name], data[f.name], _field(path, f.name))
        elif f.default is dataclasses.MISSING and f.default_factory is dataclasses.MISSING:
            raise CodecError(path, f"missing field {f.name!r} of {cls.__name__}")
    return cls(**kwargs)
