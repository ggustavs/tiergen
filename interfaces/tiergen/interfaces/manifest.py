"""The run manifest: what one infrastructure backend has to realise for one run.

``tiergen build`` writes one manifest per backend a scenario's bindings name, from the IR,
the address plan and the implementation manifests. It is the whole contract between the
build and a backend: a backend reads nothing else, so what ran is reproducible from the
run directory alone. Instances are named by their ids, ``path/kind[i]``.
"""

from dataclasses import dataclass

from tiergen.core.ir import Plane


@dataclass(frozen=True, slots=True)
class NetworkSpec:
    """One network to create. ``gateway`` is the planned gateway address, set explicitly so
    the plan and the substrate agree by construction. ``internal`` networks reach nothing
    outside the run."""

    name: str
    cidr: str
    gateway: str
    plane: Plane
    internal: bool


@dataclass(frozen=True, slots=True)
class Attachment:
    """One network a host joins, with its planned address. Order is attach order."""

    network: str
    address: str


@dataclass(frozen=True, slots=True)
class HostSpec:
    """One host to create. ``image`` is what the backend runs, ``command`` what it runs in
    it, ``cap_add`` the host capabilities the chosen implementations need, as the substrate
    names them."""

    instance: str
    kind: str
    image: str
    command: tuple[str, ...]
    cap_add: tuple[str, ...]
    attachments: tuple[Attachment, ...]


@dataclass(frozen=True, slots=True)
class RunManifest:
    """Everything one backend realises for the run named ``run``."""

    run: str
    backend: str
    networks: tuple[NetworkSpec, ...]
    hosts: tuple[HostSpec, ...]
