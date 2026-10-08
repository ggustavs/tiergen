"""The assembly over a run directory, after ``capture stop`` and ``attrib stop``.

Runs the sensors, reads what the run left (``out/<instance>/invocations.jsonl`` from the
agents, the attribution backend's records, each sensor's ``events.jsonl``, the address
plan for who owns which address, the programs for which signature each state runs), joins
them, and writes ``labels.<sensor>.jsonl``, ``flagged.jsonl`` and ``manifest.json``. The
run's record (``run.json``, from ``tiergen run``) says which backends were up and from
which images; a run brought up by hand has its state files instead, until ``infra down``.
"""

import json
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

from tiergen.backends.assemble.join import join, signatures
from tiergen.backends.assemble.manifest import (
    Counts,
    HostEntry,
    Manifest,
    SensorEntry,
    sha256,
    tool_versions,
)
from tiergen.backends.attrib._base import BY_INFRA
from tiergen.backends.sensor._base.drive import EVENTS, Readings, run_sensors
from tiergen.core.addressing import AddressPlan
from tiergen.core.codec import decode, from_json, to_json
from tiergen.core.events import AppEvent, ConnEvent
from tiergen.core.ir import Scenario
from tiergen.core.program import Program
from tiergen.core.records import InvocationRecord
from tiergen.interfaces import AttributionBackend, AttributionRecord, RunRecord, RunState
from tiergen.interfaces.registry import SensorFactory, load_attrib_backends, load_sensor_runtime
from tiergen.runtime.capture.dumpcap import SUMMARY, CaptureState
from tiergen.runtime.capture.offsets import OFFSETS, ClockOffset

RUN = "run.json"
RECORDS = "invocations.jsonl"
FLAGGED = "flagged.jsonl"
MANIFEST = "manifest.json"
SHARED_TOLERANCE_S = 1.0
"""How far apart the agent's stamp, the kernel's and the sensor's may be for one connection
when every host shares the capture host's clock: scheduling and the sensor's own
timestamping, never a clock offset. A host with its own clock gets a tolerance from its
measured offset (phase B); until then its presence stops the assembly."""

AttribLoader = Callable[[set[str]], Mapping[str, AttributionBackend]]


class AssembleError(RuntimeError):
    """The run directory lacks something the assembly needs; the message says what."""


@dataclass(frozen=True, slots=True)
class Summary:
    """Labels and flags by count: labels per sensor, flags per ``kind/reason``."""

    readings: Readings
    labels: dict[str, int]
    flags: dict[str, int]
    manifest: Manifest


def _read[T](cls: type[T], path: Path) -> T:
    return from_json(cls, json.loads(path.read_text("utf-8")))


def _dump(value: object, path: Path) -> None:
    path.write_text(json.dumps(to_json(value), indent=2) + "\n", encoding="utf-8")


def run_record(run_dir: Path, scenario: Scenario, capture: CaptureState) -> RunRecord:
    """``run.json`` if ``tiergen run`` wrote it, else what the state files and the capture say
    of a run brought up by hand."""
    if (run_dir / RUN).is_file():
        return _read(RunRecord, run_dir / RUN)
    states = {
        p.name[len("state.") : -len(".json")]: _read(RunState, p)
        for p in sorted(run_dir.glob("state.*.json"))
    }
    if not states:
        raise AssembleError(
            f"{run_dir}: neither {RUN} nor a run state; a run brought up by hand is assembled "
            "before infra down"
        )
    stopped = capture.stopped if capture.stopped is not None else capture.started
    return RunRecord(
        scenario.name, scenario.name, capture.started, stopped - capture.started, states
    )


def invocations(run_dir: Path) -> list[InvocationRecord]:
    found: list[InvocationRecord] = []
    for path in sorted((run_dir / "out").glob(f"*/{RECORDS}")):
        with path.open(encoding="utf-8") as f:
            found.extend(
                from_json(InvocationRecord, json.loads(line)) for line in f if line.strip()
            )
    return found


