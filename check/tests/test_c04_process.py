import math

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from support import RESOURCES, good, only, surf


@pytest.mark.parametrize(
    ("changes", "path", "fragment"),
    [
        ({"transitions": [[0.5, 0.4], [1.0, 0.0]]}, "transitions[0]", "sums to 0.9"),
        ({"transitions": [[1.5, -0.5], [1.0, 0.0]]}, "transitions[0]", "negative"),
        ({"transitions": [[0.5, 0.5]]}, "transitions", "not 2 by 2"),
        ({"initial": [0.5, 0.4]}, "initial", "sums to 0.9"),
        ({"initial": [1.0]}, "initial", "1 entries for 2 states"),
        ({"transitions": [[1.0, 0.0], [1.0, 0.0]]}, "states[1]", "'get' is unreachable"),
        ({"dwell": []}, "dwell", "0 distributions for 2 states"),
    ],
)
def test_ill_formed_process(changes: dict[str, object], path: str, fragment: str) -> None:
    [d] = only("C04", good(surf(**changes)))
    assert d.path == f"kinds[0].behaviours[0].process.{path}"
    assert fragment in d.message


def test_rate_curve_has_24_or_168_entries() -> None:
    [d] = only("C04", good(), {**RESOURCES, "cli.rate": [1.0 for _ in range(25)]})
    assert "25 entries" in d.message
    assert only("C04", good(), {**RESOURCES, "cli.rate": [1.0 for _ in range(168)]}) == []
    assert only("C04", good(surf(rate=None))) == []


def test_a_resource_matrix_is_checked_like_an_inline_one() -> None:
    [d] = only("C04", good(), {**RESOURCES, "cli.transitions": [[0.5, 0.5], [0.7, 0.2]]})
    assert d.path == "kinds[0].behaviours[0].process.transitions[1]"


weights = st.floats(min_value=0.0, max_value=1.0)


@given(st.lists(st.lists(weights, min_size=3, max_size=3), min_size=3, max_size=3))
@settings(max_examples=100, deadline=None)
def test_row_errors_are_reported_exactly_for_rows_that_do_not_sum_to_one(
    matrix: list[list[float]],
) -> None:
    behaviour = surf(
        states=["a", "b", "c"],
        initial=[1 / 3, 1 / 3, 1 / 3],
        transitions=matrix,
        dwell=[],
        rate=None,
        action_map={"a": None, "b": None, "c": None},
    )
    found = {
        d.path.rsplit(".", 1)[1] for d in only("C04", good(behaviour)) if "transitions[" in d.path
    }
    bad = {f"transitions[{i}]" for i, row in enumerate(matrix) if abs(math.fsum(row) - 1) > 1e-9}
    assert found == bad
