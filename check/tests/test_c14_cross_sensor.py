from dataclasses import replace

from support import RESOURCES, good, only

from tiergen.core import ir
from tiergen.core.codec import JsonValue


def _used(*caps: str) -> ir.FitProvenance:
    return ir.FitProvenance("rich", caps, dict.fromkeys(caps, 0.9))


def test_capability_gap_is_a_warning_naming_all_three_parties() -> None:
    [d] = only("C14", replace(good(), fit_provenance=_used("APP_EVENTS", "SMB_DIALECT")))
    assert d.severity == "warning"
    assert d.path == "sensors[1].capabilities"
    assert all(word in d.message for word in ("SMB_DIALECT", "rich", "poor"))


def test_the_gap_is_found_through_a_provenance_resource_too() -> None:
    provenance: JsonValue = {
        "sensor": "rich",
        "capabilities_used": ["SMB_DIALECT"],
        "coverage": {"SMB_DIALECT": 0.9},
    }
    [d] = only("C14", good(), {**RESOURCES, "lan.provenance": provenance})
    assert d.severity == "warning"


def test_a_fit_only_sensor_is_not_a_label_sensor() -> None:
    s = good()
    rich, poor = s.sensors
    s = replace(
        s,
        sensors=(replace(rich, role="fit", capabilities=()), poor),
        fit_provenance=_used("APP_EVENTS"),
    )
    assert only("C14", s) == []


def test_exactly_one_fit_sensor() -> None:
    s = good()
    rich, poor = s.sensors
    [none] = only("C14", replace(s, sensors=(replace(rich, role="label"), poor)))
    assert (none.severity, none.path) == ("error", "sensors")
    [two] = only("C14", replace(s, sensors=(rich, replace(poor, role="both"))))
    assert "2 do" in two.message


def test_fit_sensor_must_be_the_one_the_model_was_fitted_from() -> None:
    [d] = only("C14", replace(good(), fit_provenance=ir.FitProvenance("poor", (), {})))
    assert (d.severity, d.path) == ("error", "sensors[0].role")


def test_an_unfitted_scenario_has_nothing_to_compare() -> None:
    s = good()
    sensors = tuple(replace(sensor, role="label") for sensor in s.sensors)
    assert only("C14", replace(s, sensors=sensors, fit_provenance=None)) == []
