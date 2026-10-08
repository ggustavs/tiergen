"""From a scenario to its invocation records and events, without a host.

Programs are built as ``tiergen build`` builds them. Each behaviour of each instance runs
through ``BehaviourLoop`` with a clock that jumps, so a week of scenario time costs what
its draws cost, and with an implementation that records the call it was handed instead
of making a connection. An invocation then becomes the connections its signature's shape
promises: one ``ConnEvent`` per connection, at the invocation's start, from the instance's
address on the segment it shares with the target to the target's endpoint for the
signature's protocol; a scan becomes one rejected connection per port asked for. HTTP
invocations also give an ``AppEvent`` with the request's path, so a vocabulary that tells
``/`` from ``/news`` works on simulated events as on a sensor's. Durations and byte
counts are ``None``: they are the implementations', measured in M3, not the model's.

Records carry wall times from the scenario's ``start``, so the rate curve reads against
the same local hours the agents would see, and the sensor name is ``sim``.
"""

import contextlib
import json
from collections.abc import Collection, Generator, Iterator, Mapping
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from tiergen.core.addressing import AddressPlan, plan_addresses
from tiergen.core.codec import JsonValue, to_json
from tiergen.core.events import AppEvent, ConnEvent, Event, FiveTuple, SensorFlowId
from tiergen.core.ir import Scenario
from tiergen.core.program import Program, build_programs, flat_id, programs_by_file
from tiergen.core.records import AttributionKey, ClockStamp, InvocationRecord, Outcome, Peer
from tiergen.core.resolve import Resolver
from tiergen.core.resources import Resources
from tiergen.core.routing import plan_routes
from tiergen.impls._base import Context, PrimitiveImpl
from tiergen.protocols import SIGNATURES, Signature
from tiergen.runtime.behaviour import BehaviourLoop

SENSOR = "sim"
POINT = "all"
SERVERS = frozenset(s.id for s in SIGNATURES.values() if s.role == "server")
EPHEMERAL = 49152


class SimError(ValueError):
    """The scenario cannot be simulated; the message says what does not resolve."""


@dataclass(frozen=True, slots=True)
class Call:
    """What an invocation asked its implementation for."""

    invocation: str
    signature: str
    params: dict[str, JsonValue]
    targets: tuple[Peer, ...]


@dataclass(frozen=True, slots=True)
class Simulated:
    """Every instance's records in time order, the calls behind them by invocation id, and
    the events, in time order, that a sensor over every segment would have reported."""

    scenario: Scenario
    plan: AddressPlan
    programs: dict[str, Program]
    records: list[InvocationRecord]
    calls: dict[str, Call]
    events: list[Event]


class _Clock:
    """Scenario seconds that pass only when slept; wall time counted from ``epoch``."""

    def __init__(self, epoch: float) -> None:
        self.epoch = epoch
        self.t = 0.0

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += max(seconds, 0.0)

    def stamp(self) -> ClockStamp:
        return ClockStamp(self.epoch + self.t, self.t, 0.0)


class _Recorder:
    """The implementation every invocation gets: it records and succeeds."""

    def __init__(self) -> None:
        self.calls: dict[str, Call] = {}

    def run(self, ctx: Context, signature: str, **params: JsonValue) -> Outcome:
        self.calls[ctx.invocation] = Call(ctx.invocation, signature, params, ctx.targets)
        return "succeeded"


class _Attribution:
    @contextlib.contextmanager
    def enter(self, invocation: str) -> Generator[AttributionKey]:
        yield AttributionKey("linux", f"sim:{invocation}")


def programs_for(
    scenario: Scenario, resources: Resources
) -> tuple[AddressPlan, dict[str, Program]]:
    """The address plan and one program per instance, as ``build`` writes them. The scenario
    has passed the checks; what does not resolve is a ``SimError``."""
    resolver = Resolver(resources)
    topology = resolver.topology(scenario)
    if topology is None:
        raise SimError(f"{scenario.name}: the topology does not resolve")
    plan, problems = plan_addresses(scenario, topology)
    if problems:
        raise SimError(f"{scenario.name}: {problems[0].path}: {problems[0].message}")
    routes, _ = plan_routes(scenario, topology, plan)
    return plan, build_programs(scenario, topology, plan, routes, resolver, SERVERS)


def simulate_programs(
    programs: Mapping[str, Program], epoch: float
) -> tuple[list[InvocationRecord], dict[str, Call]]:
    """Every behaviour of every program under one clock each, records in time order."""
    recorder = _Recorder()
    records: list[InvocationRecord] = []

    def primitive(impl_id: str) -> PrimitiveImpl:
        return recorder

    for instance in sorted(programs):
        program = programs[instance]
        for behaviour in program.behaviours:
            BehaviourLoop(
                program,
                behaviour,
                clock=_Clock(epoch),
                primitive=primitive,
                attribution=_Attribution(),
                sink=records.append,
            ).run()
    records.sort(key=lambda r: (r.start, r.key.invocation))
    return records, recorder.calls


