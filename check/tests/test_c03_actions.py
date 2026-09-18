from support import good, only, surf

from tiergen.core import dsl


def test_a_state_without_an_entry() -> None:
    [d] = only("C03", good(surf(action_map={"get": dsl.action("http.get", "web")})))
    assert d.path == "kinds[0].behaviours[0].action_map"
    assert "'idle'" in d.message


def test_an_entry_for_something_that_is_not_a_state() -> None:
    actions = {"idle": None, "get": dsl.action("http.get", "web"), "nap": None}
    [d] = only("C03", good(surf(action_map=actions)))
    assert d.path == "kinds[0].behaviours[0].action_map['nap']"


def test_unknown_signature() -> None:
    [d] = only(
        "C03", good(surf(action_map={"idle": None, "get": dsl.action("http.teleport", "web")}))
    )
    assert d.path == "kinds[0].behaviours[0].action_map['get'].signature"


def test_a_server_signature_is_not_an_action() -> None:
    [d] = only("C03", good(surf(action_map={"idle": None, "get": dsl.action("http.serve", "web")})))
    assert "server signature" in d.message
