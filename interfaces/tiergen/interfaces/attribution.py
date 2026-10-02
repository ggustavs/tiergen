"""The attribution backend interface. No implementation lives in this package.

Attribution is kernel-level truth about which process opened which connection, and is
independent of any sensor. Each sensor's label step maps these records onto its own ids.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

from tiergen.core.events import FiveTuple
from tiergen.core.ir import Platform
from tiergen.core.records import AttributionKey


@dataclass(frozen=True, slots=True)
class AttributionRecord:
    """One observed connection and who owned it.

    ``instance`` is the id of the host it was seen on, ``path/kind[i]``, never a substrate
    name; the backend that observes it maps from its own names. ``principal`` is the
    execution context the observer saw, which the join matches to an
    ``InvocationRecord.principal``. ``start`` and ``end`` are seconds since the epoch on
    that host's clock; the record's ``ClockStamp`` moves them onto the capture host's.
    """

    instance: str
    principal: AttributionKey
    five_tuple: FiveTuple
    start: float
    end: float


class AttributionBackend(Protocol):
    """Records connection ownership on hosts of one platform."""

    @property
    def platform(self) -> Platform:
        """The guest platform this backend instruments."""
        ...

    def start(self, instance: str) -> None:
        """Begin recording on the host of ``instance``. Called before capture starts."""
        ...

    def stop(self, instance: str) -> None:
        """Stop recording on the host of ``instance``."""
        ...

    def collect(self, instance: str) -> Iterator[AttributionRecord]:
        """Yield what was recorded there. Traffic with no record stays unattributed."""
        ...
