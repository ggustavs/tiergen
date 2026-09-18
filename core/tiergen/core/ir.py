"""The scenario IR: a finite, first-order description of a run, as data.

Every node is a frozen slotted dataclass built from JSON-shaped values, so a scenario
round-trips through JSON unchanged. Nothing here is callable: signatures, implementations,
sensors and resources are referenced by name.

A field typed ``... | str`` takes either an inline value or the name of a resource that
holds one. A field typed plain ``str`` and documented as a resource is always a name.
Names are resolved by the checker, never here.
"""

from dataclasses import dataclass
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
class Action:
    """What a behaviour state does: run ``signature`` against the peers reached over ``tie``."""

    signature: str
    tie: str


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
    """A type of participant: what it serves, whom it may reach, how it behaves, where it runs."""

    name: str
    serves: tuple[Endpoint, ...]
    ties: tuple[Tie, ...]
    behaviours: tuple[Behaviour, ...]
    platforms: tuple[Platform, ...]


@dataclass(frozen=True, slots=True)
class Host:
    """Where instances of a kind run.

    ``ref`` is "default", "image:<ref>" or "template:<ref>". ``manifest`` names a resource
    listing the endpoints a custom host serves; None for default hosts.
    """

    platform: Platform
    host_type: HostType
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
    """For one kind in a scenario: its host and its implementation selections."""

    kind: str
    host: Host
    impls: tuple[ImplSelection, ...]


@dataclass(frozen=True, slots=True)
class ScheduleEvent:
    """A timed control event. ``target`` is a kind name or ``kind[i]`` for one instance."""

    at_s: float
    target: str
    op: ScheduleOp
    arg: str | float | None


@dataclass(frozen=True, slots=True)
class SensorSpec:
    """One configured sensor.

    ``config`` names the resource holding the exact configuration used on both real and
    generated traffic. ``capabilities`` are Capability names this configuration declares.
    A ``role`` of "fit" or "both" marks the sensor the model was fitted from.
    """

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
class Scenario:
    """The root of the IR.

    ``topology`` names a resource or a builtin. ``egress_overrides`` maps a hostname or
    service to a real endpoint. ``fit_provenance`` is inline, a resource name, or None when
    the scenario was not fitted. ``coverage_floor`` is the measured coverage below which a
    capability ``fit`` relied on is reported as sparse.
    """

    name: str
    kinds: tuple[ActorKind, ...]
    instances: dict[str, int]
    bindings: tuple[Binding, ...]
    topology: str
    egress: EgressPolicy
    egress_overrides: dict[str, str]
    schedule: tuple[ScheduleEvent, ...]
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
