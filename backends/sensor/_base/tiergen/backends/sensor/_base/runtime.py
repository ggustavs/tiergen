"""What the containerised sensors share: construction from a spec and a point, the run,
the capabilities as declared, and the flow ids.

A subclass says which image and command run the sensor and how its native logs become
events; everything else is here.
"""

from collections.abc import Callable, Iterator, Mapping
from pathlib import Path

from tiergen.backends.infra.docker._client import Client, DaemonClient
from tiergen.backends.sensor._base.runner import run_image
from tiergen.core.events import Event, SensorFlowId
from tiergen.core.ir import SensorSpec
from tiergen.interfaces import SCHEMAS, Capability, CapabilityInfo


class ContainerSensor:
    """A sensor that runs as a pinned image over one capture point's pcap."""

    repository: str = ""
    """The image repository; the spec's version is the tag."""

    def __init__(
        self, spec: SensorSpec, capture_point: str, client: Callable[[], Client] = DaemonClient
    ) -> None:
        self.spec = spec
        self._capture_point = capture_point
        self._connect = client

    @property
    def id(self) -> str:
        return self.spec.impl

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def capture_point(self) -> str:
        return self._capture_point

    @property
    def version(self) -> str:
        return self.spec.version

    @property
    def image(self) -> str:
        return f"{self.repository}:{self.spec.version}"

    def command(self, pcap: str, config: str) -> list[str]:
        """The command that reads ``/pcap/<pcap>`` with ``/config/<config>`` into ``/out``."""
        raise NotImplementedError

    def run(self, pcap: Path, config: Path, out: Path) -> str:
        return run_image(
            self._connect(), self.image, self.command(pcap.name, config.name), pcap, config, out
        )

    def capabilities(self) -> Mapping[Capability, CapabilityInfo]:
        """What the spec declares, each with the sensor's own claim of full coverage; ``fit``
        replaces the claim with what it measures."""
        return {
            Capability[name]: CapabilityInfo(SCHEMAS[Capability[name]].name, 1.0)
            for name in self.spec.capabilities
        }

    def flow(self, native: str) -> SensorFlowId:
        return SensorFlowId(self.name, self.capture_point, native)

    def ingest(self, native_logs: Path) -> Iterator[Event]:
        raise NotImplementedError

    def flow_key(self, event: Event) -> SensorFlowId:
        return event.flow
