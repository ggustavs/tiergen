"""HTTP and HTTPS."""

from tiergen.protocols.signature import Param, Signature, TrafficShape

_ENDPOINTS = ("http", "https")
_LOOKUPS = ("dns.query",)

SIGNATURES = (
    Signature(
        "http.get",
        "http",
        "client",
        _ENDPOINTS,
        (Param("path", "str"),),
        TrafficShape(1, "tcp", None, _LOOKUPS, "per_process"),
    ),
    Signature(
        "http.post_form",
        "http",
        "client",
        _ENDPOINTS,
        (Param("path", "str"), Param("body_bytes", "int")),
        TrafficShape(1, "tcp", None, _LOOKUPS, "per_process"),
    ),
    Signature(
        "http.browse",
        "http",
        "client",
        _ENDPOINTS,
        (Param("start_path", "str"), Param("max_pages", "int", required=False)),
        # A page load fetches subresources and follows redirects over several connections.
        TrafficShape("many", "tcp", None, _LOOKUPS, "per_session"),
    ),
    Signature(
        "http.serve", "http", "server", _ENDPOINTS, (), TrafficShape(0, "tcp", None, (), "none")
    ),
)
