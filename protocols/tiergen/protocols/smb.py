"""SMB file access."""

from tiergen.protocols.signature import Param, Signature, TrafficShape

# An SMB session in a domain is preceded by name resolution and a service ticket.
_BEFORE = ("dns.query", "kerberos.tgs")
_FILE = (Param("share", "str"), Param("path", "str"))


def _client(name: str, params: tuple[Param, ...]) -> Signature:
    return Signature(
        f"smb.{name}",
        "smb",
        "client",
        ("smb",),
        params,
        TrafficShape(1, "tcp", None, _BEFORE, "per_session"),
    )


SIGNATURES = (
    _client("read", _FILE),
    _client("write", (*_FILE, Param("size_bytes", "int"))),
    _client("list", _FILE),
    Signature("smb.serve", "smb", "server", ("smb",), (), TrafficShape(0, "tcp", None, (), "none")),
)
