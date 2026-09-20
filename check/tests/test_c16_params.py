from dataclasses import replace

import pytest
from support import IMPLS, RESOURCES, good, only, run, surf

from tiergen.core import dsl, ir


def _post(params: dict[str, ir.ParamValue]) -> ir.Scenario:
    """The baseline client posting a form, which takes a str and an int."""
    s = good(surf(action_map={"idle": None, "get": dsl.action("http.post_form", "web", params)}))
    binding = s.bindings[0]
    selection = ir.ImplSelection("http.post_form", {"http.cli": 1.0})
    return replace(s, bindings=(replace(binding, impls=(selection,)), s.bindings[1]))


PATH = "kinds[0].behaviours[0].action_map['get'].params"


@pytest.mark.parametrize(
    ("params", "path", "fragment"),
    [
        ({"path": "/f"}, PATH, "requires parameter 'body_bytes'"),
        (
            {"path": "/f", "body_bytes": 1, "colour": "red"},
            f"{PATH}['colour']",
            "no parameter 'colour'",
        ),
        ({"path": 7, "body_bytes": 1}, f"{PATH}['path']", "7 is not a str"),
        ({"path": "/f", "body_bytes": 1.5}, f"{PATH}['body_bytes']", "1.5 is not a int"),
        ({"path": "/f", "body_bytes": True}, f"{PATH}['body_bytes']", "True is not a int"),
        (
            {"path": dsl.choice(["/a", 3], [1, 1]), "body_bytes": 1},
            f"{PATH}['path']",
            "3 is not a str",
        ),
        ({"path": dsl.choice([], []), "body_bytes": 1}, f"{PATH}['path']", "at least one option"),
        (
            {"path": dsl.choice(["/a", "/b"], [1]), "body_bytes": 1},
            f"{PATH}['path']",
            "2 options but 1",
        ),
        ({"path": dsl.choice(["/a"], [0]), "body_bytes": 1}, f"{PATH}['path']", "must be positive"),
    ],
)
def test_ill_formed_parameters(params: dict[str, ir.ParamValue], path: str, fragment: str) -> None:
    assert "http.post_form" not in IMPLS["http.cli"].provides  # so filter, as in check 8's tests
    [d] = [d for d in run(_post(params)) if d.check == "C16"]
    assert d.path == path
    assert fragment in d.message


def test_literals_and_choices_of_the_right_type_pass() -> None:
    params: dict[str, ir.ParamValue] = {
        "path": dsl.choice(["/a", "/b"], [3, 1]),
        "body_bytes": dsl.choice([128, 4096], [0.9, 0.1]),
    }
    assert [d for d in run(_post(params)) if d.check == "C16"] == []


def test_an_optional_parameter_may_be_left_out_and_an_int_serves_as_a_float() -> None:
    actions = {"idle": None, "get": dsl.action("http.get", "web", {"path": "/"})}
    assert only("C16", good(surf(action_map=actions))) == []


def test_a_choice_in_a_resource_is_checked_like_an_inline_one() -> None:
    actions = {
        "idle": None,
        "get": dsl.action("http.get", "web", {"path": dsl.choice_from("cli.paths")}),
    }
    s = good(surf(action_map=actions))
    assert (
        only("C16", s, {**RESOURCES, "cli.paths": {"options": ["/", "/news"], "weights": [4, 1]}})
        == []
    )
    [d] = only("C16", s, {**RESOURCES, "cli.paths": {"options": ["/", 9], "weights": [4, 1]}})
    assert "9 is not a str" in d.message


def test_a_missing_choice_resource_is_check_5s_to_report() -> None:
    actions = {
        "idle": None,
        "get": dsl.action("http.get", "web", {"path": dsl.choice_from("cli.nowhere")}),
    }
    [d] = only("C05", good(surf(action_map=actions)))
    assert d.path == "kinds[0].behaviours[0].action_map['get'].params['path']"
