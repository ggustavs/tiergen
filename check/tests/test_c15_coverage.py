from dataclasses import replace

from support import good, only

from tiergen.core import ir


def test_coverage_under_the_floor_warns() -> None:
    provenance = ir.FitProvenance("rich", ("APP_EVENTS",), {"APP_EVENTS": 0.49})
    [d] = only("C15", replace(good(), fit_provenance=provenance))
    assert d.severity == "warning"
    assert d.path == "fit_provenance.coverage['APP_EVENTS']"
    assert "49%" in d.message
    assert "50%" in d.message


def test_the_floor_is_the_scenarios_to_set() -> None:
    provenance = ir.FitProvenance("rich", ("APP_EVENTS",), {"APP_EVENTS": 0.49})
    assert only("C15", replace(good(), fit_provenance=provenance, coverage_floor=0.4)) == []
    assert len(only("C15", replace(good(), coverage_floor=0.95))) == 1


def test_a_used_capability_without_measured_coverage_warns() -> None:
    [d] = only("C15", replace(good(), fit_provenance=ir.FitProvenance("rich", ("APP_EVENTS",), {})))
    assert "no coverage" in d.message
