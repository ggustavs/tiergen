"""The scenario IR: a finite, first-order description of a run, as data.

Every node is a frozen slotted dataclass built from JSON-shaped values, so a scenario
round-trips through JSON unchanged. Nothing here is callable: signatures, implementations,
sensors and resources are referenced by name.

A field typed ``... | str`` takes either an inline value or the name of a resource that
holds one. A field typed plain ``str`` and documented as a resource is always a name.
Names are resolved by the checker, never here.
"""

from dataclasses import dataclass, field
from typing import Literal

from tiergen.core.codec import JsonValue, from_json, to_json

Multiplicity = Literal["single", "optional", "multiple"]
Transport = Literal["tcp", "udp"]
Platform = Literal["linux", "windows"]
HostType = Literal["container", "vm"]
EgressPolicy = Literal["stub", "allowlist", "none"]
ScheduleOp = Literal["start", "stop", "set_rate", "run_sequence"]
SensorMode = Literal["offline", "live"]
SensorRole = Literal["label", "fit", "both"]
Plane = Literal["data", "management"]
Select = Literal["all", "one"]
ParamScalar = str | int | float | bool


@dataclass(frozen=True, slots=True)
class Endpoint:
    """A service an actor offers: protocol name, port and transport."""

    protocol: str
    port: int
    transport: Transport


@dataclass(frozen=True, slots=True)
class Tie:
    """A typed relation from the owning kind to ``target_kind``: who may talk to whom."""

    name: str
    target_kind: str
    multiplicity: Multiplicity


@dataclass(frozen=True, slots=True)
class Distribution:
    """A dwell-time distribution.

    ``family`` is one of "exponential", "lognormal", "weibull" or "empirical". ``params`` is
    inline or a resource name.
    """

    family: str
    params: tuple[float, ...] | str


@dataclass(frozen=True, slots=True)
class SemiMarkov:
    """A semi-Markov process over ``states``, one dwell distribution per state.

    ``states``, ``initial``, ``transitions`` and ``dwell`` are each inline or a resource
    name, so a fitted process can live entirely in resources. ``rate`` names a resource of
    hourly multipliers, 24 or 168 values, or is None for a constant rate.
    """

    states: tuple[str, ...] | str
    initial: tuple[float, ...] | str
    transitions: tuple[tuple[float, ...], ...] | str
    dwell: tuple[Distribution, ...] | str
    rate: str | None


@dataclass(frozen=True, slots=True)
class Choice:
    """A parameter value sampled per invocation: ``options[i]`` with weight ``weights[i]``."""

    options: tuple[ParamScalar, ...]
    weights: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class ChoiceRef:
    """A ``Choice`` held in a resource, such as the path popularity ``fit`` measured."""

    resource: str


ParamValue = ParamScalar | Choice | ChoiceRef


@dataclass(frozen=True, slots=True)
class Action:
    """What a behaviour state does: run ``signature`` against the peers reached over ``tie``.

    ``params`` gives a value for each parameter the signature declares: a literal, used for
    every invocation, or a choice, sampled for each one from the instance's seeded generator.
    Parameters are part of the IR so that a run is reproducible from IR and seed, and so that
    ``predict`` can see what is asked for, not only how often. ``select`` says which of a
    ``multiple`` tie's targets an invocation hits: all of them, or one drawn uniformly. It is
    required when the tie is ``multiple`` (check 16) and meaningless otherwise.
    """

    signature: str
    tie: str
    params: dict[str, ParamValue] = field(default_factory=dict[str, ParamValue])
    select: Select | None = None


@dataclass(frozen=True, slots=True)
class Behaviour:
    """A named stochastic process attached to a kind.

    ``action_map`` sends each state of ``process`` to an Action, or to None for a silent
    state. It is inline or a resource name.
    """

    name: str
    process: SemiMarkov
    action_map: dict[str, Action | None] | str


@dataclass(frozen=True, slots=True)
class ActorKind:
    """A type of participant: what it serves, whom it may reach, how it behaves, where it runs.

    A kind that ``forwards`` is a router in the RFC 1812 sense: a host that passes packets
    between the segments it is attached to. Routing is derived from that (``tiergen.core.routing``).
    """

    name: str
    serves: tuple[Endpoint, ...]
    ties: tuple[Tie, ...]
    behaviours: tuple[Behaviour, ...]
    platforms: tuple[Platform, ...]
    forwards: bool = False


@dataclass(frozen=True, slots=True)
class Host:
    """Where instances of a kind run.

    ``backend`` is the id of the infrastructure backend that provides the host: "docker",
    "libvirt". ``ref`` is "default", "image:<ref>" or "template:<ref>". ``manifest`` names a
    resource listing the endpoints a custom host serves; None for a default host, and for a
    custom host whose kind serves nothing.
    """

    platform: Platform
    host_type: HostType
    backend: str
    ref: str
    manifest: str | None


@dataclass(frozen=True, slots=True)
class ImplSelection:
    """Which implementations run ``signature``.

    ``choices`` maps "impl_id" or "impl_id:variant" to a weight, sampled per instance. It is
    inline or a resource name.
    """

    signature: str
    choices: dict[str, float] | str


