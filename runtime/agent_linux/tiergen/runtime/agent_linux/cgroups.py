"""Attribution keys on Linux: a cgroup per invocation, or the process id when there cannot be one.

The behaviour process moves itself into ``/tiergen/<invocation>`` under the container's
cgroup root before it calls the implementation and back out after, so every socket the
invocation opens, and every child it spawns, carries that cgroup. That needs the cgroup
filesystem writable and the container's cgroup its own, which a container has under the
daemon's user-namespace remap with a private cgroup namespace (design decision 4.19).
Without that the key is the behaviour process's id, and ``agent.log`` says why.
"""

import contextlib
import logging
import os
from collections.abc import Generator
from pathlib import Path

from tiergen.core.records import AttributionKey

ROOT = Path("/sys/fs/cgroup")
SUBTREE = "tiergen"


class CgroupAttribution:
    """Each invocation in its own cgroup, named after it with ``/`` written as ``-`` and
    keyed by the cgroup's kernel id, the directory's inode number, which is what the eBPF
    programs report for every socket and packet. The name is the invocation id, so the key
    needs no path; the agent removes the directory right after, so nothing could resolve
    one later."""

    def __init__(self, root: Path) -> None:
        self.root = root

    @contextlib.contextmanager
    def enter(self, invocation: str) -> Generator[AttributionKey]:
        name = invocation.replace("/", "-")
        path = self.root / SUBTREE / name
        path.mkdir()
        pid = str(os.getpid())
        cgroup_id = path.stat().st_ino
        (path / "cgroup.procs").write_text(pid)
        try:
            yield AttributionKey("linux", f"cgroup:{cgroup_id}")
        finally:
            (self.root / "cgroup.procs").write_text(pid)
            # A child the implementation left running keeps the cgroup busy; it stays.
            with contextlib.suppress(OSError):
                path.rmdir()


class PidAttribution:
    """The behaviour process's id: one key for all its invocations, told apart by interval."""

    @contextlib.contextmanager
    def enter(self, invocation: str) -> Generator[AttributionKey]:
        yield AttributionKey("linux", f"pid:{os.getpid()}")


def _writable(root: Path) -> bool:
    try:
        (root / SUBTREE).mkdir(exist_ok=True)
    except OSError:
        return False
    return True


def choose(log: logging.Logger, root: Path = ROOT) -> CgroupAttribution | PidAttribution:
    """Cgroups if the cgroup filesystem is writable; else process ids."""
    if not (root / "cgroup.controllers").is_file():
        log.warning("%s is not a cgroup v2 hierarchy; attribution keys are process ids", root)
        return PidAttribution()
    if not _writable(root):
        log.warning(
            "%s is not writable (no user-namespace remap?); attribution keys are process ids",
            root,
        )
        return PidAttribution()
    log.info("attribution keys are cgroups under %s/%s", root, SUBTREE)
    return CgroupAttribution(root)
