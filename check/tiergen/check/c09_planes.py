"""Check 9: the management plane and the data plane stay apart, and only the data plane is captured.

The tool's own traffic (agents, scheduler, log collection) runs on the management segment.
If any of it appears in a capture, the dataset represents the tool, not the network.
"""

from collections.abc import Iterator
from ipaddress import ip_network

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error, not_computed

ID = "C09"


def check(ctx: Context) -> Iterator[Diagnostic]:
    s = ctx.scenario
    topology = ctx.topology()
    if topology is None:
        return  # check 5 reports a topology that does not resolve
    planes = {net.name: net.plane for net in topology.segments}

    management = [net for net in topology.segments if net.plane == "management"]
    if len(management) != 1:
        yield error(
            ID,
            "topology.segments",
            f"exactly one management segment is needed; there are {len(management)}",
        )
    for mgmt in management:
        for net in topology.segments:
            if net.plane != "data":
                continue
            try:
                shared = ip_network(mgmt.cidr).overlaps(ip_network(net.cidr))
            except (ValueError, TypeError):
                continue  # check 10 reports a malformed CIDR; mixed IP versions cannot overlap
            if shared:
                yield error(
                    ID,
                    "topology.segments",
                    f"management segment {mgmt.name!r} ({mgmt.cidr}) overlaps data-plane "
                    f"network {net.name!r} ({net.cidr})",
                )

    defined: set[str] = set()
    for c, point in enumerate(topology.capture_points):
        path = f"topology.capture_points[{c}]"
        if point.name in defined:
            yield error(ID, path, f"capture point {point.name!r} is defined twice")
        defined.add(point.name)
        if not point.segments:
            yield error(ID, f"{path}.segments", f"capture point {point.name!r} observes no segment")
        for i, name in enumerate(point.segments):
            if name not in planes:
                yield error(
                    ID, f"{path}.segments[{i}]", f"{name!r} is not a segment of this topology"
                )
            elif planes[name] != "data":
                yield error(
                    ID,
                    f"{path}.segments[{i}]",
                    f"capture point {point.name!r} observes management segment {name!r}; "
                    "a capture there records the tool, not the network",
                )

    if not s.capture_points:
        yield error(
            ID, "capture_points", "no capture point is active, so the run would produce no pcap"
        )
    for c, name in enumerate(s.capture_points):
        if name not in defined:
            yield error(
                ID, f"capture_points[{c}]", f"{name!r} is not a capture point of the topology"
            )

    for i, sensor in enumerate(s.sensors):
        if sensor.mode == "live":
            yield not_computed(
                ID,
                f"sensors[{i}].mode",
                f"{sensor.impl} runs live, and a SensorSpec does not say which interface it "
                "listens on, so whether that interface is data-plane cannot be checked",
            )
