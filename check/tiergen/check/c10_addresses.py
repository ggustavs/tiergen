"""Check 10: the plans are complete, and every wired tie can carry a packet.

The address plan is ``tiergen.core.addressing.plan_addresses`` and the routes are
``tiergen.core.routing.plan_routes``; this check reports what stops either. It holds each
group's attachments to real kinds and data-plane segments, and every wired tie to
reachability: source and target share a segment, or the source has a route to the
target's segment through forwarders (the Header Space Analysis fixpoint over the segment
graph). That a backend can provide each bound host is check 7's. The two egress clauses
wait for fitted external destinations (M4).
"""

from collections.abc import Iterator
from ipaddress import ip_network
from itertools import combinations

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error, not_computed
from tiergen.core.addressing import plan_addresses
from tiergen.core.groups import instance_ids, targets
from tiergen.core.routing import plan_routes, reachable

ID = "C10"


def check(ctx: Context) -> Iterator[Diagnostic]:
    s = ctx.scenario
    topology = ctx.topology()
    if topology is None:
        return  # check 5 reports a topology that does not resolve
    planes = {net.name: net.plane for net in topology.segments}
    kinds = {kind.name for kind in s.kinds}

    plan, problems = plan_addresses(s, topology)
    for problem in problems:
        yield error(ID, f"topology.{problem.path}", problem.message)
    routes, route_problems = plan_routes(s, topology, plan)
    for problem in route_problems:
        yield error(ID, f"topology.{problem.path}", problem.message)

    data = [net for net in topology.segments if net.plane == "data"]
    for a, b in combinations(data, 2):
        try:
            shared = ip_network(a.cidr).overlaps(ip_network(b.cidr))
        except (ValueError, TypeError):
            continue  # a malformed CIDR is already reported above
        if shared:
            yield error(
                ID,
                "topology.segments",
                f"data-plane segments {a.name!r} ({a.cidr}) and {b.name!r} ({b.cidr}) overlap, "
                "so an address could mean two hosts",
            )

    for g, group in enumerate(s.groups):
        for kind, networks in group.attachments.items():
            path = f"groups[{g}].attachments[{kind!r}]"
            if kind not in kinds:
                yield error(ID, path, f"{kind!r} is not a kind of this scenario")
            for name in networks:
                if name not in planes:
                    yield error(ID, path, f"{name!r} is not a segment of this topology")
                elif planes[name] != "data":
                    yield error(
                        ID,
                        path,
                        f"{name!r} is the management segment; every instance joins it implicitly",
                    )
        for kind, count in group.instances.items():
            joined = [n for n in group.attachments.get(kind, ()) if planes.get(n) == "data"]
            if kind in kinds and count > 0 and not joined:
                yield error(
                    ID,
                    f"groups[{g}].instances[{kind!r}]",
                    f"{group.path!r} holds {kind!r} but attaches it to no data-plane network",
                )

    data = {seg.name for seg in topology.segments if seg.plane == "data"}
    held_by: dict[tuple[str, str], list[str]] = {}
    for path, kind, instance in instance_ids(s):
        held_by.setdefault((path, kind), []).append(instance)
    for g, group in enumerate(s.groups):
        for key in group.wiring:
            kind_name, _, tie_name = key.partition(".")
            sources = held_by.get((group.path, kind_name), [])
            reached = targets(s, group.path, kind_name, tie_name)
            if not sources or reached is None:
                continue  # check 1 reports a wire with nothing on either end
            dead = [
                (src, dst)
                for src in sources
                for dst in reached
                if not reachable(plan, routes, src, dst, data)
            ]
            if dead:
                src, dst = dead[0]
                yield error(
                    ID,
                    f"groups[{g}].wiring[{key!r}]",
                    f"{src} cannot reach {dst}: no shared segment and no route through a "
                    f"forwarder ({len(dead)} such pair(s))",
                )

    if s.egress != "none":
        yield not_computed(
            ID,
            "egress",
            f"egress is {s.egress!r}: whether an internet stub or an allowlist backs it, and "
            "whether every egress override is a fitted external destination, needs the "
            "destinations fit will emit",
        )
