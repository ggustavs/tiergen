"""What an implementation package declares about itself, as data.

An ``ImplDescriptor`` is the decoded form of a package's ``impl.toml``. The checker reads
descriptors only; it never imports an implementation's runtime.
"""

from dataclasses import dataclass, field
from typing import Literal

from tiergen.core.ir import Endpoint, Platform

ImplKind = Literal["primitive", "service", "adapter"]
FingerprintRole = Literal["client", "server"]


@dataclass(frozen=True, slots=True)
class HostRequirements:
    """What a host must offer for the implementation to run on it.

    ``capabilities`` are host privileges such as "net_raw". ``image_base`` maps a platform
    to the base image a default host is built from.
    """

    platforms: tuple[Platform, ...]
    binaries: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    image_base: dict[str, str] = field(default_factory=dict[str, str])


@dataclass(frozen=True, slots=True)
class Fingerprint:
    """How the implementation looks on the wire.

    A value of "auto" is a placeholder the package's conformance test replaces with what it
    measures. ``ja4`` is keyed by variant.
    """

    role: FingerprintRole
    product: str
    ja4: dict[str, str] = field(default_factory=dict[str, str])
    user_agent: str | None = None


@dataclass(frozen=True, slots=True)
class ServiceTable:
    """The endpoints a service implementation serves once started."""

    served: tuple[Endpoint, ...]


@dataclass(frozen=True, slots=True)
class CatalogEntry:
    """One entry of an adapter's catalog, for example a CALDERA ability.

    Catalogs are data so that a sequence's references can be checked statically.
    """

    id: str
    name: str
    attack_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ImplDescriptor:
    """One implementation package.

    ``id`` is what a binding's choices name, optionally as ``id:variant``. ``provides`` lists
    signature ids. A service carries a ``service`` table; an adapter carries a ``catalog``.
    """

    id: str
    version: str
    kind: ImplKind
    provides: tuple[str, ...]
    host: HostRequirements
    variants: tuple[str, ...] = ()
    fingerprint: Fingerprint | None = None
    service: ServiceTable | None = None
    catalog: tuple[CatalogEntry, ...] = ()
