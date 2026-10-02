"""From the IR, the address plan and the implementation manifests to one run manifest per backend.

Pure: the same inputs give the same manifests, which is what makes a run reproducible from
its run directory. Each backend's manifest holds the hosts bound to it and every network
those hosts join; the management network is joined by every host.
"""

from collections.abc import Mapping
from typing import cast

from tiergen.core.addressing import AddressPlan
from tiergen.core.codec import decode
from tiergen.core.groups import instance_ids
from tiergen.core.ir import Host, Scenario, Topology
from tiergen.core.resources import Resources
from tiergen.impls._base import ImplDescriptor
from tiergen.interfaces import Attachment, HostSpec, NetworkSpec, RunManifest

DEFAULT_IMAGE = {
    # A Linux default host is a small Debian that idles until the agent exists.
    # By digest alone: a tag beside a digest is ignored by the daemon and misleads a reader.
    "linux": "debian@sha256:3783cc01769c7b2b1b83a5c5ad96c815348e28ed7da68e2e3687004faa906251",
}
IDLE = ("sleep", "infinity")


def _image_and_command(host: Host) -> tuple[str, tuple[str, ...]]:
    if host.ref == "default":
        return DEFAULT_IMAGE[host.platform], IDLE
    _, _, ref = host.ref.partition(":")
    return ref, ()


def _capabilities(
    choices: Mapping[str, float] | str, impls: Mapping[str, ImplDescriptor], resources: Resources
) -> set[str]:
    if isinstance(choices, str):
        choices = cast(dict[str, float], decode(dict[str, float], resources.get(choices)))
    needed: set[str] = set()
    for choice in choices:
        impl = impls.get(choice.split(":", 1)[0])
        if impl is not None:
            needed.update(c.upper() for c in impl.host.capabilities)
    return needed


def build_manifests(
    scenario: Scenario,
    topology: Topology,
    plan: AddressPlan,
    impls: Mapping[str, ImplDescriptor],
    resources: Resources,
) -> dict[str, RunManifest]:
    """One manifest per backend the scenario's bindings name, keyed by backend id.

    The scenario has passed the checks: every held kind is bound, every binding's backend
    offers its host, every resource resolves, and the plan is complete.
    """
    bindings = {b.kind: b for b in scenario.bindings}
    groups = {g.path: g for g in scenario.groups}
    management = [n.name for n in topology.networks if n.plane == "management"]
    hosts: dict[str, list[HostSpec]] = {}
    for path, kind, instance in instance_ids(scenario):
        binding = bindings[kind]
        image, command = _image_and_command(binding.host)
        cap_add = set[str]()
        for selection in binding.impls:
            cap_add |= _capabilities(selection.choices, impls, resources)
        joined = [*groups[path].attachments.get(kind, ()), *management]
        addresses = plan.addresses[instance]
        hosts.setdefault(binding.host.backend, []).append(
            HostSpec(
                instance=instance,
                kind=kind,
                image=image,
                command=command,
                cap_add=tuple(sorted(cap_add)),
                attachments=tuple(Attachment(n, addresses[n]) for n in joined),
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
            )
            for n in topology.networks
            if n.name in used
        )
        manifests[backend] = RunManifest(scenario.name, backend, networks, tuple(specs))
    return manifests
