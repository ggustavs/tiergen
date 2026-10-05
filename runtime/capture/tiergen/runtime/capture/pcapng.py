"""pcapng, as much of it as the tool needs: sections, interfaces, packets, and tag insertion.

Reading follows the section header's byte order; writing is little-endian. Blocks the tool
does not interpret are copied through by ``insert_tags`` and skipped by ``packets``. The
format is the pcapng draft's: a block is type, length, body, length; options are code,
length, value, each padded to four bytes.
"""

import struct
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

SHB = 0x0A0D0D0A
IDB = 0x00000001
EPB = 0x00000006
MAGIC = 0x1A2B3C4D
OPT_END = 0
OPT_COMMENT = 1
IF_NAME = 2
IF_TSRESOL = 9
SHB_USERAPPL = 4
ETHERNET = 1
VLAN_ETHERTYPE = b"\x81\x00"


class PcapngError(ValueError):
    """The file is not pcapng the tool can read; the message says where it stopped."""


@dataclass(frozen=True, slots=True)
class Interface:
    """One capture interface of a section. ``tsresol`` is the power of ten of the
    timestamp unit, 6 for microseconds (dumpcap's default), 9 for nanoseconds."""

    name: str
    link_type: int = ETHERNET
    tsresol: int = 6


@dataclass(frozen=True, slots=True)
class Packet:
    """One captured packet: the interface it was seen on, by index over the whole file,
    its time in nanoseconds since the epoch, and its bytes. ``original_len`` is the length
    on the wire, which differs from ``len(data)`` only when the capture was truncated."""

    interface: int
    timestamp_ns: int
    data: bytes
    original_len: int | None = None

    @property
    def wire_len(self) -> int:
        return len(self.data) if self.original_len is None else self.original_len


def _pad(n: int) -> int:
    return (4 - n % 4) % 4


def _options(body: bytes, offset: int, endian: str) -> dict[int, bytes]:
    found: dict[int, bytes] = {}
    while offset + 4 <= len(body):
        code, length = struct.unpack_from(f"{endian}HH", body, offset)
        offset += 4
        if code == OPT_END:
            break
        found.setdefault(code, body[offset : offset + length])
        offset += length + _pad(length)
    return found


def _option(code: int, value: bytes) -> bytes:
    return struct.pack("<HH", code, len(value)) + value + b"\0" * _pad(len(value))


def _block(kind: int, body: bytes) -> bytes:
    total = 12 + len(body)
    return struct.pack("<II", kind, total) + body + struct.pack("<I", total)


def blocks(f: BinaryIO) -> Iterator[tuple[int, bytes, str]]:
    """Every block of a file as (type, body, endian), the endian being the section's."""
    endian = "<"
    while True:
        head = f.read(8)
        if not head:
            return
        if len(head) < 8:
            raise PcapngError("truncated block header")
        kind = struct.unpack("<I", head[:4])[0]
        if kind == SHB:
            magic = f.read(4)
            if len(magic) < 4:
                raise PcapngError("truncated section header")
            endian = "<" if struct.unpack("<I", magic)[0] == MAGIC else ">"
            if struct.unpack(f"{endian}I", magic)[0] != MAGIC:
                raise PcapngError("bad section header magic")
            total = int(struct.unpack(f"{endian}I", head[4:8])[0])
            rest = f.read(total - 12)
            body = magic + rest[:-4]
            short = len(rest) < total - 12
        else:
            total = int(struct.unpack(f"{endian}I", head[4:8])[0])
            rest = f.read(total - 8)
            body = rest[:-4]
            short = len(rest) < total - 8
        if short or struct.unpack(f"{endian}I", rest[-4:])[0] != total:
            raise PcapngError(f"block of type {kind:#x} is truncated or its lengths differ")
        yield kind, body, endian


def _interface(body: bytes, endian: str) -> Interface:
    link_type = struct.unpack_from(f"{endian}H", body, 0)[0]
    opts = _options(body, 8, endian)
    name = opts.get(IF_NAME, b"").decode("utf-8", "replace").rstrip("\0")
    tsresol = 6
    if IF_TSRESOL in opts:
        raw = opts[IF_TSRESOL][0]
        if raw & 0x80:
            raise PcapngError("timestamps in powers of two are not supported")
        tsresol = raw
    return Interface(name, link_type, tsresol)


def _packet(body: bytes, endian: str, base: int, interfaces: list[Interface]) -> Packet:
    index, high, low, caplen, origlen = (
        int(v) for v in struct.unpack_from(f"{endian}IIIII", body, 0)
    )
    interface = base + index
    if interface >= len(interfaces):
        raise PcapngError(f"packet on interface {index} before that interface's block")
    units = (high << 32) | low
    tsresol = interfaces[interface].tsresol
    ns = units * 10 ** (9 - tsresol) if tsresol <= 9 else units // 10 ** (tsresol - 9)
    data = body[20 : 20 + caplen]
    return Packet(interface, ns, data, None if origlen == caplen else origlen)


