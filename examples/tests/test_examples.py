import json
from pathlib import Path

import pytest

from tiergen.core.ir import Scenario
from tiergen.core.loader import load_scenario
from tiergen.core.resources import DirResources

EXAMPLES = Path(__file__).parent.parent
NAMES = ["hq_lan", "hq_lan_capgap", "hq_lan_broken"]


@pytest.mark.parametrize("name", NAMES)
def test_example_builds_and_round_trips(name: str) -> None:
    scenario = load_scenario(EXAMPLES / name / "scenario.py")
    assert scenario.name == name
    assert Scenario.from_json(json.loads(json.dumps(scenario.to_json()))) == scenario


def test_the_well_formed_example_has_every_resource_it_names() -> None:
    scenario = load_scenario(EXAMPLES / "hq_lan" / "scenario.py")
    models = DirResources(EXAMPLES / "hq_lan" / "models")
    office = scenario.kinds[0].behaviours[0]
    assert scenario.kinds[0].name == "workstation"
    named = [
        office.process.states,
        office.process.initial,
        office.process.transitions,
        office.process.dwell,
        office.process.rate,
        office.action_map,
        scenario.topology,
        scenario.fit_provenance,
        *(s.config for s in scenario.sensors),
    ]
    assert all(isinstance(n, str) and models.exists(n) for n in named)
