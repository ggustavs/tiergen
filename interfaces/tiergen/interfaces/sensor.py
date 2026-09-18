"""The sensor interface: a static descriptor and a runtime Protocol.

The descriptor is data and is all the checker needs. The Protocol is what ``fit``,
``fidelity`` and ``assemble`` call. No implementation lives in this package.
"""

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from tiergen.core.events import Event, SensorFlowId
from tiergen.core.ir import SensorMode
from tiergen.interfaces.capability import Capability, CapabilityInfo


@dataclass(frozen=True, slots=True)
class SensorDescriptor:
    """What a sensor implementation can do, known without running it.

    ``versions`` are the sensor versions the backend can reproduce. ``capabilities`` is the
    most any configuration of this sensor can declare; a ``SensorSpec`` declares a subset.
    Registered under the entry-point group ``tiergen.sensors``, with the entry-point name
    equal to ``id``.
    """

    id: str
    versions: tuple[str, ...]
    modes: tuple[SensorMode, ...]
    capabilities: frozenset[Capability]


class Sensor(Protocol):
    """A passive traffic sensor with a pinned version and configuration."""

    @property
    def id(self) -> str:
        """The descriptor id: "zeek", "suricata"."""
        ...

    @property
    def version(self) -> str:
        """The exact sensor version, as recorded in the run manifest."""
        ...

    def capabilities(self) -> Mapping[Capability, CapabilityInfo]:
        """The capabilities this configuration declares, each with its coverage claim."""
        ...

    def ingest(self, native_logs: Path) -> Iterator[Event]:
        """Read the sensor's own logs into the common event model.

        Yields a ``ConnEvent`` for every connection, and ``AppEvent``s only if APP_EVENTS
        is declared. Every event keeps its raw record.
        """
        ...

    def flow_key(self, event: Event) -> SensorFlowId:
        """The sensor-native connection id that labels for this event are keyed by."""
        ...
