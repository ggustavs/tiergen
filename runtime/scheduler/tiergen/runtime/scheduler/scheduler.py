"""One run of a built scenario.

The hosts come up with their agents held at their gates, so the collector can attach to
their cgroups and the capture can be listening before the first invocation. Then every
agent is released in one pass, which is when scenario time begins, the run waits out the
scenario's duration or the seconds it was given, and everything comes down in reverse:
capture, collector, hosts.
What remains in the run directory is what ``tiergen assemble`` reads: the agents' records,
the collector's events, the captures, and ``run.json``, the run's record. A failure on the
way up takes down what had come up and leaves no record. A run interrupted while waiting
is a run cut short, recorded with the time it actually ran.
"""

import json
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from functools import partial
from pathlib import Path

from tiergen.backends.attrib._base import BY_INFRA
from tiergen.core.codec import from_json, to_json
from tiergen.core.ir import Scenario
from tiergen.interfaces import (
    AttributionBackend,
    InfraBackend,
    RunManifest,
    RunRecord,
    RunState,
)
from tiergen.interfaces.registry import load_attrib_backends, load_infra_backends
from tiergen.runtime.capture import dumpcap, offsets, points
from tiergen.runtime.capture.dumpcap import CaptureState
from tiergen.runtime.capture.points import Point

RUN = "run.json"
Log = Callable[[str], None]


class SchedulerError(RuntimeError):
    """The run cannot start; the message says what the run directory lacks."""


@dataclass(frozen=True, slots=True)
class Ports:
    """What the scheduler drives, as callables, so a test runs it against fakes."""

    infra: Callable[[set[str]], Mapping[str, InfraBackend]] = load_infra_backends
    attrib: Callable[[set[str]], Mapping[str, AttributionBackend]] = load_attrib_backends
    capture_start: Callable[[str, Sequence[Point], Path], CaptureState] = dumpcap.start
    capture_stop: Callable[[Path], CaptureState] = dumpcap.stop
    clock: Callable[[], float] = time.time
    sleep: Callable[[float], None] = time.sleep


def run_id(scenario: str, started: float) -> str:
    """The scenario's name and the UTC second the agents were started. Substrate names
    still carry the scenario name alone, so one run of a scenario at a time."""
    return f"{scenario}-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime(started))}"


def _read[T](cls: type[T], path: Path) -> T:
    return from_json(cls, json.loads(path.read_text("utf-8")))


def _dump(value: object, path: Path) -> None:
    path.write_text(json.dumps(to_json(value), indent=2) + "\n", encoding="utf-8")


def manifests(run_dir: Path) -> list[RunManifest]:
    paths = sorted(run_dir.glob("manifest.*.json"))
    if not paths:
        raise SchedulerError(f"{run_dir} holds no manifest; was it written by tiergen build?")
    return [_read(RunManifest, p) for p in paths]


def _state_file(run_dir: Path, backend: str) -> Path:
    return run_dir / f"state.{backend}.json"


def _down(backend: InfraBackend, manifest: RunManifest, state_file: Path) -> None:
    backend.down(manifest)
    state_file.unlink(missing_ok=True)


def _unwind(undo: list[Callable[[], None]], log: Log) -> Exception | None:
    """Run the undo steps in reverse, every one of them; the first failure is returned."""
    first: Exception | None = None
    for step in reversed(undo):
        try:
            step()
        except Exception as err:
            log(f"tiergen: while taking the run down: {err}")
            first = first or err
    undo.clear()
    return first


def run_scenario(
    run_dir: Path,
    for_s: float | None = None,
    ports: Ports | None = None,
    log: Log = lambda line: None,
) -> RunRecord:
    """Up, on, started, waited, down. ``for_s`` cuts the scenario's duration short, for a
    test of a scenario whose duration is hours."""
    ports = ports or Ports()
    found = manifests(run_dir)
    scenario = _read(Scenario, run_dir / "scenario.json")
    duration = scenario.duration_s if for_s is None else for_s
    infra = ports.infra({m.backend for m in found})
    missing = sorted({m.backend for m in found} - set(infra))
    if missing:
        raise SchedulerError(f"no runtime installed for backend(s): {', '.join(missing)}")
    wanted = {BY_INFRA[m.backend] for m in found if m.backend in BY_INFRA}
    attrib = ports.attrib(wanted)
    missing = sorted(wanted - set(attrib))
    if missing:
        raise SchedulerError(f"no attribution backend installed: {', '.join(missing)}")

    states: dict[str, RunState] = {}
    undo: list[Callable[[], None]] = []
    try:
        for manifest in found:
            backend = infra[manifest.backend]
            states[manifest.backend] = backend.up(manifest, run_dir, start=False)
            undo.append(partial(_down, backend, manifest, _state_file(run_dir, manifest.backend)))
            _dump(states[manifest.backend], _state_file(run_dir, manifest.backend))
            log(f"{manifest.backend}: {len(manifest.hosts)} host(s) up, agents held")
        for manifest in found:
            if manifest.backend not in BY_INFRA:
                log(f"{manifest.backend}: no attribution backend; its traffic is unattributed")
                continue
            name = BY_INFRA[manifest.backend]
            attrib[name].start(manifest, states[manifest.backend], run_dir)
            undo.append(partial(attrib[name].stop, run_dir))
            # The collector's image went into the state; keep the file current.
            _dump(states[manifest.backend], _state_file(run_dir, manifest.backend))
            log(f"{name}: recording {len(manifest.hosts)} host(s) of {manifest.backend}")
        run = points.load_run(run_dir)
        capture_points = points.capture_points(run.scenario, run.topology, run.bridges)
        for manifest in found:
            infra[manifest.backend].quiesce(manifest, states[manifest.backend])
        out = run_dir / "capture"
        capture = ports.capture_start(scenario.name, capture_points, out)
        undo.append(partial(_stop_capture, ports, out, log))
        offsets.write_offsets(out, offsets.offsets(states))
        for c in capture.captures:
            log(f"{c.point}: {', '.join(c.bridges)} -> capture/{c.file}")
        started = ports.clock()
        for manifest in found:
            infra[manifest.backend].start(manifest, states[manifest.backend])
        log(f"agents started; scenario time runs for {duration:g} s")
    except BaseException:
        _unwind(undo, log)
        raise

    cut = False
    try:
        while (left := started + duration - ports.clock()) > 0:
            ports.sleep(min(1.0, left))
    except KeyboardInterrupt:
        cut = True
    ran = ports.clock() - started
    log(f"{'interrupted' if cut else 'done'} after {ran:.0f} s; taking the run down")
    failure = _unwind(undo, log)
    if failure is not None:
        raise failure
    record = RunRecord(run_id(scenario.name, started), scenario.name, started, ran, states)
    _dump(record, run_dir / RUN)
    return record


def _stop_capture(ports: Ports, out: Path, log: Log) -> None:
    state = ports.capture_stop(out)
    for c in state.captures:
        tagged = state.tagged_packets.get(c.point)
        suffix = f", {tagged} packet(s) tagged" if tagged is not None else ""
        log(f"{c.point}: capture/{c.file}{suffix}")
