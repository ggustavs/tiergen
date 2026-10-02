from tiergen.core import ir
from tiergen.core.dsl import dist, semi_markov
from tiergen.core.resolve import Resolver
from tiergen.core.resources import DictResources
from tiergen.impls._base import ImplRef


def test_inline_values_pass_through_and_resources_decode() -> None:
    r = Resolver(DictResources({"m": [[0.5, 0.5], [1.0, 0.0]], "bad": [[1, "x"]]}))
    inline = semi_markov(
        "b",
        states=["a", "b"],
        initial=[1, 0],
        transitions=[[0, 1], [1, 0]],
        dwell=[dist("exponential", [1.0])],
        action_map={},
    )
    assert r.transitions(inline.process) == ((0, 1), (1, 0))
    named = semi_markov(
        "b", states=["a", "b"], initial=[1, 0], transitions="m", dwell="d", action_map={}
    )
    assert r.transitions(named.process) == ((0.5, 0.5), (1.0, 0.0))
    assert r.dwell(named.process) is None  # missing
    assert (
        r.transitions(
            semi_markov(
                "b", states=[], initial=[], transitions="bad", dwell=[], action_map={}
            ).process
        )
        is None
    )
    assert r.choice(ir.ChoiceRef("nowhere")) is None
    assert r.choice(ir.Choice(("x",), (1.0,))) == ir.Choice(("x",), (1.0,))


def test_refs_parse() -> None:
    assert ImplRef.parse("http.cli:a") == ImplRef("http.cli", "a")
    assert ImplRef.parse("http.cli") == ImplRef("http.cli", None)
    assert ir.HostRef.parse("default") == ir.HostRef("default", "")
    assert ir.HostRef.parse("image:nginx:1.27") == ir.HostRef("image", "nginx:1.27")
    assert ir.HostRef.parse("template:w") == ir.HostRef("template", "w")
    assert ir.HostRef.parse("image:") is None
    assert ir.HostRef.parse("vm:x") is None
