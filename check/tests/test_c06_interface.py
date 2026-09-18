from dataclasses import replace

from support import RESOURCES, good, only, with_binding

from tiergen.core import dsl, ir
from tiergen.core.codec import JsonValue


def test_default_host_whose_services_do_not_cover_the_interface() -> None:
    s = with_binding(good(), 1, impls=(ir.ImplSelection("http.serve", {"http.srv80": 1.0}),))
    [d] = only("C06", s)
    assert d.path == "bindings[1]"
    assert "https on 443/tcp" in d.message


def test_every_weighted_alternative_has_to_serve_the_endpoint() -> None:
    mixed = ir.ImplSelection("http.serve", {"http.srv": 1.0, "http.srv80": 1.0})
    assert len(only("C06", with_binding(good(), 1, impls=(mixed,)))) == 1


def test_custom_host_is_judged_by_its_manifest() -> None:
    s = with_binding(
        good(), 1, host=dsl.host("linux", "vm", "template:web", manifest="srv.manifest"), impls=()
    )
    https: dict[str, JsonValue] = {"protocol": "https", "port": 443, "transport": "tcp"}
    assert only("C06", s, {**RESOURCES, "srv.manifest": [https]}) == []
    [d] = only("C06", s, {**RESOURCES, "srv.manifest": [{**https, "port": 8443}]})
    assert "manifest 'srv.manifest'" in d.message


def test_custom_host_without_a_manifest() -> None:
    [d] = only(
        "C06",
        with_binding(good(), 1, host=dsl.host("linux", "container", "image:nginx:1.27"), impls=()),
    )
    assert d.path == "bindings[1].host.manifest"


def test_host_ref_syntax() -> None:
    for ref in ("nginx", "image:", "vm:thing"):
        [d] = only("C06", with_binding(good(), 1, host=dsl.host("linux", "container", ref)))
        assert d.path == "bindings[1].host.ref"


def test_kinds_and_bindings_pair_up() -> None:
    s = good()
    [d] = only("C06", replace(s, bindings=s.bindings[:1]))
    assert (d.path, "no binding" in d.message) == ("kinds[1]", True)
    [d] = only("C06", replace(s, bindings=(*s.bindings, s.bindings[1])))
    assert "bound twice" in d.message
    [d] = only("C06", replace(s, bindings=(*s.bindings, replace(s.bindings[1], kind="ghost"))))
    assert d.path == "bindings[2].kind"


def test_a_kind_with_no_instances_needs_no_binding() -> None:
    s = good()
    s = replace(s, instances={"cli": 0, "srv": 0}, bindings=(), schedule=())
    assert only("C06", s) == []
