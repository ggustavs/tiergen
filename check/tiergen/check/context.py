"""What every check is given, and how it reads a field that may name a resource."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from tiergen.core.ir import (
    Action,
    ActorKind,
    Behaviour,
    Binding,
    Choice,
    ChoiceRef,
    Distribution,
    Endpoint,
    FitProvenance,
    Host,
    ImplSelection,
    Scenario,
    SemiMarkov,
    Topology,
)
from tiergen.core.resolve import Floats, Resolver
from tiergen.core.resources import Resources
from tiergen.impls._base import ImplDescriptor
from tiergen.interfaces import InfraDescriptor, SensorDescriptor
from tiergen.protocols import Signature


@dataclass(frozen=True)
class Context:
    """A scenario and everything it is checked against.

    Each accessor returns the field's value, fetched and decoded if the field names a
    resource, or None if that resource is missing or ill shaped. Check 5 reports those
    once; every other check treats None as "nothing to say here".
    """

    scenario: Scenario
    resources: Resources
    impls: Mapping[str, ImplDescriptor]
    sensors: Mapping[str, SensorDescriptor]
    infra: Mapping[str, InfraDescriptor]
    signatures: Mapping[str, Signature]

    resolver: Resolver = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "resolver", Resolver(self.resources))

    def resolve(self, value: object, tp: Any) -> Any:
        return self.resolver.resolve(value, tp)

    def states(self, p: SemiMarkov) -> tuple[str, ...] | None:
        return self.resolver.states(p)

    def initial(self, p: SemiMarkov) -> Floats | None:
        return self.resolver.initial(p)

    def transitions(self, p: SemiMarkov) -> tuple[Floats, ...] | None:
        return self.resolver.transitions(p)

    def dwell(self, p: SemiMarkov) -> tuple[Distribution, ...] | None:
        return self.resolver.dwell(p)

    def rate(self, p: SemiMarkov) -> Floats | None:
        return self.resolver.rate(p)

    def action_map(self, b: Behaviour) -> dict[str, Action | None] | None:
        return self.resolver.action_map(b)

    def choice(self, value: Choice | ChoiceRef) -> Choice | None:
        return self.resolver.choice(value)

    def choices(self, s: ImplSelection) -> dict[str, float] | None:
        return self.resolver.choices(s)

    def host_manifest(self, h: Host) -> tuple[Endpoint, ...] | None:
        return self.resolver.host_manifest(h)

    def provenance(self) -> FitProvenance | None:
        return self.resolver.provenance(self.scenario)

    def topology(self) -> Topology | None:
        return self.resolver.topology(self.scenario)

    def held(self, kind: str) -> int:
        """How many instances of ``kind`` the scenario's groups hold in all."""
        return sum(max(g.instances.get(kind, 0), 0) for g in self.scenario.groups)

    def kind(self, name: str) -> ActorKind | None:
        return next((k for k in self.scenario.kinds if k.name == name), None)

    def binding(self, kind: str) -> Binding | None:
        return next((b for b in self.scenario.bindings if b.kind == kind), None)

    def actions(self, kind: ActorKind) -> list[tuple[str, Action]]:
        """Every non-silent action of ``kind``, with the IR path of its action map entry."""
        found: list[tuple[str, Action]] = []
        k = self.scenario.kinds.index(kind)
        for b, behaviour in enumerate(kind.behaviours):
            for state, act in (self.action_map(behaviour) or {}).items():
                if act is not None:
                    found.append((f"kinds[{k}].behaviours[{b}].action_map[{state!r}]", act))
        return found
