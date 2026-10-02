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
    CapturePoint,
    Choice,
    ChoiceRef,
    Distribution,
    EgressPolicy,
    Endpoint,
    FitProvenance,
    Group,
    Host,
    HostType,
    ImplSelection,
    Multiplicity,
    Network,
    ParamScalar,
    ParamValue,
    Plane,
    Platform,
    Scenario,
    ScheduleEvent,
    ScheduleOp,
    SemiMarkov,
    SensorMode,
    SensorRole,
    SensorSpec,
    Tie,
    Topology,
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


@dataclass(frozen=True, eq=False)
class GroupHandle:
    """A handle on a ``Group``, usable as a wiring target and as another group's parent."""

    ir: Group
    kinds: tuple[Kind, ...]

    @property
    def path(self) -> str:
        return self.ir.path


@dataclass(frozen=True, slots=True)
class BindingSpec:
    """A binding that does not yet know its kind. ``scenario`` supplies it."""

    host: Host
    impls: tuple[ImplSelection, ...]


def _name(target: Kind | str) -> str:
    return target if isinstance(target, str) else target.name


def _path(target: GroupHandle | str) -> str:
    return target if isinstance(target, str) else target.path


def resource(name: str) -> str:
    """Refer to a resource by name. Marks intent; the IR stores the name itself."""
    return name


def endpoint(protocol: str, port: int, transport: Transport) -> Endpoint:
    return Endpoint(protocol, port, transport)


def tie(name: str, target: Kind | str, multiplicity: Multiplicity) -> Tie:
    return Tie(name, _name(target), multiplicity)


def dist(family: str, params: Sequence[float] | str) -> Distribution:
    return Distribution(family, params if isinstance(params, str) else tuple(params))


def choice(options: Sequence[ParamScalar], weights: Sequence[float]) -> Choice:
    """A parameter value sampled per invocation, ``options[i]`` with weight ``weights[i]``."""
    return Choice(tuple(options), tuple(weights))


def choice_from(resource: str) -> ChoiceRef:
    """A choice held in a resource: ``{"options": [...], "weights": [...]}``."""
    return ChoiceRef(resource)


def action(signature: str, tie: str, params: Mapping[str, ParamValue] | None = None) -> Action:
    """Run ``signature`` against the peers reached over the tie named ``tie``.

    ``params`` gives each of the signature's parameters a literal, a ``choice`` or a
    ``choice_from``.
    """
    return Action(signature, tie, dict(params or {}))


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
    platform: Platform,
    host_type: HostType,
    ref: str = "default",
    *,
    backend: str,
    manifest: str | None = None,
) -> Host:
    """``backend`` is the infrastructure backend that provides the host, "docker" or
    "libvirt". ``ref`` is "default", "image:<ref>" or "template:<ref>". A custom host whose
    kind serves something names the resource that lists what it serves in ``manifest``."""
    return Host(platform, host_type, backend, ref, manifest)


def network(name: str, cidr: str, plane: Plane = "data") -> Network:
    return Network(name, cidr, plane)


def capture_point(name: str, network: Network | str) -> CapturePoint:
    return CapturePoint(name, network if isinstance(network, str) else network.name)


def topology(
    networks: Sequence[Network],
    capture_points: Sequence[CapturePoint] = (),
    addresses: Mapping[str, str] | None = None,
) -> Topology:
    """The networks and capture points. Who joins which is said per ``group``. ``addresses``
    pins single instances by id, ``path/kind[i]``; everything else is allocated."""
    return Topology(tuple(networks), tuple(capture_points), dict(addresses or {}))


def group(
    name: str,
    *,
    instances: Mapping[Kind, int],
    attachments: Mapping[Kind, Sequence[Network | str]],
    wiring: Mapping[str, GroupHandle | str | Sequence[GroupHandle | str]] | None = None,
    parent: GroupHandle | str | None = None,
) -> GroupHandle:
    """A scope holding ``instances`` of some kinds, each joining its ``attachments``.

    ``wiring`` maps ``"kind.tie"`` to the group or groups whose instances of the tie's target
    kind are its targets. A tie left out is wired to this group itself when this group holds
    instances of the target kind, and left unwired otherwise, which check 1 reports. That is
    the only convenience: the IR holds the result, and nothing is looked up at run time.
    """
    path = name if parent is None else f"{_path(parent)}/{name}"
    held = {k.name: count for k, count in instances.items()}
    wired: dict[str, tuple[str, ...]] = {}
    for key, value in (wiring or {}).items():
        targets = (value,) if isinstance(value, (GroupHandle, str)) else tuple(value)
        wired[key] = tuple(_path(t) for t in targets)
    for kind in instances:
        for tie in kind.ir.ties:
            key = f"{kind.name}.{tie.name}"
            if key not in wired and tie.target_kind in held:
                wired[key] = (path,)
    return GroupHandle(
        kinds=tuple(instances),
        ir=Group(
            name=name,
            parent=None if parent is None else _path(parent),
            instances=held,
            attachments={
                _name(kind): tuple(n if isinstance(n, str) else n.name for n in nets)
                for kind, nets in attachments.items()
            },
            wiring=wired,
        ),
    )


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
    at_s: float,
    target: GroupHandle | str,
    op: ScheduleOp,
    arg: str | float | None = None,
    *,
    kind: Kind | str | None = None,
    index: int | None = None,
) -> ScheduleEvent:
    """``target`` is a group, or a target string. With ``kind``, every instance of that kind
    under the group; with ``index`` as well, one instance."""
    text = _path(target)
    if kind is not None:
        text = f"{text}/{_name(kind)}"
        if index is not None:
            text = f"{text}[{index}]"
    return ScheduleEvent(at_s, text, op, arg)


def scenario(
    name: str,
    *,
    groups: Sequence[GroupHandle],
    bindings: Mapping[Kind, BindingSpec],
    topology: Topology | str,
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
    """Assemble the root. The scenario's kinds are those the groups and bindings mention, in
    order of first mention; a kind nobody holds and nobody binds is not in the scenario."""
    mentioned: list[Kind] = [*_kinds_of(groups), *bindings]
    kinds: list[ActorKind] = []
    for kind in mentioned:
        if kind.ir not in kinds:
            kinds.append(kind.ir)
    names = [k.name for k in kinds]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise ValueError(f"two kinds share a name: {', '.join(duplicates)}")
    return Scenario(
        name=name,
        kinds=tuple(kinds),
        groups=tuple(g.ir for g in groups),
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


def _kinds_of(groups: Sequence[GroupHandle]) -> list[Kind]:
    """The kind handles the groups were built with, which ``group`` keeps on the handle."""
    return [kind for g in groups for kind in g.kinds]
