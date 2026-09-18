"""Embedded builders: a scenario written as Python that evaluates to IR.

The builders only assemble data. They refuse what cannot be represented, such as two
kinds with one name; everything else, including a reference to a kind that is not in the
scenario, is left for the checker to report. ``scenario.py`` files are what ``fit``
proposes and what the engineer edits.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from tiergen.core.ir import (
    Action,
    ActorKind,
    Behaviour,
    Binding,
    Distribution,
    EgressPolicy,
    Endpoint,
    FitProvenance,
    Host,
    HostType,
    ImplSelection,
    Multiplicity,
    Platform,
    Scenario,
    ScheduleEvent,
    ScheduleOp,
    SemiMarkov,
    SensorMode,
    SensorRole,
    SensorSpec,
    Tie,
    Transport,
)


@dataclass(frozen=True, eq=False)
class Kind:
    """A handle on an ``ActorKind``, usable as a dictionary key and as a tie target.

    Handles compare by identity, so two kinds that happen to have equal contents stay
    distinct until ``scenario`` sees their names.
    """

    ir: ActorKind

    @property
    def name(self) -> str:
        return self.ir.name


@dataclass(frozen=True, slots=True)
class BindingSpec:
    """A binding that does not yet know its kind. ``scenario`` supplies it."""

    host: Host
    impls: tuple[ImplSelection, ...]


def _name(target: Kind | str) -> str:
    return target if isinstance(target, str) else target.name


def resource(name: str) -> str:
    """Refer to a resource by name. Marks intent; the IR stores the name itself."""
    return name


def endpoint(protocol: str, port: int, transport: Transport) -> Endpoint:
    return Endpoint(protocol, port, transport)


def tie(name: str, target: Kind | str, multiplicity: Multiplicity) -> Tie:
    return Tie(name, _name(target), multiplicity)


def dist(family: str, params: Sequence[float] | str) -> Distribution:
    return Distribution(family, params if isinstance(params, str) else tuple(params))


def action(signature: str, tie: str) -> Action:
    """Run ``signature`` against the peers reached over the tie named ``tie``."""
    return Action(signature, tie)


def semi_markov(
    name: str,
    *,
    states: Sequence[str] | str,
    initial: Sequence[float] | str,
    transitions: Sequence[Sequence[float]] | str,
    dwell: Sequence[Distribution] | str,
    action_map: Mapping[str, Action | None] | str,
    rate: str | None = None,
) -> Behaviour:
    """A behaviour driven by a semi-Markov process. Every part is inline or a resource."""
    process = SemiMarkov(
        states=states if isinstance(states, str) else tuple(states),
        initial=initial if isinstance(initial, str) else tuple(initial),
        transitions=(
            transitions
            if isinstance(transitions, str)
            else tuple(tuple(row) for row in transitions)
        ),
        dwell=dwell if isinstance(dwell, str) else tuple(dwell),
        rate=rate,
    )
    return Behaviour(name, process, action_map if isinstance(action_map, str) else dict(action_map))


def kind(
    name: str,
    *,
    platforms: Sequence[Platform],
    serves: Sequence[Endpoint] = (),
    ties: Sequence[Tie] = (),
    behaviours: Sequence[Behaviour] = (),
) -> Kind:
    return Kind(ActorKind(name, tuple(serves), tuple(ties), tuple(behaviours), tuple(platforms)))


def host(
    platform: Platform, host_type: HostType, ref: str = "default", *, manifest: str | None = None
) -> Host:
    """``ref`` is "default", "image:<ref>" or "template:<ref>". A custom host names the
    resource that lists what it serves in ``manifest``."""
    return Host(platform, host_type, ref, manifest)


def binding(
    host: Host, impls: Mapping[str, Mapping[str, float] | str] | None = None
) -> BindingSpec:
    """``impls`` maps a signature to weighted choices, ``{"impl_id[:variant]": weight}``, or
    to the resource that holds them."""
    selections = tuple(
        ImplSelection(signature, choices if isinstance(choices, str) else dict(choices))
        for signature, choices in (impls or {}).items()
    )
    return BindingSpec(host, selections)


def sensor(
    impl: str,
    version: str,
    config: str,
    mode: SensorMode,
    *,
    caps: Sequence[str],
    role: SensorRole,
) -> SensorSpec:
    return SensorSpec(impl, version, config, mode, tuple(caps), role)


def fit_provenance(
    sensor: str, capabilities_used: Sequence[str], coverage: Mapping[str, float]
) -> FitProvenance:
    return FitProvenance(sensor, tuple(capabilities_used), dict(coverage))


def hours(n: float) -> float:
    return n * 3600.0


def at(
    at_s: float, target: Kind | str, op: ScheduleOp, arg: str | float | None = None
) -> ScheduleEvent:
    """``target`` is a kind, a kind name, or ``"kind[i]"`` for one instance."""
    return ScheduleEvent(at_s, _name(target), op, arg)


def scenario(
    name: str,
    *,
    instances: Mapping[Kind, int],
    bindings: Mapping[Kind, BindingSpec],
    topology: str,
    egress: EgressPolicy,
    duration_s: float,
    capture_points: Sequence[str],
    sensors: Sequence[SensorSpec],
    seed: int,
    egress_overrides: Mapping[str, str] | None = None,
    schedule: Sequence[ScheduleEvent] = (),
    fit_provenance: FitProvenance | str | None = None,
    coverage_floor: float = 0.5,
) -> Scenario:
    """Assemble the root. The scenario's kinds are the keys of ``instances``, in order."""
    kinds = tuple(k.ir for k in instances)
    names = [k.name for k in kinds]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError(f"two kinds share a name: {', '.join(duplicates)}")
    return Scenario(
        name=name,
        kinds=kinds,
        instances={k.name: count for k, count in instances.items()},
        bindings=tuple(Binding(k.name, spec.host, spec.impls) for k, spec in bindings.items()),
        topology=topology,
        egress=egress,
        egress_overrides=dict(egress_overrides or {}),
        schedule=tuple(schedule),
        duration_s=duration_s,
        capture_points=tuple(capture_points),
        sensors=tuple(sensors),
        fit_provenance=fit_provenance,
        seed=seed,
        coverage_floor=coverage_floor,
    )