def packets(path: Path) -> Iterator[Interface | Packet]:
    """The interfaces and packets of a file in order; interface indexes count over the
    whole file, so a second section's first interface is not 0."""
    interfaces: list[Interface] = []
    base = 0
    with path.open("rb") as f:
        for kind, body, endian in blocks(f):
            if kind == SHB:
                base = len(interfaces)
            elif kind == IDB:
                interface = _interface(body, endian)
                interfaces.append(interface)
                yield interface
            elif kind == EPB:
                yield _packet(body, endian, base, interfaces)


def read(path: Path) -> tuple[list[Interface], list[Packet]]:
    found: list[Interface] = []
    seen: list[Packet] = []
    for item in packets(path):
        (found if isinstance(item, Interface) else seen).append(item)  # type: ignore[arg-type]
    return found, seen


class Writer:
    """One section, little-endian, written as it goes."""

    def __init__(self, f: BinaryIO, application: str = "tiergen") -> None:
        self._f = f
        self._interfaces: list[Interface] = []
        body = struct.pack("<IHHq", MAGIC, 1, 0, -1)
        body += _option(SHB_USERAPPL, application.encode()) + _option(OPT_END, b"")
        f.write(_block(SHB, body))

    def add_interface(self, interface: Interface) -> int:
        body = struct.pack("<HHI", interface.link_type, 0, 0)
        body += _option(IF_NAME, interface.name.encode())
        body += _option(IF_TSRESOL, bytes([interface.tsresol]))
        body += _option(OPT_END, b"")
        self._f.write(_block(IDB, body))
        self._interfaces.append(interface)
        return len(self._interfaces) - 1

    def write_packet(self, packet: Packet) -> None:
        tsresol = self._interfaces[packet.interface].tsresol
        units = (
            packet.timestamp_ns // 10 ** (9 - tsresol)
            if tsresol <= 9
            else packet.timestamp_ns * 10 ** (tsresol - 9)
        )
        head = struct.pack(
            "<IIIII",
            packet.interface,
            units >> 32,
            units & 0xFFFFFFFF,
            len(packet.data),
            packet.wire_len,
        )
        body = head + packet.data + b"\0" * _pad(len(packet.data)) + _option(OPT_END, b"")
        self._f.write(_block(EPB, body))


def write(path: Path, interfaces: list[Interface], items: list[Packet]) -> None:
    with path.open("wb") as f:
        writer = Writer(f)
        for interface in interfaces:
            writer.add_interface(interface)
        for packet in items:
            writer.write_packet(packet)


def tag(data: bytes, vlan: int) -> bytes:
    """``data`` with an 802.1Q header carrying ``vlan`` after the two MAC addresses."""
    return data[:12] + VLAN_ETHERTYPE + struct.pack(">H", vlan & 0x0FFF) + data[12:]


def insert_tags(src: Path, dst: Path, vlan_by_interface: Mapping[int, int]) -> int:
    """Copy ``src`` to ``dst``, tagging every Ethernet packet of the interfaces in
    ``vlan_by_interface`` with that interface's VLAN id; the count of packets tagged.
    Every other block is copied as it is, in the section's own byte order."""
    tagged = 0
    interfaces: list[Interface] = []
    base = 0
    with src.open("rb") as fin, dst.open("wb") as fout:
        for kind, body, endian in blocks(fin):
            if kind == SHB:
                base = len(interfaces)
            elif kind == IDB:
                interfaces.append(_interface(body, endian))
            elif kind == EPB:
                index = int(struct.unpack_from(f"{endian}I", body, 0)[0])
                interface = base + index
                vlan = vlan_by_interface.get(interface)
                if vlan is not None and interfaces[interface].link_type == ETHERNET:
                    caplen, origlen = (int(v) for v in struct.unpack_from(f"{endian}II", body, 12))
                    data = tag(body[20 : 20 + caplen], vlan)
                    trailer = body[20 + caplen + _pad(caplen) :]
                    body = (
                        body[:12]
                        + struct.pack(f"{endian}II", len(data), origlen + 4)
                        + data
                        + b"\0" * _pad(len(data))
                        + trailer
                    )
                    tagged += 1
            total = 12 + len(body)
            fout.write(struct.pack(f"{endian}II", kind, total))
            fout.write(body)
            fout.write(struct.pack(f"{endian}I", total))
    return tagged
