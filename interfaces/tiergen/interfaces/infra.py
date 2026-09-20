"""The infrastructure backend interface. No implementation lives in this package.

The method set is the smallest the M0 checker and the M1 scheduler need; M1's first
backends will refine it.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from tiergen.core.ir import HostType, Platform, Scenario


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


class InfraBackend(Protocol):
    """Brings a scenario's hosts and networks up and down on some substrate."""

    @property
    def id(self) -> str:
        """The backend id: "docker", "libvirt"."""
        ...

    def platforms(self) -> frozenset[tuple[Platform, HostType]]:
        """The (platform, host type) pairs this backend can provide."""
        ...

    def grantable(self, platform: Platform, host_type: HostType) -> frozenset[str]:
        """Host capabilities, such as "net_raw", this backend can grant on such a host."""
        ...

    def plan(self, scenario: Scenario, run_dir: Path) -> None:
        """Write the manifests for ``scenario`` under ``run_dir``. Starts nothing."""
        ...

    def up(self, run_dir: Path) -> None:
        """Start everything ``plan`` described. The management network is never captured."""
        ...

    def down(self, run_dir: Path) -> None:
        """Stop and remove everything ``up`` started."""
        ...
