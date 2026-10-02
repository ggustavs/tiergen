"""What ``tiergen check`` finds in each example, against the installed descriptors."""

from dataclasses import replace
from pathlib import Path

from tiergen.check import Diagnostic, run_checks
from tiergen.core.groups import targets
from tiergen.core.loader import load_scenario
from tiergen.core.resources import DirResources
from tiergen.impls._base import load_impls
from tiergen.interfaces.registry import load_infra, load_sensors

EXAMPLES = Path(__file__).parent.parent


def _check(name: str) -> list[Diagnostic]:
    directory = EXAMPLES / name
    return run_checks(
        load_scenario(directory / "scenario.py"),
        DirResources(directory / "models"),
        load_impls(),
        load_sensors(),
        load_infra(),
    )


def _summary(found: list[Diagnostic]) -> list[tuple[str, str, str]]:
    return [(d.check, d.severity, d.path) for d in found]


def test_hq_lan_is_well_formed() -> None:
    assert _check("hq_lan") == []


def test_linux_slice_is_well_formed() -> None:
    assert _check("linux_slice") == []


def test_two_teams_is_well_formed_and_each_team_reaches_its_own_server() -> None:
    assert _check("two_teams") == []
    s = load_scenario(EXAMPLES / "two_teams" / "scenario.py")
    assert targets(s, "corp/eng", "workstation", "fs") == ["corp/eng/file_server[0]"]
    assert targets(s, "corp/sales", "workstation", "fs") == ["corp/sales/file_server[0]"]
    assert targets(s, "corp/eng", "workstation", "dc") == ["corp/domain_controller[0]"]
    victims = targets(s, "corp", "attacker", "victims")
    assert victims is not None
    assert len(victims) == 20
    assert victims[0] == "corp/eng/workstation[0]"
    assert victims[-1] == "corp/sales/workstation[7]"


def test_two_teams_broken_by_hand_fails_check_1_on_the_wire_not_at_run_time() -> None:
    s = load_scenario(EXAMPLES / "two_teams" / "scenario.py")
    corp, eng, sales = s.groups
    unwired = replace(eng, wiring={k: v for k, v in eng.wiring.items() if k != "workstation.dc"})
    crowded = replace(sales, instances={**sales.instances, "file_server": 2})
    broken = replace(s, groups=(corp, unwired, crowded))
    models = DirResources(EXAMPLES / "two_teams" / "models")
    found = [
        (d.path, d.message)
        for d in run_checks(broken, models, load_impls(), load_sensors(), load_infra())
        if d.check == "C01"
    ]
    assert [p for p, _ in found] == ["groups[1].wiring", "groups[2].wiring['workstation.fs']"]
    assert "workstation.dc is not wired" in found[0][1]
    assert "exactly one 'file_server'; 'corp/sales' hold 2" in found[1][1]


def test_hq_lan_capgap_warns_about_smb_dialect_and_nothing_else() -> None:
    found = _check("hq_lan_capgap")
    assert _summary(found) == [("C14", "warning", "sensors[1].capabilities")]
    assert all(word in found[0].message for word in ("SMB_DIALECT", "zeek", "suricata"))


def test_hq_lan_broken_fails_the_six_checks_it_was_broken_for() -> None:
    errors = [d for d in _summary(_check("hq_lan_broken")) if d[1] == "error"]
    assert errors == [
        ("C01", "error", "groups[0].wiring['workstation.dc']"),
        ("C01", "error", "groups[0].wiring['attacker.dc']"),
        ("C04", "error", "kinds[4].behaviours[0].process.transitions[0]"),
        ("C05", "error", "kinds[0].behaviours[0].process.rate"),
        ("C09", "error", "topology.capture_points[1].segments[0]"),
        ("C10", "error", "topology.segments"),
        ("C12", "error", "schedule[1].at_s"),
    ]
