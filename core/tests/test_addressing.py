from dataclasses import replace
from ipaddress import ip_address, ip_network

from hypothesis import given, settings
from hypothesis import strategies as st

from tiergen.core import ir
from tiergen.core.addressing import AddressPlan, instance_ids, plan_addresses
from tiergen.core.codec import from_json, to_json
from tiergen.core.dsl import kind, network, scenario, topology

LAN = network("lan", "10.0.0.0/24")
DMZ = network("dmz", "10.0.1.0/28")
MGMT = network("mgmt", "10.9.0.0/24", "management")


def _scenario(cli: int = 3, srv: int = 2) -> ir.Scenario:
    return scenario(
        "s",
        instances={kind("cli", platforms=["linux"]): cli, kind("srv", platforms=["linux"]): srv},
        bindings={},
        topology="unused",
        egress="none",
        duration_s=1,
        capture_points=[],
        sensors=[],
        seed=0,
    )


TOPOLOGY = topology([LAN, DMZ, MGMT], {"cli": [LAN], "srv": [LAN, DMZ]})


def test_allocation_order_is_kinds_then_instances_after_the_gateway() -> None:
    plan, problems = plan_addresses(_scenario(), TOPOLOGY)
    assert problems == []
    assert plan.gateways == {"lan": "10.0.0.1", "dmz": "10.0.1.1", "mgmt": "10.9.0.1"}
    assert plan.addresses["cli[0]"] == {"lan": "10.0.0.2", "mgmt": "10.9.0.2"}
    assert plan.addresses["cli[2]"] == {"lan": "10.0.0.4", "mgmt": "10.9.0.4"}
    assert plan.addresses["srv[0]"] == {"lan": "10.0.0.5", "dmz": "10.0.1.2", "mgmt": "10.9.0.5"}
    assert plan.addresses["srv[1]"] == {"lan": "10.0.0.6", "dmz": "10.0.1.3", "mgmt": "10.9.0.6"}


def test_a_pin_is_kept_and_allocation_flows_around_it() -> None:
    pinned = replace(TOPOLOGY, addresses={"srv[0]": "10.0.0.3", "cli[1]": "10.9.0.200"})
    plan, problems = plan_addresses(_scenario(), pinned)
    assert problems == []
    assert plan.addresses["srv[0]"]["lan"] == "10.0.0.3"
    assert plan.addresses["cli[1]"]["mgmt"] == "10.9.0.200"
    assert [plan.addresses[f"cli[{i}]"]["lan"] for i in range(3)] == [
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
            ir.Network("lan", "10.5.0.0/24", "data"),
            ir.Network("bad", "10.0.0.7/24", "data"),
            MGMT,
        ),
        {"cli": ("lan",), "srv": ("lan",)},
        (),
        {
            "ghost[0]": "10.0.0.9",
            "cli[0]": "not-an-ip",
            "cli[1]": "192.168.0.5",
            "cli[2]": "10.0.0.1",
            "srv[0]": "10.0.0.255",
        },
    )
    plan, problems = plan_addresses(_scenario(), broken)
    found = {p.path: p.message for p in problems}
    assert "defined twice" in found["networks[1].name"]
    assert "is not a network" in found["networks[2].cidr"]
    assert "not an instance" in found["addresses['ghost[0]']"]
    assert "is not an address" in found["addresses['cli[0]']"]
    assert "none of the networks" in found["addresses['cli[1]']"]
    assert "already taken" in found["addresses['cli[2]']"]  # the gateway
    assert "not a host address" in found["addresses['srv[0]']"]
    assert len(found) == 7
    assert plan.addresses["cli[0]"]["lan"] == "10.0.0.2"


def test_a_network_that_is_too_small() -> None:
    tight = topology([network("lan", "10.0.0.0/29"), MGMT], {"cli": ["lan"], "srv": ["lan"]})
    _, problems = plan_addresses(_scenario(cli=4, srv=2), tight)
    [p] = problems
    assert "room for 5 hosts; 6 are attached" in p.message
    _, problems = plan_addresses(
        _scenario(), topology([network("p2p", "10.0.0.0/31")], {"cli": ["p2p"]})
    )
    assert "no room for hosts" in problems[0].message


def test_instances_with_a_negative_count_are_none() -> None:
    assert instance_ids(replace(_scenario(), instances={"cli": -2, "srv": 1})) == [
        ("srv", "srv[0]")
    ]


@given(
    cli=st.integers(0, 40),
    srv=st.integers(0, 40),
    prefix=st.integers(24, 29),
    pins=st.dictionaries(st.integers(0, 39), st.integers(2, 250), max_size=5),
)
@settings(max_examples=150, deadline=None)
def test_plan_properties(cli: int, srv: int, prefix: int, pins: dict[int, int]) -> None:
    lan = f"10.0.0.0/{prefix}"
    addresses = {f"cli[{i}]": f"10.0.0.{host}" for i, host in pins.items()}
    top = topology(
        [network("lan", lan), MGMT], {"cli": ["lan"], "srv": ["lan"]}, addresses=addresses
    )
    s = _scenario(cli, srv)
    plan, problems = plan_addresses(s, top)

    assert plan_addresses(s, top) == (plan, problems)  # deterministic
    for name, cidr in (("lan", lan), ("mgmt", "10.9.0.0/24")):
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
