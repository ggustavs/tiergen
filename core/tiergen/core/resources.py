"""Resources: named values a scenario refers to instead of carrying inline.

Fitted parameters are resources. A scenario never defaults a missing one; the checker
reports it. Most resources are JSON. Some, such as a sensor's configuration, are opaque:
the checker can only ask whether they exist.
"""

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from tiergen.core.codec import JsonValue

_NAME = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*")


class Resources(Protocol):
    """A store of resources by name."""

    def exists(self, name: str) -> bool:
        """True if ``name`` is a resource of either sort, JSON or opaque."""
        ...

    def get(self, name: str) -> JsonValue:
        """The value of a JSON resource. Raises ``KeyError`` if there is none by that name."""
        ...


class DictResources:
    """Resources held in memory. For tests and for scenarios built in code."""

    def __init__(
        self, values: Mapping[str, JsonValue], opaque: frozenset[str] = frozenset()
    ) -> None:
        self._values = dict(values)
        self._opaque = opaque

    def exists(self, name: str) -> bool:
        return name in self._values or name in self._opaque

    def get(self, name: str) -> JsonValue:
        return self._values[name]


class DirResources:
    """Resources in one directory, the ``models/`` that ``fit`` writes.

    The JSON resource ``a.b`` is the file ``a.b.json``. An opaque resource ``a.b`` is the
    file or directory ``a.b``. A name that could leave the directory is not a resource.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    def exists(self, name: str) -> bool:
        if not _NAME.fullmatch(name):
            return False
        return (self._root / f"{name}.json").is_file() or (self._root / name).exists()

    def get(self, name: str) -> JsonValue:
        path = self._root / f"{name}.json"
        if not _NAME.fullmatch(name) or not path.is_file():
            raise KeyError(name)
        return json.loads(path.read_text(encoding="utf-8"))
