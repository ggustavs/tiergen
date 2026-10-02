from dataclasses import replace

from support import good, only, with_group, with_kind

from tiergen.core import ir


def test_single_tie_wired_to_a_group_holding_none_of_its_target() -> None:
    [d] = only("C01", with_group(good(), 0, instances={"cli": 3, "srv": 0}))
    assert (d.severity, d.path) == ("error", "groups[0].wiring['cli.web']")
    assert "exactly one 'srv'; 'lan' hold 0" in d.message


def test_single_tie_wired_to_groups_holding_two() -> None:
    [d] = only("C01", with_group(good(), 0, instances={"cli": 3, "srv": 2}))
    assert "'lan' hold 2" in d.message


def test_nothing_held_means_nothing_to_wire() -> None:
    s = with_group(good(), 0, instances={"cli": 0, "srv": 0}, wiring={})
    assert only("C01", replace(s, schedule=())) == []


def test_multiple_accepts_any_count_and_optional_at_most_one() -> None:
    s = with_kind(good(), 0, ties=(ir.Tie("web", "srv", "multiple"),))
    assert only("C01", with_group(s, 0, instances={"cli": 3, "srv": 0})) == []
    assert only("C01", with_group(s, 0, instances={"cli": 3, "srv": 5})) == []
    s = with_kind(good(), 0, ties=(ir.Tie("web", "srv", "optional"),))
    assert only("C01", with_group(s, 0, instances={"cli": 3, "srv": 0})) == []
    [d] = only("C01", with_group(s, 0, instances={"cli": 3, "srv": 2}))
    assert "at most one 'srv'; 'lan' hold 2" in d.message


def test_a_tie_left_unwired_is_an_error_not_a_lookup() -> None:
    [d] = only("C01", with_group(good(), 0, wiring={}))
    assert d.path == "groups[0].wiring"
    assert "cli.web is not wired" in d.message


def test_wiring_counts_across_the_named_groups() -> None:
    s = good()
    lan = s.groups[0]
    site = ir.Group("site", None, {"srv": 1}, {"srv": ("lan",)}, {})
    team = replace(
        lan, name="team", parent="site", instances={"cli": 2}, wiring={"cli.web": ("site",)}
    )
    assert only("C01", replace(s, groups=(site, team), schedule=())) == []
    both = replace(team, instances={"cli": 2, "srv": 1}, wiring={"cli.web": ("site", "site/team")})
    [d] = only("C01", replace(s, groups=(site, both), schedule=()))
    assert "'site', 'site/team' hold 2" in d.message


def test_wiring_to_a_group_that_does_not_exist_or_to_nothing() -> None:
    [d] = only("C01", with_group(good(), 0, wiring={"cli.web": ("mars",)}))
    assert "'mars' is not a group" in d.message
    [d] = only("C01", with_group(good(), 0, wiring={"cli.web": ()}))
    assert "wired to no group" in d.message


def test_wiring_keys_name_held_kinds_and_their_ties() -> None:
    s = with_group(
        good(), 0, wiring={"cli.web": ("lan",), "cli.nope": ("lan",), "srv.web": ("lan",)}
    )
    found = {d.path: d.message for d in only("C01", s)}
    assert "no tie 'nope'" in found["groups[0].wiring['cli.nope']"]
    assert "no tie 'web'" in found["groups[0].wiring['srv.web']"]


def test_unknown_tie_target() -> None:
    s = with_kind(
        good(), 0, ties=(ir.Tie("web", "srv", "single"), ir.Tie("dc", "ghost", "multiple"))
    )
    s = with_group(s, 0, wiring={"cli.web": ("lan",), "cli.dc": ("lan",)})
    [d] = only("C01", s)
    assert d.path == "kinds[0].ties[1].target_kind"


def test_instance_counts_name_kinds_and_are_not_negative() -> None:
    s = with_group(good(), 0, instances={"cli": 3, "ghost": 1, "srv": -1})
    found = {d.path for d in only("C01", replace(s, schedule=())) if "instances" in d.path}
    assert found == {"groups[0].instances['ghost']", "groups[0].instances['srv']"}
