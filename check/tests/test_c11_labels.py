from dataclasses import replace

from support import good, only, surf, with_binding, with_kind

from tiergen.core import ir


def test_duplicate_names_break_label_uniqueness() -> None:
    s = good()
    cli = s.kinds[0]
    [d] = only("C11", with_kind(s, 0, behaviours=(cli.behaviours[0], cli.behaviours[0])))
    assert d.path == "kinds[0].behaviours"
    [d] = only("C11", with_kind(s, 0, ties=(cli.ties[0], ir.Tie("web", "srv", "optional"))))
    assert d.path == "kinds[0].ties"


def test_duplicate_kind_names_can_arrive_through_json() -> None:
    s = good()
    found = [d for d in only("C11", replace(s, kinds=(*s.kinds, s.kinds[1]))) if d.path == "kinds"]
    assert len(found) == 1


def test_a_state_listed_twice() -> None:
    behaviour = surf(
        states=["idle", "idle"],
        action_map={"idle": None},
        transitions=[[0.5, 0.5], [0.5, 0.5]],
    )
    [d] = [d for d in only("C11", good(behaviour)) if d.severity == "error"]
    assert d.path == "kinds[0].behaviours[0].process.states"


def test_a_client_selection_nothing_invokes_is_a_warning() -> None:
    s = good(surf(action_map={"idle": None, "get": None}))
    [d] = only("C11", s)
    assert d.severity == "warning"
    assert d.path == "bindings[0].impls[0]"


def test_a_signature_selected_twice() -> None:
    s = good()
    selection = s.bindings[0].impls[0]
    [d] = only("C11", with_binding(s, 0, impls=(selection, selection)))
    assert d.path == "bindings[0].impls"
