"""Zeek's logs as records, in both formats a deployment writes.

The ASCII writer's tab-separated form carries its own schema in the header: ``#fields``
names the columns and ``#types`` says how to read each, with ``#unset_field`` for a value
that is absent and ``#empty_field`` for an empty set. The JSON form is one object per line
with the same names and values already typed. A reader must take whichever the
configuration produced, so this one looks at the first byte.
"""

import json
from collections.abc import Iterator
from pathlib import Path

from tiergen.core.codec import JsonValue


def _convert(value: str, kind: str, set_separator: str) -> JsonValue:
    if kind in ("time", "interval", "double"):
        return float(value)
    if kind in ("count", "int", "port"):
        return int(value)
    if kind == "bool":
        return value == "T"
    if kind.startswith(("set[", "vector[")):
        inner = kind[kind.index("[") + 1 : -1]
        return [_convert(v, inner, set_separator) for v in value.split(set_separator)]
    return value


def read_zeek_log(path: Path) -> Iterator[dict[str, JsonValue]]:
    """Every record of a Zeek log file, typed."""
    with path.open(encoding="utf-8") as f:
        first = f.read(1)
        f.seek(0)
        if first == "{":
            for line in f:
                if line.strip():
                    yield json.loads(line)
            return
        separator = "\t"
        set_separator = ","
        empty = "(empty)"
        unset = "-"
        fields: list[str] = []
        types: list[str] = []
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("#"):
                key, _, rest = line[1:].partition(
                    separator if separator != "\t" or "\t" in line else " "
                )
                if key == "separator":
                    separator = rest.encode().decode("unicode_escape")
                elif key == "set_separator":
                    set_separator = rest
                elif key == "empty_field":
                    empty = rest
                elif key == "unset_field":
                    unset = rest
                elif key == "fields":
                    fields = rest.split(separator)
                elif key == "types":
                    types = rest.split(separator)
                continue
            if not line:
                continue
            values = line.split(separator)
            record: dict[str, JsonValue] = {}
            for name, kind, value in zip(fields, types, values, strict=True):
                if value == unset:
                    record[name] = None
                elif value == empty:
                    record[name] = [] if kind.startswith(("set[", "vector[")) else ""
                else:
                    record[name] = _convert(value, kind, set_separator)
            yield record
