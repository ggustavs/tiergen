from dataclasses import replace
from itertools import product

from hypothesis import given, settings
from hypothesis import strategies as st
from support import good, only, with_kind

from tiergen.check._solver import unsatisfiable
from tiergen.core import ir


def test_single_tie_to_a_kind_with_no_instances() -> None:
    s = replace(good(), instances={"cli": 3, "srv": 0})
    [d] = only("C01", s)
    assert d.severity == "error"
    assert d.path == "kinds[0].ties[0]"
    assert "no 'srv'" in d.message


def test_single_tie_is_fine_when_the_source_has_no_instances_either() -> None:
    s = replace(good(), instances={"cli": 0, "srv": 0}, schedule=())
    assert only("C01", s) == []


def test_multiple_and_optional_ties_accept_zero_targets() -> None:
    for multiplicity in ("multiple", "optional"):
        s = with_kind(good(), 0, ties=(ir.Tie("web", "srv", multiplicity),))
        assert only("C01", replace(s, instances={"cli": 3, "srv": 0})) == []


def test_unknown_tie_target() -> None:
    s = with_kind(
        good(), 0, ties=(ir.Tie("web", "srv", "single"), ir.Tie("dc", "ghost", "multiple"))
    )
    [d] = only("C01", s)
    assert d.path == "kinds[0].ties[1].target_kind"


def test_instance_counts_must_cover_exactly_the_kinds() -> None:
    s = replace(good(), instances={"cli": 3, "ghost": 1, "srv": -1}, schedule=())
    found = {(d.path, d.severity) for d in only("C01", s)}
    assert found == {("instances['ghost']", "error"), ("instances['srv']", "error")}
    [d] = only("C01", replace(good(), instances={"srv": 1}, schedule=()))
    assert d.path == "instances"
    assert "'cli'" in d.message


KINDS = ["a", "b", "c"]
PAIRS = [(x, y) for x, y in product(KINDS, KINDS) if x != y]


@given(
    counts=st.fixed_dictionaries({k: st.integers(0, 3) for k in KINDS}),
    needs=st.lists(st.sampled_from(PAIRS), max_size=5),
)
@settings(max_examples=60, deadline=None)
def test_solver_agrees_with_arithmetic(
    counts: dict[str, int], needs: list[tuple[str, str]]
) -> None:
    expected = [i for i, (src, tgt) in enumerate(needs) if counts[src] > 0 and counts[tgt] < 1]
    assert unsatisfiable(counts, needs) == expected
