"""The Protocols are satisfiable: a minimal fake of each passes pyright and runs."""

from collections.abc import Iterator, Mapping
from pathlib import Path

from tiergen.core.events import ConnEvent, Event, FiveTuple, SensorFlowId
from tiergen.core.ir import HostType, Platform, Scenario
from tiergen.interfaces import (
    AttributionBackend,
    AttributionRecord,
    Capability,
    CapabilityInfo,
    InfraBackend,
    Sensor,
)

CONN = ConnEvent(
    flow=SensorFlowId("fake", "C1"),
    five_tuple=FiveTuple("10.0.0.2", 50000, "10.0.0.1", 445, "tcp"),
    start=0.0,
    duration=None,
    orig_bytes=None,
    resp_bytes=None,
    orig_pkts=1,
    resp_pkts=0,
    state="attempted",
    raw={},
)


class FlowOnlySensor:
    """A sensor at the floor: connections, no capabilities."""

    id = "fake"
    version = "0"

    def capabilities(self) -> Mapping[Capability, CapabilityInfo]:
        return {}

    def ingest(self, native_logs: Path) -> Iterator[Event]:
        yield CONN

    def flow_key(self, event: Event) -> SensorFlowId:
        return event.flow


class NoInfra:
    id = "none"

    def platforms(self) -> frozenset[tuple[Platform, HostType]]:
        return frozenset()

    def grantable(self, platform: Platform, host_type: HostType) -> frozenset[str]:
        return frozenset()

    def plan(self, scenario: Scenario, run_dir: Path) -> None: ...

    def up(self, run_dir: Path) -> None: ...

    def down(self, run_dir: Path) -> None: ...


class NoAttribution:
    platform: Platform = "linux"

    def start(self, host: str) -> None: ...

    def stop(self, host: str) -> None: ...

    def collect(self, host: str) -> Iterator[AttributionRecord]:
        yield AttributionRecord(host, "cgroup:/x", CONN.five_tuple, 0.0, 1.0)


def test_a_flow_only_sensor_meets_the_interface() -> None:
    sensor: Sensor = FlowOnlySensor()
    events = list(sensor.ingest(Path(".")))
    assert events == [CONN]
    assert sensor.flow_key(events[0]) == SensorFlowId("fake", "C1")
    assert Capability.APP_EVENTS not in sensor.capabilities()


def test_infra_and_attribution_fakes_meet_their_interfaces() -> None:
    infra: InfraBackend = NoInfra()
    attribution: AttributionBackend = NoAttribution()
    assert infra.platforms() == frozenset()
    assert [r.host for r in attribution.collect("h1")] == ["h1"]


def test_capability_names_are_what_the_ir_stores() -> None:
    assert Capability["SMB_DIALECT"] is Capability.SMB_DIALECT
