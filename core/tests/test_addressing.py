from dataclasses import replace
from ipaddress import ip_address, ip_network

from hypothesis import given, settings
from hypothesis import strategies as st

from tiergen.core import ir
from tiergen.core.addressing import AddressPlan, plan_addresses
from tiergen.core.codec import from_json, to_json
from tiergen.core.dsl import group, kind, scenario, segment, topology
from tiergen.core.groups import instance_ids

LAN = segment("lan", "10.0.0.0/24")
DMZ = segment("dmz", "10.0.1.0/28")
MGMT = segment("mgmt", "10.9.0.0/24", "management")
CLI = kind("cli", platforms=["linux"])
SRV = kind("srv", platforms=["linux"])


def _scenario(
    cli: int = 3,
    srv: int = 2,
    cli_nets: list[ir.Segment] | None = None,
    srv_nets: list[ir.Segment] | None = None,
) -> ir.Scenario:
    g = group(
        "g",
        instances={CLI: cli, SRV: srv},
        attachments={CLI: cli_nets or [LAN], SRV: srv_nets or [LAN, DMZ]},
    )
    return scenario(
        "s",
        groups=[g],
        bindings={},
        topology="unused",
        egress="none",
        start="2026-10-05T08:00:00+02:00",
        duration_s=1,
        capture_points=[],
        sensors=[],
        seed=0,
    )


TOPOLOGY = topology([LAN, DMZ, MGMT])


def test_allocation_order_is_kinds_then_instances_after_the_gateway() -> None:
    plan, problems = plan_addresses(_scenario(), TOPOLOGY)
    assert problems == []
    assert plan.gateways == {"lan": "10.0.0.1", "dmz": "10.0.1.1", "mgmt": "10.9.0.1"}
    assert plan.addresses["g/cli[0]"] == {"lan": "10.0.0.2", "mgmt": "10.9.0.2"}
    assert plan.addresses["g/cli[2]"] == {"lan": "10.0.0.4", "mgmt": "10.9.0.4"}
    assert plan.addresses["g/srv[0]"] == {"lan": "10.0.0.5", "dmz": "10.0.1.2", "mgmt": "10.9.0.5"}
    assert plan.addresses["g/srv[1]"] == {"lan": "10.0.0.6", "dmz": "10.0.1.3", "mgmt": "10.9.0.6"}


def test_groups_are_allocated_in_order_before_kinds() -> None:
    a = group("a", instances={CLI: 1, SRV: 1}, attachments={CLI: [LAN], SRV: [LAN]})
    b = group("b", instances={CLI: 1}, attachments={CLI: [LAN]}, parent=a)
    s = scenario(
        "s",
        groups=[a, b],
        bindings={},
        topology="unused",
        egress="none",
        start="2026-10-05T08:00:00+02:00",
        duration_s=1,
        capture_points=[],
        sensors=[],
        seed=0,
    )
    plan, problems = plan_addresses(s, topology([LAN, MGMT]))
    assert problems == []
    assert [(i, nets["lan"]) for i, nets in plan.addresses.items()] == [
        ("a/cli[0]", "10.0.0.2"),
        ("a/srv[0]", "10.0.0.3"),
        ("a/b/cli[0]", "10.0.0.4"),
    ]


def test_a_pin_is_kept_and_allocation_flows_around_it() -> None:
    pinned = replace(TOPOLOGY, addresses={"g/srv[0]": "10.0.0.3", "g/cli[1]": "10.9.0.200"})
    plan, problems = plan_addresses(_scenario(), pinned)
    assert problems == []
    assert plan.addresses["g/srv[0]"]["lan"] == "10.0.0.3"
    assert plan.addresses["g/cli[1]"]["mgmt"] == "10.9.0.200"
    assert [plan.addresses[f"g/cli[{i}]"]["lan"] for i in range(3)] == [
        "10.0.0.2",
        "10.0.0.4",
        "10.0.0.5",
    ]


def test_the_plan_is_data() -> None:
    plan, _ = plan_addresses(_scenario(), TOPOLOGY)
    assert from_json(AddressPlan, to_json(plan)) == plan


