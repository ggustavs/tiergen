from dataclasses import replace

import pytest
from support import good, only, run

from tiergen.core import ir


def _first(**changes: object) -> ir.Scenario:
    s = good()
    return replace(s, sensors=(replace(s.sensors[0], **changes), s.sensors[1]))  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize(
    ("changes", "path", "fragment"),
    [
        ({"impl": "snort"}, "sensors[0].impl", "not installed"),
        ({"version": "9.9"}, "sensors[0].version", "known versions: 1.0"),
        (
            {"capabilities": ("APP_EVENTS", "TELEPATHY")},
            "sensors[0].capabilities[1]",
            "not a capability",
        ),
    ],
)
def test_ill_formed_sensor(changes: dict[str, object], path: str, fragment: str) -> None:
    # Renaming the fit sensor also trips check 14; this test is about check 13 alone.
    [d] = [d for d in run(_first(**changes)) if d.check == "C13" and d.path == path]
    assert fragment in d.message


def test_capability_and_mode_the_implementation_cannot_offer() -> None:
    s = good()
    poor = replace(s.sensors[1], capabilities=("APP_EVENTS", "TLS_JA4"), mode="live")
    found = {d.path: d.message for d in only("C13", replace(s, sensors=(s.sensors[0], poor)))}
    assert found == {
        "sensors[1].mode": "poor does not support live mode",
        "sensors[1].capabilities[1]": "poor cannot declare TLS_JA4",
    }


def test_at_least_one_sensor() -> None:
    [d] = only("C13", replace(good(), sensors=(), fit_provenance=None))
    assert d.path == "sensors"
