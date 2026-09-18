from support import RESOURCES, good, only, surf, with_binding, with_kind

from tiergen.core import dsl, ir
from tiergen.core.codec import JsonValue, to_json


def _serving(*endpoints: ir.Endpoint) -> tuple[ir.Scenario, dict[str, JsonValue]]:
    """The server kind serving ``endpoints`` from a custom host whose manifest agrees, so
    that only check 2 has anything to object to."""
    s = with_kind(good(), 1, serves=endpoints)
    s = with_binding(
        s, 1, host=dsl.host("linux", "vm", "template:t", manifest="srv.manifest"), impls=()
    )
    return s, {**RESOURCES, "srv.manifest": to_json(endpoints)}


def test_action_over_a_tie_the_kind_does_not_have() -> None:
    actions = {"idle": None, "get": dsl.action("http.get", "intranet")}
    [d] = only("C02", good(surf(action_map=actions)))
    assert d.path == "kinds[0].behaviours[0].action_map['get'].tie"


def test_target_does_not_serve_a_compatible_endpoint() -> None:
    [d] = only("C02", *_serving(ir.Endpoint("smb", 445, "tcp")))
    assert d.path == "kinds[0].behaviours[0].action_map['get']"
    assert "http or https on tcp" in d.message


def test_transport_has_to_match_as_well() -> None:
    assert len(only("C02", *_serving(ir.Endpoint("https", 443, "udp")))) == 1


def test_http_get_fits_an_https_endpoint() -> None:
    assert only("C02", *_serving(ir.Endpoint("https", 8443, "tcp"))) == []


def test_a_scan_needs_a_tie_but_no_served_endpoint() -> None:
    s, resources = _serving()
    cli = s.kinds[0]
    scan = surf(action_map={"idle": None, "get": dsl.action("scan.tcp_syn", "web")})
    s = with_kind(s, 0, behaviours=(scan,), ties=cli.ties)
    s = with_binding(
        s,
        0,
        host=dsl.host("linux", "container"),
        impls=(ir.ImplSelection("scan.tcp_syn", {"scan.raw": 1.0}),),
    )
    assert only("C02", s, resources) == []