@dataclass(frozen=True, slots=True)
class Binding:
    """For one kind in a scenario: its host and its implementation selections.

    ``mac_oui`` is the first three octets of the MAC addresses its instances get, as
    ``"3c:ec:ef"``, which ``fit`` can measure from DHCP or ARP; None leaves the substrate's
    own prefix, which a sensor can fingerprint, so check 7 reports it. ``credentials`` names
    an opaque resource with the domain, accounts and secrets the kind's implementations use;
    its shape is the implementations' business, not the IR's.
    """

    kind: str
    host: Host
    impls: tuple[ImplSelection, ...]
    mac_oui: str | None = None
    credentials: str | None = None


@dataclass(frozen=True, slots=True)
class ScheduleEvent:
    """A timed control event.

    ``target`` is a group path (every instance under it), ``path/kind`` (every instance of
    that kind under it) or ``path/kind[i]`` (one instance).
    """

    at_s: float
    target: str
    op: ScheduleOp
    arg: str | float | None


@dataclass(frozen=True, slots=True)
class SensorSpec:
    """One configured sensor.

    ``name`` is unique among the scenario's sensors and is what flow ids and labels are keyed
    by; one implementation may be configured twice (offline and live). ``config`` names the
    resource holding the exact configuration used on both real and generated traffic.
    ``capabilities`` are Capability names this configuration declares. A ``role`` of "fit"
    or "both" marks the sensor the model was fitted from.
    """

    name: str
    impl: str
    version: str
    config: str
    mode: SensorMode
    capabilities: tuple[str, ...]
    role: SensorRole


@dataclass(frozen=True, slots=True)
class FitProvenance:
    """What ``fit`` relied on: the sensor, the capabilities used, each one's measured coverage."""

    sensor: str
    capabilities_used: tuple[str, ...]
    coverage: dict[str, float]


@dataclass(frozen=True, slots=True)
class Segment:
    """One broadcast domain, carrying one IPv4 prefix (RFC 4903), realised as one bridge.

    ``vlan`` is the 802.1Q id the real network gives it, or None if untagged; it is what a
    sensor keys flows by when a trunk is mirrored with its tags. Data-plane segments are
    captured; the management one carries the tool's own traffic and never is. A second
    prefix (IPv6) makes ``cidr`` a tuple when it is needed.
    """

    name: str
    cidr: str
    plane: Plane
    vlan: int | None = None


@dataclass(frozen=True, slots=True)
class CapturePoint:
    """An observation point (RFC 7011): every frame on the named segments.

    One segment is a SPAN of that VLAN or a tap on a shared medium; several is a SPAN of a
    trunk, where a routed flow is seen once per segment it crosses. ``tagged`` says the frames
    reach the sensor with their 802.1Q tags, which decides whether the sensor keys those two
    sightings as one flow or two.
    """

    name: str
    segments: tuple[str, ...]
    tagged: bool = False


@dataclass(frozen=True, slots=True)
class Topology:
    """The segments of a scenario. Who joins which is said per group.

    Every instance joins the management network, which carries the tool's own traffic; that
    attachment is implicit. Addresses are allocated from each network's CIDR in a fixed order
    (see ``tiergen.core.addressing``). ``addresses`` overrides the allocation for single
    instances, keyed by instance id, which is how ``fit`` keeps the addresses it observed.
    """

    segments: tuple[Segment, ...]
    capture_points: tuple[CapturePoint, ...]
    addresses: dict[str, str] = field(default_factory=dict[str, str])


@dataclass(frozen=True, slots=True)
class Group:
    """A scope that holds instances: a team, a branch, a site. Groups nest.

    A group's path is its ancestors' names and its own joined by ``/``; ``parent`` is the
    enclosing group's path, or None at the top. An instance is ``path/kind[i]``.
    ``instances`` counts each kind here; ``attachments`` lists the data-plane segments each
    kind's instances join here, one interface each. ``wiring`` says, for each tie of each
    kind held here as ``"kind.tie"``, which groups' instances of the tie's target kind are
    its targets.
    Wiring is explicit and total: nothing is looked up by walking the tree, and nothing is
    inherited from a parent. What the IR says is what connects.
    """

    name: str
    parent: str | None
    instances: dict[str, int]
    attachments: dict[str, tuple[str, ...]]
    wiring: dict[str, tuple[str, ...]] = field(default_factory=dict[str, tuple[str, ...]])

    @property
    def path(self) -> str:
        return self.name if self.parent is None else f"{self.parent}/{self.name}"


@dataclass(frozen=True, slots=True)
class Scenario:
    """The root of the IR.

    ``topology`` is inline or a resource name. ``capture_points`` names the capture points
    of the topology that are active in this run. ``start`` is the run's wall-clock origin as
    ISO 8601 with an offset, in the target network's local time, so that a 24- or 168-value
    rate curve has an hour and a weekday to anchor to. ``egress_overrides`` maps a hostname or
    service to a real endpoint. ``fit_provenance`` is inline, a resource name, or None when
    the scenario was not fitted. ``coverage_floor`` is the measured coverage below which a
    capability ``fit`` relied on is reported as sparse.
    """

    name: str
    kinds: tuple[ActorKind, ...]
    groups: tuple[Group, ...]
    bindings: tuple[Binding, ...]
    topology: Topology | str
    egress: EgressPolicy
    egress_overrides: dict[str, str]
    schedule: tuple[ScheduleEvent, ...]
    start: str
    duration_s: float
    capture_points: tuple[str, ...]
    sensors: tuple[SensorSpec, ...]
    fit_provenance: FitProvenance | str | None
    seed: int
    coverage_floor: float = 0.5

    def to_json(self) -> JsonValue:
        return to_json(self)

    @staticmethod
    def from_json(data: JsonValue) -> "Scenario":
        return from_json(Scenario, data)