def test_problems_are_reported_and_the_rest_is_still_planned() -> None:
    broken = ir.Topology(
        (
            LAN,
            ir.Segment("lan", "10.5.0.0/24", "data"),
            ir.Segment("bad", "10.0.0.7/24", "data"),
            MGMT,
        ),
        (),
        {
            "g/ghost[0]": "10.0.0.9",
            "g/cli[0]": "not-an-ip",
            "g/cli[1]": "192.168.0.5",
            "g/cli[2]": "10.0.0.1",
            "g/srv[0]": "10.0.0.255",
        },
    )
    plan, problems = plan_addresses(_scenario(srv_nets=[LAN]), broken)
    found = {p.path: p.message for p in problems}
    assert "defined twice" in found["segments[1].name"]
    assert "is not a prefix" in found["segments[2].cidr"]
    assert "not an instance" in found["addresses['g/ghost[0]']"]
    assert "is not an address" in found["addresses['g/cli[0]']"]
    assert "none of the networks" in found["addresses['g/cli[1]']"]
    assert "already taken" in found["addresses['g/cli[2]']"]  # the gateway
    assert "not a host address" in found["addresses['g/srv[0]']"]
    assert len(found) == 7
    assert plan.addresses["g/cli[0]"]["lan"] == "10.0.0.2"


def test_a_network_that_is_too_small() -> None:
    small = segment("lan", "10.0.0.0/29")
    s = _scenario(cli=4, srv=2, cli_nets=[small], srv_nets=[small])
    _, problems = plan_addresses(s, topology([small, MGMT]))
    [p] = problems
    assert "room for 5 hosts; 6 are attached" in p.message
    p2p = segment("p2p", "10.0.0.0/31")
    _, problems = plan_addresses(_scenario(cli_nets=[p2p], srv_nets=[]), topology([p2p]))
    assert "no room for hosts" in problems[0].message


def test_instances_with_a_negative_count_are_none() -> None:
    s = _scenario()
    s = replace(s, groups=(replace(s.groups[0], instances={"cli": -2, "srv": 1}),))
    assert instance_ids(s) == [("g", "srv", "g/srv[0]")]


@given(
    cli=st.integers(0, 40),
    srv=st.integers(0, 40),
    prefix=st.integers(24, 29),
    pins=st.dictionaries(st.integers(0, 39), st.integers(2, 250), max_size=5),
)
@settings(max_examples=150, deadline=None)
def test_plan_properties(cli: int, srv: int, prefix: int, pins: dict[int, int]) -> None:
    lan = segment("lan", f"10.0.0.0/{prefix}")
    addresses = {f"g/cli[{i}]": f"10.0.0.{host}" for i, host in pins.items()}
    top = topology([lan, MGMT], addresses=addresses)
    s = _scenario(cli, srv, cli_nets=[lan], srv_nets=[lan])
    plan, problems = plan_addresses(s, top)

    assert plan_addresses(s, top) == (plan, problems)  # deterministic
    for name, cidr in (("lan", lan.cidr), ("mgmt", "10.9.0.0/24")):
        held = [nets[name] for nets in plan.addresses.values() if name in nets]
        assert len(held) == len(set(held))  # no collisions
        assert plan.gateways[name] not in held
        assert all(ip_address(a) in ip_network(cidr) for a in held)
    for key, pinned in addresses.items():  # a pin is honoured or reported, never moved
        honoured = plan.addresses.get(key, {}).get("lan") == pinned
        reported = any(p.path == f"addresses[{key!r}]" for p in problems)
        assert honoured != reported
    if not problems:
        assert all(set(nets) == {"lan", "mgmt"} for nets in plan.addresses.values())
        assert len(plan.addresses) == cli + srv


@st.composite
def group_trees(draw: st.DrawFn) -> list[ir.Group]:
    """Up to seven groups in a tree of depth at most three, each holding a few cli and srv on
    the shared lan, in an order where every parent comes before its children."""
    count = draw(st.integers(1, 7))
    groups: list[ir.Group] = []
    for i in range(count):
        parent = None if i == 0 else draw(st.sampled_from([None, *[g.path for g in groups]]))
        depth = 0 if parent is None else parent.count("/") + 1
        if depth > 2:
            parent = None
        held = {"cli": draw(st.integers(0, 4)), "srv": draw(st.integers(0, 2))}
        groups.append(ir.Group(f"g{i}", parent, held, {"cli": ("lan",), "srv": ("lan",)}, {}))
    return groups


@given(groups=group_trees(), pin=st.integers(2, 200))
@settings(max_examples=100, deadline=None)
def test_plan_over_a_group_tree(groups: list[ir.Group], pin: int) -> None:
    s = replace(_scenario(), groups=tuple(groups))
    ids = [i for _, _, i in instance_ids(s)]
    addresses = {ids[0]: f"10.0.0.{pin}"} if ids else {}
    plan, problems = plan_addresses(s, topology([LAN, MGMT], addresses=addresses))
    assert problems == []
    assert list(plan.addresses) == ids  # plan order is instance order, groups first
    held = [nets["lan"] for nets in plan.addresses.values()]
    assert len(held) == len(set(held))
    assert all(ip_address(a) in ip_network(LAN.cidr) for a in held)
    if ids:
        assert plan.addresses[ids[0]]["lan"] == f"10.0.0.{pin}"
