"""The address plan: which address each instance has on each of its networks.

The plan is a function of the IR and nothing else, so the checker can see it before anything
runs and every backend realises the same one. On each network the first usable address is
reserved for a gateway. Pinned addresses (``Topology.addresses``) are placed first. Every
other member then takes the next free address, members in the order of
``tiergen.core.groups.instance_ids``: group, then kind as listed in the scenario, then
index. An allocation order is not a fitted parameter, so fixing one here invents nothing
about the network being modelled.
"""

import hashlib
from dataclasses import dataclass, field
from ipaddress import IPv4Address, IPv4Network, IPv6Address, IPv6Network, ip_address, ip_network

from tiergen.core.groups import instance_ids
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
    """What every instance is called and where it sits on each segment.

    ``addresses[instance][segment]`` is an address; ``gateways[segment]`` is the substrate's
    own address on the segment (the bridge), reserved first. ``hostnames[instance]`` is the
    host's name, the instance id with ``/`` and ``_`` as ``-`` and the index after a dash,
    which is a function of the IR like everything here. ``macs[instance][segment]`` is the
    interface's MAC, present only when the binding gives an OUI: the vendor part is the OUI
    and the rest a hash of the instance and segment. Without an OUI the substrate assigns
    one, and check 7 says so. A segment with a malformed CIDR is absent from everything.
    """

    addresses: dict[str, dict[str, str]]
    gateways: dict[str, str]
    hostnames: dict[str, str] = field(default_factory=dict[str, str])
    macs: dict[str, dict[str, str]] = field(default_factory=dict[str, dict[str, str]])


def hostname(instance: str) -> str:
    """``corp/eng/workstation[3]`` becomes ``corp-eng-workstation-3``."""
    return instance.replace("/", "-").replace("_", "-").replace("[", "-").replace("]", "")


def mac_address(oui: str, instance: str, segment: str) -> str:
    """``oui`` as ``"3c:ec:ef"`` plus three octets hashed from the interface's identity."""
    digest = hashlib.blake2b(f"{instance}@{segment}".encode(), digest_size=3).digest()
    return ":".join([oui.lower(), *(f"{b:02x}" for b in digest)])


def plan_addresses(
    scenario: Scenario, topology: Topology
) -> tuple[AddressPlan, list[AddressProblem]]:
    """The address plan, as far as it can be made, and what is wrong with the rest."""
    problems: list[AddressProblem] = []
    everyone = instance_ids(scenario)
    attached = {
        g.path: {kind: set(nets) for kind, nets in g.attachments.items()} for g in scenario.groups
    }

    parsed: dict[str, _Network] = {}
    members: dict[str, list[str]] = {}
    for n, net in enumerate(topology.segments):
        if net.name in members:
            problems.append(
                AddressProblem(f"segments[{n}].name", f"segment {net.name!r} is defined twice")
            )
            continue
        if net.plane == "management":
            members[net.name] = [instance for _, _, instance in everyone]
        else:
            members[net.name] = [
                instance
                for path, kind, instance in everyone
                if net.name in attached.get(path, {}).get(kind, set())
            ]
        try:
            parsed[net.name] = ip_network(net.cidr, strict=True)
        except ValueError as err:
            problems.append(
                AddressProblem(f"segments[{n}].cidr", f"{net.cidr!r} is not a prefix: {err}")
            )

    gateways: dict[str, _Address] = {}
    for name, network in parsed.items():
        first = next(iter(network.hosts()), None)
        if first is None or network.num_addresses < 4:
            problems.append(
                AddressProblem("segments", f"segment {name!r} ({network}) has no room for hosts")
            )
        else:
            gateways[name] = first
    usable = {name: network for name, network in parsed.items() if name in gateways}

    assigned: dict[str, dict[str, _Address]] = {instance: {} for _, _, instance in everyone}
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
                        "segments",
                        f"segment {name!r} ({network}) has room for {room} hosts; "
                        f"{len(members[name])} are attached",
                    )
                )
                break
            assigned[instance][name] = address

    ouis = {b.kind: b.mac_oui for b in scenario.bindings if b.mac_oui is not None}
    plan = AddressPlan(
        {instance: {n: str(a) for n, a in nets.items()} for instance, nets in assigned.items()},
        {name: str(address) for name, address in gateways.items()},
        {instance: hostname(instance) for _, _, instance in everyone},
        {
            instance: {n: mac_address(ouis[kind], instance, n) for n in assigned[instance]}
            for _, kind, instance in everyone
            if kind in ouis
        },
    )
    return plan, problems