def simulate(
    scenario: Scenario,
    resources: Resources,
    *,
    seed: int | None = None,
    duration_s: float | None = None,
    instances: Collection[str] | None = None,
) -> Simulated:
    """``seed`` and ``duration_s`` override the scenario's; ``instances`` limits the run to
    those ids, the rest of the scenario still standing as their peers."""
    if seed is not None:
        scenario = replace(scenario, seed=seed)
    if duration_s is not None:
        scenario = replace(scenario, duration_s=duration_s)
    plan, programs = programs_for(scenario, resources)
    if instances is not None:
        missing = sorted(set(instances) - set(programs))
        if missing:
            raise SimError(f"no such instance(s): {', '.join(missing)}")
        programs = {i: p for i, p in programs.items() if i in instances}
    epoch = datetime.fromisoformat(scenario.start).timestamp()
    records, calls = simulate_programs(programs, epoch)
    events = list(_events(records, calls, plan))
    return Simulated(scenario, plan, programs, records, calls, events)


def _source(plan: AddressPlan, instance: str, target: Peer) -> str:
    """The instance's address on the segment the target's address is on, else its first."""
    mine = plan.addresses.get(instance, {})
    for segment, address in plan.addresses.get(target.instance, {}).items():
        if address == target.address and segment in mine:
            return mine[segment]
    return next(iter(mine.values()), "0.0.0.0")


def _ports(signature: Signature, params: Mapping[str, JsonValue], target: Peer) -> list[int]:
    """The destination ports one invocation reaches: the shape's, the target's endpoint for
    the signature's protocol, or, for a scan, every port its ``ports`` parameter names."""
    if signature.shape.port is not None:
        return [signature.shape.port]
    if signature.endpoints:
        for endpoint in target.served:
            if endpoint.protocol in signature.endpoints:
                return [endpoint.port]
        return []
    spec = params.get("ports")
    if isinstance(spec, str):
        found: list[int] = []
        for part in spec.split(","):
            lo, _, hi = part.strip().partition("-")
            found.extend(range(int(lo), int(hi or lo) + 1))
        return found
    if isinstance(spec, int):
        return [spec]
    return []


def _events(
    records: list[InvocationRecord], calls: Mapping[str, Call], plan: AddressPlan
) -> Iterator[Event]:
    n = 0
    for record in records:
        call = calls.get(record.key.invocation)
        if call is None:  # the implementation raised before recording: nothing on the wire
            continue
        signature = SIGNATURES[call.signature]
        scan = not signature.endpoints and signature.shape.port is None
        count = signature.shape.connections if isinstance(signature.shape.connections, int) else 1
        for target in call.targets:
            source = _source(plan, record.key.instance, target)
            for port in _ports(signature, call.params, target):
                for _ in range(1 if scan else count):
                    n += 1
                    flow = SensorFlowId(SENSOR, POINT, str(n))
                    five = FiveTuple(
                        source,
                        EPHEMERAL + (n % 16384),
                        target.address,
                        port,
                        signature.shape.transport,
                    )
                    yield ConnEvent(
                        flow,
                        five,
                        record.start,
                        None,
                        None,
                        None,
                        None,
                        None,
                        "rejected" if scan else "closed",
                        {"invocation": record.key.invocation},
                    )
                    if signature.protocol == "http" and not scan:
                        fields: dict[str, JsonValue] = {
                            "method": "POST" if "post" in signature.id else "GET",
                            "host": target.address,
                        }
                        path = call.params.get("path", call.params.get("start_path"))
                        if path is not None:
                            fields["uri"] = path
                        yield AppEvent(flow, 0, record.start, "http", fields, {})


def write(sim: Simulated, run_dir: Path) -> None:
    """A run directory as ``build``, the agents and ``sensors run`` would have left it:
    the IR, the plan, the programs, ``out/<instance>/invocations.jsonl`` and
    ``sensors/sim/all/events.jsonl``, so the fit reads a simulation like a run."""
    run_dir.mkdir(parents=True, exist_ok=True)
    _dump(sim.scenario, run_dir / "scenario.json")
    _dump(sim.plan, run_dir / "addresses.json")
    for name, program in programs_by_file(sim.programs).items():
        _dump(program, run_dir / name)
    by_instance: dict[str, list[InvocationRecord]] = {}
    for record in sim.records:
        by_instance.setdefault(record.key.instance, []).append(record)
    for instance in sim.programs:
        out = run_dir / "out" / flat_id(instance)
        out.mkdir(parents=True, exist_ok=True)
        _lines(by_instance.get(instance, []), out / "invocations.jsonl")
    sensor = run_dir / "sensors" / SENSOR / POINT
    sensor.mkdir(parents=True, exist_ok=True)
    _lines(sim.events, sensor / "events.jsonl")


def _dump(value: object, path: Path) -> None:
    path.write_text(json.dumps(to_json(value), indent=2) + "\n", encoding="utf-8")


def _lines(values: Collection[object], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(to_json(v)) + "\n" for v in values)


__all__ = [
    "EPHEMERAL",
    "POINT",
    "SENSOR",
    "Call",
    "SimError",
    "Simulated",
    "programs_for",
    "simulate",
    "simulate_programs",
    "write",
]
