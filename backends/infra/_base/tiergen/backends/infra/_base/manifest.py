"""From the IR, the address plan and the implementation manifests to one run manifest per backend.

Pure: the same inputs give the same manifests, which is what makes a run reproducible from
its run directory. Each backend's manifest holds the hosts bound to it and every network
those hosts join; the management network is joined by every host.
"""

import hashlib
from collections.abc import Mapping

from tiergen.core.addressing import AddressPlan
from tiergen.core.groups import instance_ids
from tiergen.core.ir import Host, HostRef, ImplSelection, Scenario, Topology
from tiergen.core.program import flat_id
from tiergen.core.resolve import Resolver
from tiergen.core.resources import Resources
from tiergen.core.routing import RoutePlan
from tiergen.impls._base import ImplDescriptor, ImplRef
from tiergen.interfaces import Attachment, HostSpec, NetworkSpec, RouteSpec, RunManifest

AGENT_IMAGE = {
    # A default host runs the platform's agent from the backend's own image, named here
    # without a tag: the backend builds or finds it and records the id it ran in the state.
    "linux": "tiergen/base-linux",
}
RUN_MOUNT = "/tiergen/run"
"""Where an agent host sees the run directory."""
GATE = "/tiergen/go"
"""The path inside an agent host whose creation starts its behaviours (``HostSpec.gate``)."""


def agent_command(instance: str) -> tuple[str, ...]:
    return ("tiergen-agent", f"{RUN_MOUNT}/program.{flat_id(instance)}.json", "--go", GATE)


def bridge_name(run: str, segment: str) -> str:
    """The Linux bridge every backend attaches this segment's hosts to: ``tg-`` and twelve
    hex digits of a hash, within the 15-character interface-name limit."""
    return "tg-" + hashlib.blake2b(f"{run}|{segment}".encode(), digest_size=6).hexdigest()


def _image_and_command(host: Host, instance: str) -> tuple[str, tuple[str, ...], bool]:
    """Image, command and whether the host runs the agent: a default host does, from the
    agent image; a custom image runs its own entrypoint."""
    parsed = HostRef.parse(host.ref)
    assert parsed is not None  # check 6 holds the syntax before build gets here
    if parsed.kind == "default":
        return AGENT_IMAGE[host.platform], agent_command(instance), True
    return parsed.ref, (), False


def _capabilities(
    selection: ImplSelection, impls: Mapping[str, ImplDescriptor], resolver: Resolver
) -> set[str]:
    needed: set[str] = set()
    for choice in resolver.choices(selection) or {}:
        impl = impls.get(ImplRef.parse(choice).impl)
        if impl is not None:
            needed.update(c.upper() for c in impl.host.capabilities)
    return needed


def build_manifests(
    scenario: Scenario,
    topology: Topology,
    plan: AddressPlan,
    routes: RoutePlan,
    impls: Mapping[str, ImplDescriptor],
    resources: Resources,
) -> dict[str, RunManifest]:
    """One manifest per backend the scenario's bindings name, keyed by backend id.

    The scenario has passed the checks: every held kind is bound, every binding's backend
    offers its host, every resource resolves, and the plan is complete.
    """
    resolver = Resolver(resources)
    bindings = {b.kind: b for b in scenario.bindings}
    kinds = {k.name: k for k in scenario.kinds}
    groups = {g.path: g for g in scenario.groups}
    management = [n.name for n in topology.segments if n.plane == "management"]
    hosts: dict[str, list[HostSpec]] = {}
    for path, kind, instance in instance_ids(scenario):
        binding = bindings[kind]
        image, command, agent = _image_and_command(binding.host, instance)
        cap_add = set[str]()
        for selection in binding.impls:
            cap_add |= _capabilities(selection, impls, resolver)
        joined = [*groups[path].attachments.get(kind, ()), *management]
        addresses = plan.addresses[instance]
        macs = plan.macs.get(instance, {})
        hosts.setdefault(binding.host.backend, []).append(
            HostSpec(
                instance=instance,
                kind=kind,
                platform=binding.host.platform,
                hostname=plan.hostnames[instance],
                image=image,
                command=command,
                cap_add=tuple(sorted(cap_add)),
                attachments=tuple(Attachment(n, addresses[n], macs.get(n)) for n in joined),
                routes=tuple(RouteSpec(r.cidr, r.via) for r in routes.routes.get(instance, ())),
                forwards=kinds[kind].forwards,
                agent=agent,
                gate=GATE if agent else None,
            )
        )
    manifests: dict[str, RunManifest] = {}
    for backend, specs in hosts.items():
        used = {a.network for h in specs for a in h.attachments}
        networks = tuple(
            NetworkSpec(
                name=n.name,
                cidr=n.cidr,
                gateway=plan.gateways[n.name],
                plane=n.plane,
                internal=n.plane == "data" and scenario.egress == "none",
                bridge=bridge_name(scenario.name, n.name),
            )
            for n in topology.segments
            if n.name in used
        )
        manifests[backend] = RunManifest(scenario.name, backend, networks, tuple(specs))
    return manifests
