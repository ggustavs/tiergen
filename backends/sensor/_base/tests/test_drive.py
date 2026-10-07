"""The driver over a fake sensor: every offline spec over every captured point."""

import json
from collections.abc import Iterator, Mapping
from pathlib import Path

import pytest

from tiergen.backends.sensor._base.drive import run_sensors
from tiergen.cli.main import main
from tiergen.core.codec import decode, to_json
from tiergen.core.events import AppEvent, ConnEvent, Event, FiveTuple, SensorFlowId
from tiergen.core.ir import SensorSpec
from tiergen.interfaces import Capability, CapabilityInfo
from tiergen.interfaces.registry import SensorFactory
from tiergen.runtime.capture.dumpcap import CaptureState, Running

EXAMPLES = Path(__file__).parents[4] / "examples"


class FakeSensor:
    def __init__(self, spec: SensorSpec, capture_point: str) -> None:
        self.spec = spec
        self.capture_point = capture_point

    @property
    def id(self) -> str:
        return self.spec.impl

    @property
    def name(self) -> str:
        return self.spec.name

    @property
    def version(self) -> str:
        return self.spec.version

    def run(self, pcap: Path, config: Path, out: Path) -> str:
        assert pcap.is_file()
        assert config.is_file()
        out.mkdir(parents=True, exist_ok=True)
        (out / "native.log").write_text("x")
        return f"{self.spec.impl}@sha256:{self.spec.version}"

    def capabilities(self) -> Mapping[Capability, CapabilityInfo]:
        return {}

    def ingest(self, native_logs: Path) -> Iterator[Event]:
        assert (native_logs / "native.log").is_file()
        flow = SensorFlowId(self.name, self.capture_point, "C1")
        five = FiveTuple("10.20.0.2", 40000, "10.20.0.80", 80, "tcp")
        yield ConnEvent(flow, five, 1.0, 0.1, 1, 2, 3, 4, "closed", {})
        yield AppEvent(flow, 0, 1.0, "http", {"user_agent": "x"}, {})

    def flow_key(self, event: Event) -> SensorFlowId:
        return event.flow


def _built(tmp_path: Path, with_capture: bool) -> Path:
    run_dir = tmp_path / "r"
    scenario = EXAMPLES / "linux_slice" / "scenario.py"
    assert main(["build", str(scenario), "--out", str(run_dir)]) == 0
    if with_capture:
        capture = run_dir / "capture"
        capture.mkdir()
        (capture / "lan-span.pcapng").write_bytes(b"")
        running = Running("lan-span", 1, "lan-span.pcapng", ("lan",), ("tg-x",), (None,), False)
        state = CaptureState("linux_slice", 1.0, (running,), 2.0)
        (capture / "capture.json").write_text(json.dumps(to_json(state)))
    return run_dir


def test_every_offline_sensor_reads_every_point(tmp_path: Path) -> None:
    run_dir = _built(tmp_path, with_capture=True)
    made: list[tuple[str, str]] = []

    def factory(sensor_id: str) -> SensorFactory:
        def make(spec: SensorSpec, point: str) -> FakeSensor:
            made.append((spec.name, point))
            return FakeSensor(spec, point)

        return make

    readings = run_sensors(run_dir, factory)
    assert [(r.sensor, r.point, r.connections, r.app_events) for r in readings.readings] == [
        ("zeek", "lan-span", 1, 1),
        ("suricata", "lan-span", 1, 1),
    ]
    assert readings.digests == {"zeek": "zeek@sha256:7.0", "suricata": "suricata@sha256:7.0.7"}
    lines = (run_dir / "sensors" / "zeek" / "lan-span" / "events.jsonl").read_text().splitlines()
    # The alias is a ``type`` statement, which the codec does not unwrap; the union does.
    events: list[Event] = [decode(ConnEvent | AppEvent, json.loads(line)) for line in lines]
    assert isinstance(events[0], ConnEvent)
    assert events[0].flow == SensorFlowId("zeek", "lan-span", "C1")
    assert isinstance(events[1], AppEvent)
    image = json.loads((run_dir / "sensors" / "suricata" / "image.json").read_text())
    assert image == {"image": "suricata:7.0.7", "digest": "suricata@sha256:7.0.7"}
    assert made == [("zeek", "lan-span"), ("suricata", "lan-span")]


def test_without_a_stopped_capture_there_is_nothing_to_read(tmp_path: Path) -> None:
    run_dir = _built(tmp_path, with_capture=False)
    with pytest.raises(FileNotFoundError, match="has the capture been stopped"):
        run_sensors(run_dir, lambda _: FakeSensor)
