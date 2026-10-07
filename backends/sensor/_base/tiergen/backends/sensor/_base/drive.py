"""Every offline sensor over every captured point: what ``tiergen sensors run`` does.

Needs the run directory after ``capture stop`` and nothing running: the IR for the sensor
specs, ``models/`` for their configurations, ``capture/capture.json`` for the points and
their files. Writes ``sensors/<name>/<point>/`` with the sensor's native logs and
``events.jsonl`` in the common event model, and ``sensors/<name>/image.json`` with the
digest of the instrument that ran.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from tiergen.core.codec import from_json, to_json
from tiergen.core.events import ConnEvent
from tiergen.core.ir import Scenario, SensorSpec
from tiergen.interfaces import Sensor
from tiergen.interfaces.registry import SensorFactory, load_sensor_runtime
from tiergen.runtime.capture.dumpcap import SUMMARY, CaptureState

EVENTS = "events.jsonl"
IMAGE = "image.json"


@dataclass(frozen=True, slots=True)
class Reading:
    """One sensor over one point: how many events of each kind it yielded."""

    sensor: str
    point: str
    connections: int
    app_events: int


@dataclass(frozen=True, slots=True)
class Readings:
    readings: list[Reading] = field(default_factory=list[Reading])
    digests: dict[str, str] = field(default_factory=dict[str, str])


def config_path(run_dir: Path, spec: SensorSpec) -> Path:
    """An opaque resource is the file or directory of its name under ``models/``."""
    return run_dir / "models" / spec.config


def run_sensors(
    run_dir: Path, factory: Callable[[str], SensorFactory] = load_sensor_runtime
) -> Readings:
    scenario = from_json(Scenario, json.loads((run_dir / "scenario.json").read_text("utf-8")))
    summary = run_dir / "capture" / SUMMARY
    if not summary.is_file():
        raise FileNotFoundError(f"{summary} is missing: has the capture been stopped?")
    capture = from_json(CaptureState, json.loads(summary.read_text("utf-8")))
    result = Readings()
    for spec in scenario.sensors:
        if spec.mode != "offline":
            continue
        make = factory(spec.impl)
        for captured in capture.captures:
            sensor: Sensor = make(spec, captured.point)
            out = run_dir / "sensors" / spec.name / captured.point
            digest = sensor.run(
                run_dir / "capture" / captured.file, config_path(run_dir, spec), out
            )
            result.digests[spec.name] = digest
            connections = app_events = 0
            with (out / EVENTS).open("w", encoding="utf-8") as f:
                for event in sensor.ingest(out):
                    if isinstance(event, ConnEvent):
                        connections += 1
                    else:
                        app_events += 1
                    f.write(json.dumps(to_json(event)) + "\n")
            result.readings.append(Reading(spec.name, captured.point, connections, app_events))
        (run_dir / "sensors" / spec.name / IMAGE).write_text(
            json.dumps(
                {"image": f"{spec.impl}:{spec.version}", "digest": result.digests[spec.name]},
                indent=2,
            )
            + "\n",
            "utf-8",
        )
    return result
