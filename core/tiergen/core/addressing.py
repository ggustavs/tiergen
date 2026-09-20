"""The address plan: which address each instance has on each of its networks.

The plan is a function of the IR and nothing else, so the checker can see it before anything
runs and every backend realises the same one. On each network the first usable address is
reserved for a gateway. Pinned addresses (``Topology.addresses``) are placed first. Every
other member then takes the next free address, members ordered by kind as listed in the
scenario and then by instance index. An allocation order is not a fitted parameter, so
fixing one here invents nothing about the network being modelled.
"""

from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network, ip_address, ip_network

from tiergen.core.ir import Scenario, Topology

type _Network = IPv4Network | IPv6Network
type _Address = IPv4Address | IPv6Address


@dataclass(frozen=True, slots=True)
class AddressProblem:
    """Something that stops the plan from being complete. ``path`` is relative to the topology."""

    path: str
    message: str


@dataclass(frozen=True, slots=True)
class AddressPlan:
    """``addresses[instance][network]`` is an address; ``gateways[network]`` is the reserved one.

    An instance is named ``kind[i]``. A network with a malformed CIDR is absent from both.
    """

    addresses: dict[str, dict[str, str]]
    gateways: dict[str, str]


def instance_ids(scenario: Scenario) -> list[tuple[str, str]]:
    """Every ``(kind, "kind[i]")`` of the scenario, in plan order."""
    return [
        (kind.name, f"{kind.name}[{i}]")
        for kind in scenario.kinds
        for i in range(max(scenario.instances.get(kind.name, 0), 0))
    ]


def plan_addresses(
    scenario: Scenario, topology: Topology
) -> tuple[AddressPlan, list[AddressProblem]]:
    """The address plan, as far as it can be made, and what is wrong with the rest."""
    problems: list[AddressProblem] = []
    everyone = instance_ids(scenario)

    parsed: dict[str, _Network] = {}
    members: dict[str, list[str]] = {}
    for n, net in enumerate(topology.networks):
        if net.name in members:
            problems.append(
                AddressProblem(f"networks[{n}].name", f"network {net.name!r} is defined twice")
            )
            continue
        if net.plane == "management":
            members[net.name] = [instance for _, instance in everyone]
        else:
            members[net.name] = [
                instance
                for kind, instance in everyone
                if net.name in topology.attachments.get(kind, ())
            ]
        try:
            parsed[net.name] = ip_network(net.cidr, strict=True)
        except ValueError as err:
            problems.append(
                AddressProblem(f"networks[{n}].cidr", f"{net.cidr!r} is not a network: {err}")
            )

    gateways: dict[str, _Address] = {}
    for name, network in parsed.items():
        first = next(iter(network.hosts()), None)
        if first is None or network.num_addresses < 4:
            problems.append(
                AddressProblem("networks", f"network {name!r} ({network}) has no room for hosts")
            )
        else:
            gateways[name] = first
    usable = {name: network for name, network in parsed.items() if name in gateways}

    assigned: dict[str, dict[str, _Address]] = {instance: {} for _, instance in everyone}
    taken: dict[str, set[_Address]] = {name: {gateways[name]} for name in usable}
    for key, text in topology.addresses.items():
        path = f"addresses[{key!r}]"
        if key not in assigned:
            problems.append(AddressProblem(path, f"{key!r} is not an instance of this scenario"))
            continue
        try:
            address = ip_address(text)
        except ValueError:
            problems.append(AddressProblem(path, f"{text!r} is not an address"))
            continue
        home = next((n for n, net in usable.items() if key in members[n] and address in net), None)
        if home is None:
            problems.append(AddressProblem(path, f"{text} is on none of the networks {key} joins"))
        elif address in (usable[home].network_address, usable[home].broadcast_address):
            problems.append(AddressProblem(path, f"{text} is not a host address of {home!r}"))
        elif address in taken[home]:
            problems.append(AddressProblem(path, f"{text} is already taken on {home!r}"))
        else:
            assigned[key][home] = address
            taken[home].add(address)

    for name, network in usable.items():
        free = (host for host in network.hosts() if host not in taken[name])
        waiting = [instance for instance in members[name] if name not in assigned[instance]]
        for instance in waiting:
            address = next(free, None)
            if address is None:
                room = network.num_addresses - 3  # network, broadcast, gateway
                problems.append(
                    AddressProblem(
                        "networks",
                        f"network {name!r} ({network}) has room for {room} hosts; "
                        f"{len(members[name])} are attached",
                    )
                )
                break
            assigned[instance][name] = address

    plan = AddressPlan(
        {instance: {n: str(a) for n, a in nets.items()} for instance, nets in assigned.items()},
        {name: str(address) for name, address in gateways.items()},
    )
    return plan, problems
