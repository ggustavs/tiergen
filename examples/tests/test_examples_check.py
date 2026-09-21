"""What ``tiergen check`` finds in each example, against the installed descriptors."""

from pathlib import Path

from tiergen.check import Diagnostic, run_checks
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


def test_hq_lan_capgap_warns_about_smb_dialect_and_nothing_else() -> None:
    found = _check("hq_lan_capgap")
    assert _summary(found) == [("C14", "warning", "sensors[1].capabilities")]
    assert all(word in found[0].message for word in ("SMB_DIALECT", "zeek", "suricata"))


def test_hq_lan_broken_fails_the_six_checks_it_was_broken_for() -> None:
    errors = [d for d in _summary(_check("hq_lan_broken")) if d[1] == "error"]
    assert errors == [
        ("C01", "error", "kinds[0].ties[0]"),
        ("C01", "error", "kinds[4].ties[0]"),
        ("C04", "error", "kinds[4].behaviours[0].process.transitions[0]"),
        ("C05", "error", "kinds[0].behaviours[0].process.rate"),
        ("C09", "error", "topology.capture_points[1].network"),
        ("C10", "error", "topology.networks"),
        ("C12", "error", "schedule[1].at_s"),
    ]
