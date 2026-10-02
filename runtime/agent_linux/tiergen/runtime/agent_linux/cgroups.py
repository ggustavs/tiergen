"""Attribution keys on Linux: a cgroup per invocation, or the process id when there cannot be one.

The behaviour process moves itself into ``/tiergen/<invocation>`` under the container's
cgroup root before it calls the implementation and back out after, so every socket the
invocation opens, and every child it spawns, carries that cgroup. That needs the cgroup
filesystem writable, which a container gets from a private cgroup namespace plus the
``SYS_ADMIN`` capability to remount it; both were tried against the daemon. Without them
the key is the behaviour process's id, and ``agent.log`` says why.
"""

import contextlib
import logging
import os
import subprocess
from collections.abc import Generator
from pathlib import Path

from tiergen.core.records import AttributionKey

ROOT = Path("/sys/fs/cgroup")
SUBTREE = "tiergen"


class CgroupAttribution:
    """Each invocation in its own cgroup, named after it with ``/`` written as ``-``."""

    def __init__(self, root: Path) -> None:
        self.root = root

    @contextlib.contextmanager
    def enter(self, invocation: str) -> Generator[AttributionKey]:
        name = invocation.replace("/", "-")
        path = self.root / SUBTREE / name
        path.mkdir()
        pid = str(os.getpid())
        (path / "cgroup.procs").write_text(pid)
        try:
            yield AttributionKey("linux", f"cgroup:/{SUBTREE}/{name}")
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
    """Cgroups if the cgroup filesystem is, or can be remounted, writable; else process ids."""
    if not (root / "cgroup.controllers").is_file():
        log.warning("%s is not a cgroup v2 hierarchy; attribution keys are process ids", root)
        return PidAttribution()
    if not _writable(root):
        remount = subprocess.run(
            ["mount", "-o", "remount,rw", str(root)], capture_output=True, text=True, check=False
        )
        if remount.returncode != 0 or not _writable(root):
            log.warning(
                "%s is read-only and cannot be remounted (%s); attribution keys are process ids",
                root,
                remount.stderr.strip() or "needs SYS_ADMIN",
            )
            return PidAttribution()
    log.info("attribution keys are cgroups under %s/%s", root, SUBTREE)
    return CgroupAttribution(root)
