"""Loading a scenario from a file: ``scenario.py`` written with the builders, or IR as JSON."""

import json
import runpy
from pathlib import Path

from tiergen.core.ir import Scenario


class ScenarioLoadError(ValueError):
    """The file does not yield exactly one scenario."""


def load_scenario(path: Path) -> Scenario:
    """Load ``path``.

    A ``.json`` file is decoded as IR. Any other file is run as Python, and must leave
    exactly one ``Scenario`` among its module-level names. Running a scenario file executes
    the engineer's own code; it is never done with files from elsewhere.
    """
    if path.suffix == ".json":
        return Scenario.from_json(json.loads(path.read_text(encoding="utf-8")))
    found = {id(v): v for v in runpy.run_path(str(path)).values() if isinstance(v, Scenario)}
    if len(found) != 1:
        raise ScenarioLoadError(f"{path}: expected one module-level Scenario, found {len(found)}")
    return next(iter(found.values()))
