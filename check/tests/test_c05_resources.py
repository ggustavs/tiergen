from dataclasses import replace

from support import RESOURCES, good, only, surf

from tiergen.core import dsl


def test_missing_resource() -> None:
    [d] = only("C05", good(surf(rate="cli.rate_missing")))
    assert d.path == "kinds[0].behaviours[0].process.rate"
    assert "does not exist" in d.message


def test_wrong_shape_carries_the_codec_path() -> None:
    [d] = only("C05", good(), {**RESOURCES, "cli.transitions": [[0.5, "half"], [1.0, 0.0]]})
    assert d.path == "kinds[0].behaviours[0].process.transitions"
    assert "[0][1]" in d.message


def test_opaque_resource_where_json_is_needed() -> None:
    [d] = only("C05", good(surf(rate="lan.rich")))
    assert "is not JSON" in d.message


def test_opaque_references_only_need_to_exist() -> None:
    [d] = only("C05", replace(good(), topology="lan.nowhere"))
    assert d.path == "topology"
    s = good()
    [d] = only("C05", replace(s, sensors=(replace(s.sensors[0], config="lan.nocfg"), s.sensors[1])))
    assert d.path == "sensors[0].config"


def test_distribution_parameters_are_references_too() -> None:
    dwell = [dsl.dist("exponential", "cli.idle_dwell"), dsl.dist("exponential", [2.0])]
    [d] = only("C05", good(surf(dwell=dwell)))
    assert d.path == "kinds[0].behaviours[0].process.dwell[0].params"
    assert only("C05", good(surf(dwell=dwell)), {**RESOURCES, "cli.idle_dwell": [30.0]}) == []


def test_every_reference_kind_is_followed() -> None:
    s = good(surf(states="r.states", initial="r.initial", dwell="r.dwell", action_map="r.actions"))
    s = replace(
        s,
        bindings=(
            replace(s.bindings[0], impls=(replace(s.bindings[0].impls[0], choices="r.mix"),)),
            replace(
                s.bindings[1], host=dsl.host("linux", "vm", "template:t", manifest="r.manifest")
            ),
        ),
    )
    paths = {d.path for d in only("C05", s)}
    assert paths == {
        "kinds[0].behaviours[0].process.states",
        "kinds[0].behaviours[0].process.initial",
        "kinds[0].behaviours[0].process.dwell",
        "kinds[0].behaviours[0].action_map",
        "bindings[0].impls[0].choices",
        "bindings[1].host.manifest",
    }
