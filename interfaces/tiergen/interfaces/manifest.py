"""The run manifest: what one infrastructure backend has to realise for one run.

``tiergen build`` writes one manifest per backend a scenario's bindings name, from the IR,
the address plan and the implementation manifests. It is the whole contract between the
build and a backend: a backend reads nothing else, so what ran is reproducible from the
run directory alone. Instances are named by their ids, ``path/kind[i]``.
"""

from dataclasses import dataclass, field

from tiergen.core.ir import Plane, Platform


@dataclass(frozen=True, slots=True)
class NetworkSpec:
    """One segment to create as a network. ``gateway`` is the substrate's own address on it,
    set explicitly so the plan and the substrate agree by construction. ``internal`` networks
    reach nothing outside the run. ``bridge`` is the Linux bridge's name, fixed by ``build``
    so that every backend realising this segment attaches to the same bridge."""

    name: str
    cidr: str
    gateway: str
    plane: Plane
    internal: bool
    bridge: str


@dataclass(frozen=True, slots=True)
class Attachment:
    """One network a host joins, with its planned address and, when the binding gave an OUI,
    its planned MAC. Order is attach order."""

    network: str
    address: str
    mac: str | None = None


@dataclass(frozen=True, slots=True)
class RouteSpec:
    """A static route the host installs: ``cidr`` via ``via``."""

    cidr: str
    via: str


@dataclass(frozen=True, slots=True)
class HostSpec:
    """One host to create. ``image`` is what the backend runs, ``command`` what it runs in
    it, ``cap_add`` the host capabilities the chosen implementations need, as the substrate
    names them. ``forwards`` makes the host a router; ``routes`` are installed after it
    starts, and need the substrate's route-adding capability, which the backend adds.
    ``agent`` says the host runs the platform's agent, which the backend gives the run
    directory and whatever the agent needs of the host: the mounts, the cgroup namespace
    and the capability to write it. ``gate`` is the path inside such a host whose creation
    releases its agent: the host runs from ``up``, services and all, and its behaviours
    start when the backend's ``start`` creates the gate, so attribution and capture can be
    in place before the first invocation."""

    instance: str
    kind: str
    platform: Platform
    hostname: str
    image: str
    command: tuple[str, ...]
    cap_add: tuple[str, ...]
    attachments: tuple[Attachment, ...]
    routes: tuple[RouteSpec, ...] = ()
    forwards: bool = False
    agent: bool = False
    gate: str | None = None


@dataclass(frozen=True, slots=True)
class RunManifest:
    """Everything one backend realises for the run named ``run``."""

    run: str
    backend: str
    networks: tuple[NetworkSpec, ...]
    hosts: tuple[HostSpec, ...]


@dataclass(frozen=True, slots=True)
class HostState:
    """What the substrate called a host once it existed: its name there, and its id."""

    name: str
    id: str


@dataclass(frozen=True, slots=True)
class RunState:
    """What ``up`` created, by instance id and by segment: what attribution and capture need
    to find the substrate's objects, and the id of every image the run's hosts were created
    from, by the name the manifest used. ``down`` does not read it; labels suffice there."""

    run: str
    backend: str
    hosts: dict[str, HostState] = field(default_factory=dict[str, HostState])
    bridges: dict[str, str] = field(default_factory=dict[str, str])
    images: dict[str, str] = field(default_factory=dict[str, str])
