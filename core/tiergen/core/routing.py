"""Routing, derived from the IR: which hosts forward, and how every instance reaches every segment.

Nothing here is declared in a scenario. A forwarder is an instance of a kind that
``forwards`` (RFC 1812: a host that passes packets between its interfaces). Segments are
adjacent when a forwarder is on both; every instance gets one static route per data
segment it is not on but can reach, via the forwarder on one of its own segments that
starts a shortest path. Two forwarders that both start a shortest path to the same
destination make the next hop ambiguous, which is a problem rather than a guess. The
management segment is never routed: every instance is on it, and nothing forwards between
it and the data plane. ``reachable`` is what check 10 asks of every wired tie: the Header
Space Analysis fixpoint, specialised to IP over this graph.
"""

from collections import defaultdict, deque
from dataclasses import dataclass

from tiergen.core.addressing import AddressPlan
from tiergen.core.groups import instance_ids
from tiergen.core.ir import Scenario, Topology


@dataclass(frozen=True, slots=True)
class Route:
    """Reach ``segment`` (its CIDR) via the forwarder at ``via``, an address on ``out``."""

    segment: str
    cidr: str
    via: str
    out: str


@dataclass(frozen=True, slots=True)
class RouteProblem:
    path: str
    message: str


@dataclass(frozen=True, slots=True)
class RoutePlan:
    """``routes[instance]`` in segment order; ``forwarders`` the instances that forward."""

    routes: dict[str, tuple[Route, ...]]
    forwarders: tuple[str, ...]


def forwarders(scenario: Scenario) -> list[str]:
    forwarding = {k.name for k in scenario.kinds if k.forwards}
    return [instance for _, kind, instance in instance_ids(scenario) if kind in forwarding]


def _segments_of(plan: AddressPlan, instance: str, data: set[str]) -> list[str]:
    return [s for s in plan.addresses.get(instance, {}) if s in data]


def _distances(start: str, adjacent: dict[str, set[str]]) -> dict[str, int]:
    """Hops from ``start`` to every segment reachable through forwarders."""
    seen = {start: 0}
    queue = deque([start])
    while queue:
        here = queue.popleft()
        for there in adjacent[here]:
            if there not in seen:
                seen[there] = seen[here] + 1
                queue.append(there)
    return seen


def plan_routes(
    scenario: Scenario, topology: Topology, plan: AddressPlan
) -> tuple[RoutePlan, list[RouteProblem]]:
    """Static routes for every instance, and what stops some from existing.

    An instance that cannot reach a segment simply has no route to it; whether that matters
    is check 10's question per tie.
    """
    data = {seg.name for seg in topology.segments if seg.plane == "data"}
    cidr = {seg.name: seg.cidr for seg in topology.segments}
    fwd = forwarders(scenario)
    attached = {f: _segments_of(plan, f, data) for f in fwd}
    adjacent: defaultdict[str, set[str]] = defaultdict(set)
    for s in data:
        adjacent[s]
    for segs in attached.values():
        for s in segs:
            adjacent[s].update(x for x in segs if x != s)
    distance = {s: _distances(s, adjacent) for s in data}

    problems: list[RouteProblem] = []
    routes: dict[str, tuple[Route, ...]] = {}
    for _, _, instance in instance_ids(scenario):
        mine = _segments_of(plan, instance, data)
        reachable_from_me = {d for s in mine for d in distance[s]} - set(mine)
        found: list[Route] = []
        for dest in sorted(reachable_from_me):
            # Candidate first hops: a forwarder on one of my segments, and the segment of its
            # that gets closest to the destination. Shortest total wins; a tie is ambiguous.
            best: dict[str, tuple[str, int]] = {}  # forwarder -> (my segment it is on, hops)
            for f, segs in attached.items():
                if f == instance:
                    continue
                for out in segs:
                    if out not in mine:
                        continue
                    hops = min((distance[s].get(dest, 10**9) for s in segs), default=10**9)
                    if hops < best.get(f, ("", 10**9))[1]:
                        best[f] = (out, hops)
            if not best:
                continue
            shortest = min(h for _, h in best.values())
            winners = sorted(f for f, (_, h) in best.items() if h == shortest)
            if len(winners) > 1:
                problems.append(
                    RouteProblem(
                        f"routes[{instance!r}]",
                        f"{instance} has {len(winners)} equally short next hops to {dest!r} "
                        f"({', '.join(winners)}); a route must be unique",
                    )
                )
                continue
            via = winners[0]
            out = best[via][0]
            found.append(Route(dest, cidr[dest], plan.addresses[via][out], out))
        routes[instance] = tuple(found)
    return RoutePlan(routes, tuple(fwd)), problems


def reachable(
    plan: AddressPlan, routes: RoutePlan, source: str, target: str, data: set[str]
) -> bool:
    """``source`` can send to ``target`` on the data plane: a shared segment, or a route."""
    mine = set(_segments_of(plan, source, data))
    theirs = set(_segments_of(plan, target, data))
    if mine & theirs:
        return True
    return any(r.segment in theirs for r in routes.routes.get(source, ()))
