"""Check 10: the address plan is complete and collision-free, and everyone is on the data plane.

The plan is ``tiergen.core.addressing.plan_addresses``; this check reports what stops it. It
also holds attachments to real kinds and data-plane networks. That a backend can provide each
bound host is check 7's. The two egress clauses wait for fitted external destinations (M4).
"""

from collections.abc import Iterator
from ipaddress import ip_network
from itertools import combinations

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error, not_computed
from tiergen.core.addressing import plan_addresses

ID = "C10"


def check(ctx: Context) -> Iterator[Diagnostic]:
    s = ctx.scenario
    topology = ctx.topology()
    if topology is None:
        return  # check 5 reports a topology that does not resolve
    planes = {net.name: net.plane for net in topology.networks}
    kinds = {kind.name for kind in s.kinds}

    _, problems = plan_addresses(s, topology)
    for problem in problems:
        yield error(ID, f"topology.{problem.path}", problem.message)

    data = [net for net in topology.networks if net.plane == "data"]
    for a, b in combinations(data, 2):
        try:
            shared = ip_network(a.cidr).overlaps(ip_network(b.cidr))
        except (ValueError, TypeError):
            continue  # a malformed CIDR is already reported above
        if shared:
            yield error(
                ID,
                "topology.networks",
                f"data-plane networks {a.name!r} ({a.cidr}) and {b.name!r} ({b.cidr}) overlap, "
                "so an address could mean two hosts",
            )

    for kind, networks in topology.attachments.items():
        path = f"topology.attachments[{kind!r}]"
        if kind not in kinds:
            yield error(ID, path, f"{kind!r} is not a kind of this scenario")
        for name in networks:
            if name not in planes:
                yield error(ID, path, f"{name!r} is not a network of this topology")
            elif planes[name] != "data":
                yield error(
                    ID,
                    path,
                    f"{name!r} is the management network; every instance joins it implicitly",
                )
    for k, kind in enumerate(s.kinds):
        joined = [n for n in topology.attachments.get(kind.name, ()) if planes.get(n) == "data"]
        if s.instances.get(kind.name, 0) > 0 and not joined:
            yield error(
                ID,
                f"kinds[{k}]",
                f"kind {kind.name!r} has instances but joins no data-plane network",
            )

    if s.egress != "none":
        yield not_computed(
            ID,
            "egress",
            f"egress is {s.egress!r}: whether an internet stub or an allowlist backs it, and "
            "whether every egress override is a fitted external destination, needs the "
            "destinations fit will emit",
        )
