"""The infrastructure backend interface and its descriptor. No implementation lives here."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from tiergen.core.ir import HostType, Platform
from tiergen.interfaces.manifest import RunManifest, RunState


class BackendError(RuntimeError):
    """A backend could not do what its manifest asked: the substrate is unreachable, refused
    a resource, or lacks an image. The message is the substrate's own, so it can be acted on."""


@dataclass(frozen=True, slots=True)
class HostOffer:
    """One sort of host a backend can provide.

    ``grantable`` is the set of host capabilities, such as "net_raw", the backend can give
    such a host. None means there is nothing to grant: the host owns its kernel, as a VM
    does, and an implementation there has whatever it asks for.
    """

    platform: Platform
    host_type: HostType
    grantable: frozenset[str] | None


@dataclass(frozen=True, slots=True)
class InfraDescriptor:
    """What an infrastructure backend can do, known without running it.

    Registered under the entry-point group ``tiergen.infra``, with the entry-point name
    equal to ``id``. ``Host.backend`` in a scenario names one.
    """

    id: str
    offers: tuple[HostOffer, ...]

    def offer(self, platform: Platform, host_type: HostType) -> HostOffer | None:
        return next(
            (o for o in self.offers if (o.platform, o.host_type) == (platform, host_type)), None
        )


@runtime_checkable
class InfraBackend(Protocol):
    """Brings the hosts and networks of a run manifest up and down on some substrate.

    A backend reads nothing but its manifest, which ``tiergen build`` wrote from the IR, the
    address plan and the implementation manifests. Registered under the entry-point group
    ``tiergen.infra.backends`` as a class with a no-argument constructor, named by ``id``.
    """

    @property
    def id(self) -> str:
        """The descriptor id this backend implements: "docker", "libvirt"."""
        ...

    def up(self, manifest: RunManifest, run_dir: Path) -> RunState:
        """Create the manifest's networks and hosts, start the hosts, install their routes.

        ``run_dir`` is the directory ``tiergen build`` wrote: an agent host reads its program
        from it and writes its records under ``run_dir/out/<instance>``. Returns what was
        created under which substrate names. Every resource also carries the run's label, so
        ``down`` can find it without state. On failure, undo what was created and re-raise;
        a half-up run is never left behind.
        """
        ...

    def down(self, manifest: RunManifest) -> None:
        """Stop and remove everything of this run, whether or not ``up`` completed."""
        ...

    def quiesce(self, manifest: RunManifest, state: RunState) -> None:
        """Make the run's hosts put wire-sized frames on their segments, so a capture sees
        what a sensor on a real wire would: segmentation offloads off on every host
        interface, by whatever means the substrate has. Called before capture starts."""
        ...