def attribution(
    run_dir: Path, states: Mapping[str, RunState], loader: AttribLoader
) -> list[AttributionRecord]:
    wanted = {BY_INFRA[b] for b in states if b in BY_INFRA}
    backends = loader(wanted)
    missing = sorted(wanted - set(backends))
    if missing:
        raise AssembleError(f"no attribution backend installed: {', '.join(missing)}")
    found: list[AttributionRecord] = []
    for name in sorted(wanted):
        found.extend(backends[name].records(run_dir))
    return found


def tolerance(run_dir: Path) -> float:
    offsets = _read(dict[str, ClockOffset], run_dir / "capture" / OFFSETS)
    unmeasured = sorted(i for i, o in offsets.items() if o.offset_s is None)
    if unmeasured:
        raise AssembleError(
            f"the clock offset of {', '.join(unmeasured)} is unmeasured; the join cannot place "
            "their intervals on the capture"
        )
    return SHARED_TOLERANCE_S


def connections(run_dir: Path, scenario: Scenario, capture: CaptureState) -> Iterator[ConnEvent]:
    for spec in scenario.sensors:
        if spec.mode != "offline":
            continue
        for captured in capture.captures:
            path = run_dir / "sensors" / spec.name / captured.point / EVENTS
            with path.open(encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        event = decode(ConnEvent | AppEvent, json.loads(line))
                        if isinstance(event, ConnEvent):
                            yield event


def assemble(
    run_dir: Path,
    *,
    sensor_factory: Callable[[str], SensorFactory] = load_sensor_runtime,
    attribution_loader: AttribLoader = load_attrib_backends,
) -> Summary:
    readings = run_sensors(run_dir, sensor_factory)
    scenario = _read(Scenario, run_dir / "scenario.json")
    capture = _read(CaptureState, run_dir / "capture" / SUMMARY)
    record = run_record(run_dir, scenario, capture)
    plan = _read(AddressPlan, run_dir / "addresses.json")
    instance_of = {a: i for i, by_segment in plan.addresses.items() for a in by_segment.values()}
    programs = [_read(Program, p) for p in sorted(run_dir.glob("program.*.json"))]
    ran = invocations(run_dir)
    records = attribution(run_dir, record.states, attribution_loader)
    tolerance_s = tolerance(run_dir)
    joined = join(
        connections(run_dir, scenario, capture),
        records,
        ran,
        signatures(programs),
        instance_of,
        tolerance_s,
    )

    offline = [s for s in scenario.sensors if s.mode == "offline"]
    labels: dict[str, int] = {}
    for spec in offline:
        found = joined.labels.get(spec.name, [])
        with (run_dir / f"labels.{spec.name}.jsonl").open("w", encoding="utf-8") as f:
            f.writelines(json.dumps(to_json(label)) + "\n" for label in found)
        labels[spec.name] = len(found)
    with (run_dir / FLAGGED).open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(to_json(flag)) + "\n" for flag in joined.flags)
    flags: dict[str, int] = {}
    for flag in joined.flags:
        flags[f"{flag.kind}/{flag.reason}"] = flags.get(f"{flag.kind}/{flag.reason}", 0) + 1

    images: dict[str, str] = {}
    hosts: dict[str, HostEntry] = {}
    for backend, state in sorted(record.states.items()):
        images.update(state.images)
        hosts.update({i: HostEntry(backend, h.name, h.id) for i, h in state.hosts.items()})
    sensors: dict[str, SensorEntry] = {}
    for spec in offline:
        image = f"{spec.impl}:{spec.version}"
        digest = readings.digests[spec.name]
        images[image] = digest
        sensors[spec.name] = SensorEntry(spec.impl, spec.version, image, digest, spec.capabilities)
    seen: dict[str, int] = {}
    for r in readings.readings:
        seen[r.sensor] = seen.get(r.sensor, 0) + r.connections
    manifest = Manifest(
        record.run,
        scenario.name,
        scenario.seed,
        scenario.duration_s,
        record.started,
        record.duration_s,
        sha256(run_dir / "scenario.json"),
        tool_versions(),
        dict(sorted(images.items())),
        dict(sorted(hosts.items())),
        {c.point: c.file for c in capture.captures},
        sensors,
        tolerance_s,
        Counts(len(ran), len(records), seen, labels, flags),
    )
    _dump(manifest, run_dir / MANIFEST)
    return Summary(readings, labels, flags, manifest)
