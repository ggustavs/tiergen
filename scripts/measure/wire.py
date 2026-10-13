"""What the capture says, read through tshark: SMB2 headers, Kerberos messages and DNS
queries, each with its frame's time and connection, so a measurement can join them to what
the hosts logged.

A Kerberos message's ``tickets`` are the encrypted parts of the tickets it carries. A
ticket is encrypted for the service and never altered by the client, so the ticket a KDC
reply hands out reappears byte for byte in each request that presents it: the next TGS-REQ
for a TGT, the AP-REQ inside an SMB session setup for a service ticket. Two messages sharing
one share a ticket.
"""

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

FIELDS = (
    "frame.number",
    "frame.time_epoch",
    "ip.src",
    "ip.dst",
    "tcp.srcport",
    "tcp.dstport",
    "udp.srcport",
    "udp.dstport",
    "tcp.stream",
    "udp.stream",
    "smb2.cmd",
    "smb2.msg_id",
    "smb2.sesid",
    "smb2.tid",
    "smb2.flags.response",
    "kerberos.msg_type",
    "kerberos.CNameString",
    "kerberos.SNameString",
    "kerberos.encryptedTicketData_cipher",
    "dns.id",
    "dns.qry.name",
    "dns.flags.response",
    "dns.a",
)

SMB2_COMMANDS = {
    0: "NEGOTIATE",
    1: "SESSION_SETUP",
    2: "LOGOFF",
    3: "TREE_CONNECT",
    4: "TREE_DISCONNECT",
    5: "CREATE",
    6: "CLOSE",
    7: "FLUSH",
    8: "READ",
    9: "WRITE",
    10: "LOCK",
    11: "IOCTL",
    12: "CANCEL",
    13: "ECHO",
    14: "QUERY_DIRECTORY",
    15: "CHANGE_NOTIFY",
    16: "QUERY_INFO",
    17: "SET_INFO",
    18: "OPLOCK_BREAK",
}
KRB_TYPES = {10: "AS-REQ", 11: "AS-REP", 12: "TGS-REQ", 13: "TGS-REP", 14: "AP-REQ", 15: "AP-REP"}


@dataclass(frozen=True)
class Frame:
    number: int
    time: float
    src: str
    sport: int
    dst: str
    dport: int
    stream: str
    """``tcp:<n>`` or ``udp:<n>``, tshark's own connection index."""


@dataclass(frozen=True)
class Smb2:
    frame: Frame
    command: int
    message_id: int
    session_id: int
    tree_id: int | None
    response: bool


@dataclass(frozen=True)
class Krb:
    frame: Frame
    msg_type: int
    cname: tuple[str, ...]
    sname: tuple[str, ...]
    tickets: frozenset[str]


@dataclass(frozen=True)
class Dns:
    frame: Frame
    id: int
    names: tuple[str, ...]
    response: bool
    answers: tuple[str, ...]


@dataclass(frozen=True)
class Wire:
    smb2: list[Smb2]
    krb: list[Krb]
    dns: list[Dns]


def _number(text: str) -> int:
    return int(text, 0) if text.startswith("0x") else int(text)


def _true(text: str) -> bool:
    return text in ("1", "True", "true")


def _first(layers: dict[str, list[str]], name: str, default: str = "0") -> str:
    return layers.get(name, [default])[0]


def read(pcap: Path) -> Wire:
    args = ["tshark", "-r", str(pcap), "-Y", "smb2 || kerberos || dns", "-T", "json"]
    for f in FIELDS:
        args += ["-e", f]
    out = subprocess.run(args, check=True, capture_output=True, text=True).stdout
    wire = Wire([], [], [])
    for packet in json.loads(out or "[]"):
        layers: dict[str, list[str]] = packet["_source"]["layers"]
        tcp = "tcp.stream" in layers
        frame = Frame(
            int(_first(layers, "frame.number")),
            float(_first(layers, "frame.time_epoch")),
            _first(layers, "ip.src", ""),
            int(_first(layers, "tcp.srcport" if tcp else "udp.srcport")),
            _first(layers, "ip.dst", ""),
            int(_first(layers, "tcp.dstport" if tcp else "udp.dstport")),
            f"tcp:{_first(layers, 'tcp.stream')}" if tcp else f"udp:{_first(layers, 'udp.stream')}",
        )
        commands = layers.get("smb2.cmd", [])
        ids = layers.get("smb2.msg_id", [])
        sessions = layers.get("smb2.sesid", [])
        trees = layers.get("smb2.tid", [])
        responses = layers.get("smb2.flags.response", [])
        if commands and len(commands) == len(ids) == len(sessions) == len(responses):
            # A compound frame lists each header's fields in order; an async header has no
            # tree id, so the trees line up only when every header has one.
            aligned = len(trees) == len(commands)
            for i, command in enumerate(commands):
                wire.smb2.append(
                    Smb2(
                        frame,
                        int(command),
                        _number(ids[i]),
                        _number(sessions[i]),
                        _number(trees[i]) if aligned else None,
                        _true(responses[i]),
                    )
                )
        if "kerberos.msg_type" in layers:
            wire.krb.append(
                Krb(
                    frame,
                    int(_first(layers, "kerberos.msg_type")),
                    tuple(layers.get("kerberos.CNameString", [])),
                    tuple(layers.get("kerberos.SNameString", [])),
                    frozenset(layers.get("kerberos.encryptedTicketData_cipher", [])),
                )
            )
        if "dns.id" in layers:
            wire.dns.append(
                Dns(
                    frame,
                    _number(_first(layers, "dns.id")),
                    tuple(layers.get("dns.qry.name", [])),
                    _true(_first(layers, "dns.flags.response", "0")),
                    tuple(layers.get("dns.a", [])),
                )
            )
    return wire
