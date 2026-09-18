"""Kerberos ticket requests."""

from tiergen.protocols.signature import Param, Signature, TrafficShape

SIGNATURES = (
    Signature(
        "kerberos.as",
        "kerberos",
        "client",
        ("kerberos",),
        (Param("principal", "str"),),
        TrafficShape(1, "tcp", None, ("dns.query",), "none"),
    ),
    Signature(
        "kerberos.tgs",
        "kerberos",
        "client",
        ("kerberos",),
        (Param("spn", "str"),),
        TrafficShape(1, "tcp", None, ("dns.query",), "none"),
    ),
    Signature(
        "kerberos.serve",
        "kerberos",
        "server",
        ("kerberos",),
        (),
        TrafficShape(0, "tcp", None, (), "none"),
    ),
)
