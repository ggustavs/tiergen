"""Shared by attribution backends: what a collector emits, and how it becomes records.

A collector is a process that prints one event per line; everything above that line is
here and in Python, whatever toolchain sits below it.
"""

from tiergen.backends.attrib._base.events import Event, EventKind, read_events
from tiergen.backends.attrib._base.join import Joined, join
from tiergen.interfaces import RunManifest

BY_INFRA: dict[tuple[str, str], str] = {
    ("docker", "linux"): "linux_ebpf",
    ("libvirt", "linux"): "linux_ebpf_guest",
}
"""Which attribution backend instruments the hosts of which infrastructure backend, per
guest platform. A container's kernel is the capture host's, so eBPF on the host there; a
Linux guest runs the same collector inside, through the guest agent; a Windows guest will
bring its own."""


def backends_for(manifest: RunManifest) -> dict[str, set[str]]:
    """The attribution backends a manifest's hosts need, each with the platforms it covers
    there; a platform no backend covers is absent, and its traffic stays unattributed."""
    found: dict[str, set[str]] = {}
    for host in manifest.hosts:
        name = BY_INFRA.get((manifest.backend, host.platform))
        if name is not None:
            found.setdefault(name, set()).add(host.platform)
    return found


def uncovered(manifest: RunManifest) -> set[str]:
    """The platforms of a manifest's hosts that no attribution backend covers."""
    return {h.platform for h in manifest.hosts if (manifest.backend, h.platform) not in BY_INFRA}


__all__ = [
    "BY_INFRA",
    "Event",
    "EventKind",
    "Joined",
    "backends_for",
    "join",
    "read_events",
    "uncovered",
]
