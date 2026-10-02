"""Reading IR fields that may name a resource, in one place.

A field typed ``T | str`` holds its value inline or the name of a resource that holds one.
``Resolver`` turns either into the value, or None when the resource is missing or ill
shaped; check 5 is the one place that reports those, so every other consumer, the checker,
``build`` and the agent alike, treats None as "nothing to say here" and never sees a
resource name it has to interpret itself.
"""

from typing import Any, cast

from tiergen.core.codec import CodecError, decode
from tiergen.core.ir import (
    Action,
    Behaviour,
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
from tiergen.core.resources import Resources

Floats = tuple[float, ...]


class Resolver:
    """Accessors for every resource-bearing field of the IR, over one resource store."""

    def __init__(self, resources: Resources) -> None:
        self.resources = resources

    def resolve[T](self, value: T | str, tp: Any) -> T | None:
        """``value`` itself if inline; the decoded resource if it is a name; else None.

        ``tp`` is the annotation to decode the resource as, which is ``T`` with the ``str``
        arm removed; an annotation is not a ``type``, hence the cast.
        """
        if not isinstance(value, str):
            return value
        try:
            return cast(T, decode(tp, self.resources.get(value)))
        except (KeyError, CodecError):
            return None

    def states(self, p: SemiMarkov) -> tuple[str, ...] | None:
        return self.resolve(p.states, tuple[str, ...])

    def initial(self, p: SemiMarkov) -> Floats | None:
        return self.resolve(p.initial, Floats)

    def transitions(self, p: SemiMarkov) -> tuple[Floats, ...] | None:
        return self.resolve(p.transitions, tuple[Floats, ...])

    def dwell(self, p: SemiMarkov) -> tuple[Distribution, ...] | None:
        return self.resolve(p.dwell, tuple[Distribution, ...])

    def rate(self, p: SemiMarkov) -> Floats | None:
        return None if p.rate is None else self.resolve(p.rate, Floats)

    def action_map(self, b: Behaviour) -> dict[str, Action | None] | None:
        return self.resolve(b.action_map, dict[str, Action | None])

    def choice(self, value: Choice | ChoiceRef) -> Choice | None:
        if isinstance(value, Choice):
            return value
        return self.resolve(value.resource, Choice)

    def choices(self, s: ImplSelection) -> dict[str, float] | None:
        return self.resolve(s.choices, dict[str, float])

    def host_manifest(self, h: Host) -> tuple[Endpoint, ...] | None:
        return None if h.manifest is None else self.resolve(h.manifest, tuple[Endpoint, ...])

    def provenance(self, s: Scenario) -> FitProvenance | None:
        return self.resolve(s.fit_provenance, FitProvenance)

    def topology(self, s: Scenario) -> Topology | None:
        return self.resolve(s.topology, Topology)
