"""SSH."""

from tiergen.protocols.signature import Param, Signature, TrafficShape

SIGNATURES = (
    Signature(
        "ssh.session",
        "ssh",
        "client",
        ("ssh",),
        (Param("command", "str", required=False),),
        TrafficShape(1, "tcp", None, ("dns.query",), "none"),
    ),
    Signature("ssh.serve", "ssh", "server", ("ssh",), (), TrafficShape(0, "tcp", None, (), "none")),
)
