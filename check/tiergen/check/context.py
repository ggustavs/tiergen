"""What every check is given, and how it reads a field that may name a resource."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, cast

from tiergen.core.codec import CodecError, decode
from tiergen.core.ir import (
    Action,
    ActorKind,
    Behaviour,
    Binding,
    Distribution,
    Endpoint,
    FitProvenance,
    Host,
    ImplSelection,
    Scenario,
    SemiMarkov,
)
from tiergen.core.resources import Resources
from tiergen.impls._base import ImplDescriptor
from tiergen.interfaces import SensorDescriptor
from tiergen.protocols import Signature

Floats = tuple[float, ...]


@dataclass(frozen=True, slots=True)
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
    signatures: Mapping[str, Signature]

    def resolve(self, value: object, tp: Any) -> Any:
        """``value`` itself if inline; the decoded resource if it is a name; else None."""
        if not isinstance(value, str):
            return value
        try:
            return decode(tp, self.resources.get(value))
        except (KeyError, CodecError):
            return None

    def states(self, p: SemiMarkov) -> tuple[str, ...] | None:
        return cast(tuple[str, ...] | None, self.resolve(p.states, tuple[str, ...]))

    def initial(self, p: SemiMarkov) -> Floats | None:
        return cast(Floats | None, self.resolve(p.initial, Floats))

    def transitions(self, p: SemiMarkov) -> tuple[Floats, ...] | None:
        return cast(tuple[Floats, ...] | None, self.resolve(p.transitions, tuple[Floats, ...]))

    def dwell(self, p: SemiMarkov) -> tuple[Distribution, ...] | None:
        return cast(
            tuple[Distribution, ...] | None, self.resolve(p.dwell, tuple[Distribution, ...])
        )

    def rate(self, p: SemiMarkov) -> Floats | None:
        return None if p.rate is None else cast(Floats | None, self.resolve(p.rate, Floats))

    def action_map(self, b: Behaviour) -> dict[str, Action | None] | None:
        return cast(
            dict[str, Action | None] | None, self.resolve(b.action_map, dict[str, Action | None])
        )

    def choices(self, s: ImplSelection) -> dict[str, float] | None:
        return cast(dict[str, float] | None, self.resolve(s.choices, dict[str, float]))

    def host_manifest(self, h: Host) -> tuple[Endpoint, ...] | None:
        if h.manifest is None:
            return None
        return cast(tuple[Endpoint, ...] | None, self.resolve(h.manifest, tuple[Endpoint, ...]))

    def provenance(self) -> FitProvenance | None:
        return cast(FitProvenance | None, self.resolve(self.scenario.fit_provenance, FitProvenance))

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
