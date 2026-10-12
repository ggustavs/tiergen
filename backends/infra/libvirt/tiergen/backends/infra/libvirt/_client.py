# pyright: basic
# The libvirt binding ships no type stubs; this is the one module that touches it, checked
# at basic strictness like the Docker facade.
"""The one module that touches libvirt and the QEMU guest agent.

``Client`` is what the backend needs of the hypervisor, as a Protocol, so the backend's
logic is tested against a fake and only this module is tested against libvirt. Everything
goes through the system connection, ``qemu:///system``: taps on the run's bridges need it,
and the user is in the ``libvirt`` group. Storage is a pool libvirt owns, so no file under
it needs the user's permissions; a guest is reached through its agent, so nothing in a
guest listens.
"""

import base64
import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from tiergen.interfaces.infra import BackendError

AGENT_TIMEOUT_S = 30
EXEC_POLL_S = 0.5


@dataclass(frozen=True, slots=True)
class Exec:
    """What a command run through the guest agent came back with."""

    exit_code: int
    out: str
    err: str


class Client(Protocol):
    """What the backend asks of libvirt. Names are the backend's, already prefixed."""

    def ensure_pool(self, name: str, path: str) -> None:
        """A directory pool at ``path``, defined, built and running."""
        ...

    def volumes(self, pool: str) -> list[str]: ...

    def volume_path(self, pool: str, name: str) -> str: ...

    def upload(self, pool: str, name: str, source: Path, fmt: str) -> None:
        """A new volume ``name`` of format ``fmt`` holding ``source``'s bytes."""
        ...

    def clone(self, pool: str, name: str, backing: str, capacity_gib: int) -> None:
        """A new qcow2 volume backed by ``backing`` (a volume of the pool)."""
        ...

    def delete_volume(self, pool: str, name: str) -> None: ...

    def bridge_exists(self, bridge: str) -> bool: ...

    def create_network(self, name: str, bridge: str) -> None:
        """A transient isolated network whose Linux bridge is called ``bridge``."""
        ...

    def networks(self) -> list[str]: ...

    def destroy_network(self, name: str) -> None: ...

    def ensure_network(self, name: str) -> None:
        """A defined network such as libvirt's ``default`` NAT, started if it is not."""
        ...

    def create_domain(self, xml: str) -> str:
        """A transient domain from ``xml``, started. Returns its UUID."""
        ...

    def domains(self) -> dict[str, str]:
        """Every domain's name to its description, running or not."""
        ...

    def destroy_domain(self, name: str) -> None: ...

    def agent_ready(self, domain: str, timeout_s: float) -> bool:
        """Whether the guest agent answers a ping within ``timeout_s``."""
        ...

    def guest_exec(
        self, domain: str, path: str, args: Sequence[str] = (), timeout_s: float = 300.0
    ) -> Exec:
        """Run ``path`` with ``args`` in the guest, wait for it, return what it said."""
        ...

    def guest_write(self, domain: str, path: str, data: bytes) -> None: ...

    def guest_read(self, domain: str, path: str) -> bytes: ...

    def guest_time(self, domain: str) -> float:
        """The guest's wall clock, seconds since the epoch, as the agent reports it."""
        ...

    def guest_interfaces(self, domain: str) -> dict[str, list[str]]:
        """MAC address to the IPv4 addresses the guest has on that interface."""
        ...


