"""The Protocols are satisfiable: a minimal fake of each passes pyright and runs."""

from collections.abc import Iterator, Mapping
from pathlib import Path

from tiergen.core.events import ConnEvent, Event, FiveTuple, SensorFlowId
from tiergen.core.ir import Platform
from tiergen.core.records import AttributionKey
from tiergen.interfaces import (
    AttributionBackend,
    AttributionRecord,
    Capability,
    CapabilityInfo,
    InfraBackend,
    RunManifest,
    RunState,
    Sensor,
)

CONN = ConnEvent(
    flow=SensorFlowId("fake", "span0", "C1"),
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
    seen: list[str]

    def __init__(self) -> None:
        self.seen = []

    def up(self, manifest: RunManifest, run_dir: Path) -> RunState:
        self.seen.append(f"up {manifest.run}")
        return RunState(manifest.run, self.id)

    def down(self, manifest: RunManifest) -> None:
        self.seen.append(f"down {manifest.run}")

    def quiesce(self, manifest: RunManifest, state: RunState) -> None:
        self.seen.append(f"quiesce {manifest.run}")


class NoAttribution:
    platform: Platform = "linux"

    def start(self, manifest: RunManifest, state: RunState, run_dir: Path) -> None: ...

    def stop(self, run_dir: Path) -> None: ...

    def records(self, run_dir: Path) -> Iterator[AttributionRecord]:
        yield AttributionRecord(
            "h1", AttributionKey("linux", "cgroup:4242"), CONN.five_tuple, 0.0, 1.0
        )


def test_a_flow_only_sensor_meets_the_interface() -> None:
    sensor: Sensor = FlowOnlySensor()
    events = list(sensor.ingest(Path(".")))
    assert events == [CONN]
    assert sensor.flow_key(events[0]) == SensorFlowId("fake", "span0", "C1")
    assert Capability.APP_EVENTS not in sensor.capabilities()


def test_infra_and_attribution_fakes_meet_their_interfaces() -> None:
    infra: InfraBackend = NoInfra()
    attribution: AttributionBackend = NoAttribution()
    infra.up(RunManifest("r", "none", (), ()), Path("run"))
    assert isinstance(infra, InfraBackend)
    attribution.start(RunManifest("r", "none", (), ()), RunState("r", "none"), Path("run"))
    assert [r.instance for r in attribution.records(Path("run"))] == ["h1"]


def test_capability_names_are_what_the_ir_stores() -> None:
    assert Capability["SMB_DIALECT"] is Capability.SMB_DIALECT
