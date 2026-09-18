"""The attribution backend interface. No implementation lives in this package.

Attribution is kernel-level truth about which process opened which connection, and is
independent of any sensor. Each sensor's label step maps these records onto its own ids.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from tiergen.core.events import FiveTuple
from tiergen.core.ir import Platform


@dataclass(frozen=True, slots=True)
class AttributionRecord:
    """One observed connection and who owned it.

    ``principal`` identifies the invocation's execution context on ``host``: a cgroup path
    on Linux, a job object or PID on Windows. ``start`` and ``end`` are seconds since the
    epoch on the host's clock; per-host offsets are applied at the join, not here.
    """

    host: str
    principal: str
    five_tuple: FiveTuple
    start: float
    end: float


class AttributionBackend(Protocol):
    """Records connection ownership on hosts of one platform."""

    @property
    def platform(self) -> Platform:
        """The guest platform this backend instruments."""
        ...

    def start(self, host: str) -> None:
        """Begin recording on ``host``. Called before capture starts."""
        ...

    def stop(self, host: str) -> None:
        """Stop recording on ``host``."""
        ...

    def collect(self, host: str) -> Iterator[AttributionRecord]:
        """Yield what was recorded on ``host``. Traffic with no record stays unattributed."""
        ...