class LibvirtClient:
    """``Client`` over the system connection."""

    def __init__(self, uri: str = "qemu:///system") -> None:
        try:
            import libvirt_qemu

            import libvirt
        except ImportError as err:  # pragma: no cover - the marker keeps Windows out
            raise BackendError("libvirt-python is not installed") from err
        self._libvirt = libvirt
        self._qemu = libvirt_qemu
        try:
            self._conn = libvirt.open(uri)
        except libvirt.libvirtError as err:
            raise BackendError(f"cannot connect to libvirt at {uri}: {err}") from err

    # -- storage ---------------------------------------------------------------------------

    def ensure_pool(self, name: str, path: str) -> None:
        lv = self._libvirt
        try:
            pool = self._conn.storagePoolLookupByName(name)
        except lv.libvirtError:
            pool = self._conn.storagePoolDefineXML(
                f"<pool type='dir'><name>{name}</name><target><path>{path}</path></target></pool>"
            )
            pool.build(0)
            pool.setAutostart(1)
        if not pool.isActive():
            pool.create(0)
        pool.refresh(0)

    def _pool(self, name: str):
        try:
            return self._conn.storagePoolLookupByName(name)
        except self._libvirt.libvirtError as err:
            raise BackendError(f"storage pool {name!r} is missing: {err}") from err

    def volumes(self, pool: str) -> list[str]:
        p = self._pool(pool)
        p.refresh(0)
        return sorted(p.listVolumes())

    def volume_path(self, pool: str, name: str) -> str:
        try:
            return self._pool(pool).storageVolLookupByName(name).path()
        except self._libvirt.libvirtError as err:
            raise BackendError(f"volume {name!r} is missing from pool {pool!r}: {err}") from err

    def upload(self, pool: str, name: str, source: Path, fmt: str) -> None:
        size = source.stat().st_size
        xml = (
            f"<volume type='file'><name>{name}</name><capacity unit='bytes'>{size}</capacity>"
            f"<target><format type='{fmt}'/></target></volume>"
        )
        try:
            vol = self._pool(pool).createXML(xml, 0)
            stream = self._conn.newStream(0)
            with source.open("rb") as f:
                vol.upload(stream, 0, size, 0)
                stream.sendAll(lambda _s, nbytes, fh: fh.read(nbytes), f)
            stream.finish()
        except self._libvirt.libvirtError as err:
            raise BackendError(f"cannot upload {source} as {name!r}: {err}") from err

    def clone(self, pool: str, name: str, backing: str, capacity_gib: int) -> None:
        path = self.volume_path(pool, backing)
        xml = (
            f"<volume type='file'><name>{name}</name>"
            f"<capacity unit='GiB'>{capacity_gib}</capacity>"
            "<target><format type='qcow2'/></target>"
            f"<backingStore><path>{path}</path><format type='qcow2'/></backingStore></volume>"
        )
        try:
            self._pool(pool).createXML(xml, 0)
        except self._libvirt.libvirtError as err:
            raise BackendError(f"cannot clone {backing!r} as {name!r}: {err}") from err

    def create_volume(self, pool: str, name: str, capacity_gib: int) -> None:
        """An empty qcow2 volume. Only the template build needs it, to install onto."""
        xml = (
            f"<volume type='file'><name>{name}</name>"
            f"<capacity unit='GiB'>{capacity_gib}</capacity>"
            "<target><format type='qcow2'/></target></volume>"
        )
        try:
            self._pool(pool).createXML(xml, 0)
        except self._libvirt.libvirtError as err:
            raise BackendError(f"cannot create volume {name!r}: {err}") from err

    def delete_volume(self, pool: str, name: str) -> None:
        try:
            self._pool(pool).storageVolLookupByName(name).delete(0)
        except self._libvirt.libvirtError as err:
            raise BackendError(f"cannot delete volume {name!r}: {err}") from err

    # -- networks --------------------------------------------------------------------------

    def bridge_exists(self, bridge: str) -> bool:
        return Path("/sys/class/net", bridge, "bridge").is_dir()

    def create_network(self, name: str, bridge: str) -> None:
        xml = f"<network><name>{name}</name><bridge name='{bridge}' stp='off' delay='0'/></network>"
        try:
            self._conn.networkCreateXML(xml)
        except self._libvirt.libvirtError as err:
            raise BackendError(f"cannot create network {name!r} on {bridge}: {err}") from err

    def networks(self) -> list[str]:
        return sorted(n.name() for n in self._conn.listAllNetworks())

    def destroy_network(self, name: str) -> None:
        try:
            self._conn.networkLookupByName(name).destroy()
        except self._libvirt.libvirtError as err:
            raise BackendError(f"cannot destroy network {name!r}: {err}") from err

    def ensure_network(self, name: str) -> None:
        try:
            net = self._conn.networkLookupByName(name)
            if not net.isActive():
                net.create()
        except self._libvirt.libvirtError as err:
            raise BackendError(f"cannot start network {name!r}: {err}") from err

    # -- domains ---------------------------------------------------------------------------

    def create_domain(self, xml: str) -> str:
        try:
            return self._conn.createXML(xml, 0).UUIDString()
        except self._libvirt.libvirtError as err:
            raise BackendError(f"cannot start the domain: {err}") from err

    def domains(self) -> dict[str, str]:
        found: dict[str, str] = {}
        for d in self._conn.listAllDomains():
            try:
                found[d.name()] = d.metadata(
                    self._libvirt.VIR_DOMAIN_METADATA_DESCRIPTION,
                    None,  # pyright: ignore[reportArgumentType]
                )
            except self._libvirt.libvirtError:
                found[d.name()] = ""
        return found

    def _domain(self, name: str):
        try:
            return self._conn.lookupByName(name)
        except self._libvirt.libvirtError as err:
            raise BackendError(f"domain {name!r} is missing: {err}") from err

    def destroy_domain(self, name: str) -> None:
        try:
            self._domain(name).destroy()
        except self._libvirt.libvirtError as err:
            raise BackendError(f"cannot destroy domain {name!r}: {err}") from err

    def send_key(self, domain: str, keycode: int) -> None:
        """Press and release one key on the guest's keyboard (a Linux input keycode). Only
        the template build needs it, to pass an installer's boot prompt."""
        lv = self._libvirt
        try:
            self._domain(domain).sendKey(lv.VIR_KEYCODE_SET_LINUX, 50, [keycode], 1, 0)
        except lv.libvirtError as err:
            raise BackendError(f"{domain}: cannot send a key: {err}") from err

    # -- the guest agent -------------------------------------------------------------------

    def _agent(self, domain: str, command: Mapping[str, object], timeout_s: float) -> Any:
        """One guest agent command's ``return`` member; its shape is the command's."""
        dom = self._domain(domain)
        try:
            reply = self._qemu.qemuAgentCommand(dom, json.dumps(command), int(timeout_s), 0)
        except self._libvirt.libvirtError as err:
            raise BackendError(f"{domain}: guest agent {command['execute']} failed: {err}") from err
        return json.loads(reply).get("return")

    def agent_ready(self, domain: str, timeout_s: float) -> bool:
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            try:
                self._agent(domain, {"execute": "guest-ping"}, 5)
                return True
            except BackendError:
                time.sleep(1.0)
        return False

    def guest_exec(
        self, domain: str, path: str, args: Sequence[str] = (), timeout_s: float = 300.0
    ) -> Exec:
        started = self._agent(
            domain,
            {
                "execute": "guest-exec",
                "arguments": {"path": path, "arg": list(args), "capture-output": True},
            },
            AGENT_TIMEOUT_S,
        )
        pid = started["pid"]
        deadline = time.monotonic() + timeout_s
        while True:
            status = self._agent(
                domain,
                {"execute": "guest-exec-status", "arguments": {"pid": pid}},
                AGENT_TIMEOUT_S,
            )
            if status.get("exited"):
                out = base64.b64decode(status.get("out-data", "")).decode("utf-8", "replace")
                err = base64.b64decode(status.get("err-data", "")).decode("utf-8", "replace")
                return Exec(int(status.get("exitcode", -1)), out, err)
            if time.monotonic() > deadline:
                raise BackendError(f"{domain}: {path} did not finish within {timeout_s:g} s")
            time.sleep(EXEC_POLL_S)

    def guest_write(self, domain: str, path: str, data: bytes) -> None:
        handle = self._agent(
            domain,
            {"execute": "guest-file-open", "arguments": {"path": path, "mode": "w"}},
            AGENT_TIMEOUT_S,
        )
        try:
            for i in range(0, max(len(data), 1), 32768):
                chunk = base64.b64encode(data[i : i + 32768]).decode("ascii")
                self._agent(
                    domain,
                    {
                        "execute": "guest-file-write",
                        "arguments": {"handle": handle, "buf-b64": chunk},
                    },
                    AGENT_TIMEOUT_S,
                )
        finally:
            self._agent(
                domain,
                {"execute": "guest-file-close", "arguments": {"handle": handle}},
                AGENT_TIMEOUT_S,
            )

    def guest_read(self, domain: str, path: str) -> bytes:
        handle = self._agent(
            domain,
            {"execute": "guest-file-open", "arguments": {"path": path, "mode": "r"}},
            AGENT_TIMEOUT_S,
        )
        parts: list[bytes] = []
        try:
            while True:
                reply = self._agent(
                    domain,
                    {
                        "execute": "guest-file-read",
                        "arguments": {"handle": handle, "count": 1 << 20},
                    },
                    AGENT_TIMEOUT_S,
                )
                parts.append(base64.b64decode(reply.get("buf-b64", "")))
                if reply.get("eof") or reply.get("count", 0) == 0:
                    break
        finally:
            self._agent(
                domain,
                {"execute": "guest-file-close", "arguments": {"handle": handle}},
                AGENT_TIMEOUT_S,
            )
        return b"".join(parts)

    def guest_time(self, domain: str) -> float:
        ns = self._agent(domain, {"execute": "guest-get-time"}, AGENT_TIMEOUT_S)
        return int(ns) / 1e9

    def guest_interfaces(self, domain: str) -> dict[str, list[str]]:
        reply = self._agent(domain, {"execute": "guest-network-get-interfaces"}, AGENT_TIMEOUT_S)
        found: dict[str, list[str]] = {}
        for iface in reply or []:
            mac = str(iface.get("hardware-address", "")).lower()
            if not mac:
                continue
            found[mac] = [
                a["ip-address"]
                for a in iface.get("ip-addresses", [])
                if a.get("ip-address-type") == "ipv4"
            ]
        return found
