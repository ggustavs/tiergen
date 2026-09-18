from support import good, only, surf, with_binding

from tiergen.core import dsl, ir


def test_binding_platform_the_kind_does_not_allow() -> None:
    [d] = only("C07", with_binding(good(), 1, host=dsl.host("windows", "container")))[:1]
    assert d.path == "bindings[1].host.platform"
    assert "allows linux, not windows" in d.message


def test_implementation_that_does_not_run_on_the_bound_platform() -> None:
    found = only("C07", with_binding(good(), 1, host=dsl.host("windows", "container")))
    assert [d.path for d in found][1:] == ["bindings[1].impls[0].choices['http.srv']"]
    assert "does not run on windows" in found[1].message


def test_host_capabilities_are_reported_as_not_computed_never_as_a_pass() -> None:
    s = good(surf(action_map={"idle": None, "get": dsl.action("scan.tcp_syn", "web")}))
    s = with_binding(
        s,
        0,
        host=dsl.host("linux", "container"),
        impls=(ir.ImplSelection("scan.tcp_syn", {"scan.raw": 1.0}),),
    )
    [d] = only("C07", s)
    assert d.severity == "not_computed"
    assert "net_raw" in d.message
    assert "linux container" in d.message
