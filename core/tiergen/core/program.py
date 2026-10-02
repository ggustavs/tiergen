"""The projected program: everything one instance's agent needs, with every resource resolved.

``tiergen build`` writes one per instance into the run directory. An agent reads nothing
else, so it never sees a resource name, never resolves a tie, and never derives a route.
The program is data: a run is reproducible from the run directory and the seed.
"""

from collections.abc import Collection, Mapping
from dataclasses import dataclass

from tiergen.core.addressing import AddressPlan
from tiergen.core.groups import instance_ids, select, targets
from tiergen.core.ir import (
    Action,
    Choice,
    ChoiceRef,
    Distribution,
    ParamScalar,
    Platform,
    Scenario,
    ScheduleEvent,
    Select,
    Topology,
)
from tiergen.core.records import Peer
from tiergen.core.resolve import Resolver
from tiergen.core.routing import Route, RoutePlan


@dataclass(frozen=True, slots=True)
class ResolvedAction:
    """An action with its parameters resolved: a literal or an inline ``Choice``."""

    signature: str
    tie: str
    params: dict[str, ParamScalar | Choice]
    select: Select | None


@dataclass(frozen=True, slots=True)
class ResolvedBehaviour:
    """A behaviour with every resource inlined, as the agent's loop reads it."""

    name: str
    states: tuple[str, ...]
    initial: tuple[float, ...]
    transitions: tuple[tuple[float, ...], ...]
    dwell: tuple[Distribution, ...]
    rate: tuple[float, ...] | None
    action_map: dict[str, ResolvedAction | None]


@dataclass(frozen=True, slots=True)
class Program:
    """One instance's projected program.

    ``impls`` maps each signature the instance may run to its weighted implementation
    choices; ``services`` are the server signatures among them, which the agent starts at
    boot. ``peers`` maps each tie to the instances it reaches, with their address on the
    segment the source shares with them or routes to, and what they serve. ``routes`` are
    the static routes the host installs. ``schedule`` is the scenario's schedule narrowed to
    the events that select this instance, so the agent owns its own timeline.
    ``credentials`` names the resource the implementations authenticate with, by name: its
    contents are theirs, not the agent's.
    """

    scenario: str
    instance: str
    group: str
    kind: str
    platform: Platform
    hostname: str
    seed: int
    start: str
    duration_s: float
    behaviours: tuple[ResolvedBehaviour, ...]
    impls: dict[str, dict[str, float]]
    services: tuple[str, ...]
    peers: dict[str, tuple[Peer, ...]]
    routes: tuple[Route, ...]
    schedule: tuple[ScheduleEvent, ...]
    forwards: bool
    credentials: str | None


class UnresolvedError(ValueError):
    """A resource the program needs did not resolve. The checks would have reported it."""


def _resolve_action(resolver: Resolver, act: Action) -> ResolvedAction:
    params: dict[str, ParamScalar | Choice] = {}
    for name, value in act.params.items():
        if isinstance(value, ChoiceRef):
            choice = resolver.choice(value)
            if choice is None:
                raise UnresolvedError(f"choice resource {value.resource!r}")
            params[name] = choice
        else:
            params[name] = value
    return ResolvedAction(act.signature, act.tie, params, act.select)


def _peer_address(
    plan: AddressPlan, routes: RoutePlan, source: str, target: str, data: set[str]
) -> str | None:
    """The target's address the source should use: on a shared segment, else on the
    segment the source routes to."""
    mine = [s for s in plan.addresses.get(source, {}) if s in data]
    theirs = plan.addresses.get(target, {})
    for segment in mine:
        if segment in theirs:
            return theirs[segment]
    for route in routes.routes.get(source, ()):
        if route.segment in theirs:
            return theirs[route.segment]
    return None


def build_programs(
    scenario: Scenario,
    topology: Topology,
    plan: AddressPlan,
    routes: RoutePlan,
    resolver: Resolver,
    server_signatures: Collection[str],
) -> dict[str, Program]:
    """One program per instance, keyed by instance id. The scenario has passed the checks.

    ``server_signatures`` are the signature ids with role ``server`` (from ``tiergen.protocols``,
    which core does not import), so the program can say which bindings are services.
    """
    kinds = {k.name: k for k in scenario.kinds}
    bindings = {b.kind: b for b in scenario.bindings}
    data = {seg.name for seg in topology.segments if seg.plane == "data"}
    selected: dict[str, list[ScheduleEvent]] = {}
    for event in scenario.schedule:
        for instance in select(scenario, event.target) or []:
            selected.setdefault(instance, []).append(event)
    programs: dict[str, Program] = {}
    for path, kind_name, instance in instance_ids(scenario):
        kind = kinds[kind_name]
        binding = bindings[kind_name]
        behaviours: list[ResolvedBehaviour] = []
        for b in kind.behaviours:
            p = b.process
            states, initial = resolver.states(p), resolver.initial(p)
            transitions, dwell = resolver.transitions(p), resolver.dwell(p)
            action_map = resolver.action_map(b)
            if None in (states, initial, transitions, dwell, action_map):
                raise UnresolvedError(f"behaviour {b.name!r} of {kind_name!r}")
            assert states is not None
            assert initial is not None
            assert transitions is not None
            assert dwell is not None
            assert action_map is not None
            rate = resolver.rate(p)
            if p.rate is not None and rate is None:
                raise UnresolvedError(f"rate resource {p.rate!r} of behaviour {b.name!r}")
            resolved_dwell: list[Distribution] = []
            for d in dwell:
                params = resolver.resolve(d.params, tuple[float, ...])
                if params is None:
                    raise UnresolvedError(f"dwell parameters {d.params!r}")
                resolved_dwell.append(Distribution(d.family, params))
            behaviours.append(
                ResolvedBehaviour(
                    b.name,
                    states,
                    initial,
                    transitions,
                    tuple(resolved_dwell),
                    rate,
                    {
                        state: None if act is None else _resolve_action(resolver, act)
                        for state, act in action_map.items()
                    },
                )
            )
        impls: dict[str, dict[str, float]] = {}
        for selection in binding.impls:
            choices = resolver.choices(selection)
            if choices is None:
                raise UnresolvedError(f"choices for {selection.signature!r}")
            impls[selection.signature] = dict(choices)
        peers: dict[str, tuple[Peer, ...]] = {}
        for tie in kind.ties:
            reached = targets(scenario, path, kind_name, tie.name) or []
            found: list[Peer] = []
            for target in reached:
                address = _peer_address(plan, routes, instance, target, data)
                if address is not None:
                    found.append(Peer(target, address, kinds[tie.target_kind].serves))
            peers[tie.name] = tuple(found)
        programs[instance] = Program(
            scenario=scenario.name,
            instance=instance,
            group=path,
            kind=kind_name,
            platform=binding.host.platform,
            hostname=plan.hostnames[instance],
            seed=scenario.seed,
            start=scenario.start,
            duration_s=scenario.duration_s,
            behaviours=tuple(behaviours),
            impls=impls,
            services=tuple(s for s in impls if s in server_signatures),
            peers=peers,
            routes=routes.routes.get(instance, ()),
            schedule=tuple(selected.get(instance, ())),
            forwards=kind.forwards,
            credentials=binding.credentials,
        )
    return programs


def flat_id(instance: str) -> str:
    """``lab/web_server[0]`` as a file-name-safe ``lab-web_server-0``."""
    return instance.replace("/", "-").replace("[", "-").replace("]", "")


def programs_by_file(programs: Mapping[str, Program]) -> dict[str, Program]:
    return {f"program.{flat_id(i)}.json": p for i, p in programs.items()}
