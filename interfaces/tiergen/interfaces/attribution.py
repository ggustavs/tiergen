"""The attribution backend interface. No implementation lives in this package.

Attribution is kernel-level truth about which process opened which connection, and is
independent of any sensor. Each sensor's label step maps these records onto its own ids.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from tiergen.core.events import FiveTuple
from tiergen.core.ir import Platform
from tiergen.core.records import AttributionKey
from tiergen.interfaces.manifest import RunManifest, RunState


@dataclass(frozen=True, slots=True)
class AttributionRecord:
    """One observed connection and who owned it.

    ``instance`` is the id of the host it was seen on, ``path/kind[i]``, never a substrate
    name; the backend that observes it maps from its own names. ``principal`` is the
    execution context the observer saw, which the join matches to an
    ``InvocationRecord.principal``; ``tgid`` is the thread group the kernel saw, which is
    what a ``pid:<n>`` key matches, 0 where the observer has no process (a raw packet seen
    by a cgroup hook). ``start`` and ``end`` are seconds since the epoch on that host's
    clock; the record's ``ClockStamp`` moves them onto the capture host's. ``end`` equal to
    ``start`` means the observer saw the beginning and not the end.
    """

    instance: str
    principal: AttributionKey
    five_tuple: FiveTuple
    start: float
    end: float
    tgid: int = 0


@runtime_checkable
class AttributionBackend(Protocol):
    """Records connection ownership on the hosts of one platform, for a whole run.

    One backend instruments every host of its platform that a run has: for containers, one
    collector on the capture host sees them all; for guests, one agent per guest behind the
    same three calls. What it writes lives under ``run_dir/attrib/``.
    """

    @property
    def platform(self) -> Platform:
        """The guest platform this backend instruments."""
        ...

    def start(self, manifest: RunManifest, state: RunState, run_dir: Path) -> None:
        """Begin recording on the run's hosts. Called before capture starts."""
        ...

    def stop(self, run_dir: Path) -> None:
        """Stop recording and finish what was written."""
        ...

    def records(self, run_dir: Path) -> Iterator[AttributionRecord]:
        """What was recorded, as records. Traffic with no record stays unattributed."""
        ...
