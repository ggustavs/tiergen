"""Port scans. A scan needs a tie to aim at, but no endpoint served on the other side."""

from tiergen.protocols.signature import Param, Signature, TrafficShape

_PORTS = (Param("ports", "str"),)

SIGNATURES = (
    Signature(
        "scan.tcp_syn", "scan", "client", (), _PORTS, TrafficShape("many", "tcp", None, (), "none")
    ),
    Signature(
        "scan.tcp_connect",
        "scan",
        "client",
        (),
        _PORTS,
        TrafficShape("many", "tcp", None, (), "none"),
    ),
    Signature(
        "scan.udp", "scan", "client", (), _PORTS, TrafficShape("many", "udp", None, (), "none")
    ),
)
