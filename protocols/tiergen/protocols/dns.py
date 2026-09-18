"""DNS."""

from tiergen.protocols.signature import Param, Signature, TrafficShape

SIGNATURES = (
    Signature(
        "dns.query",
        "dns",
        "client",
        ("dns",),
        (Param("name", "str"), Param("rtype", "str", required=False)),
        TrafficShape(1, "udp", None, (), "none"),
    ),
    Signature("dns.serve", "dns", "server", ("dns",), (), TrafficShape(0, "udp", None, (), "none")),
)
