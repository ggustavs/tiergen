"""Discovery of descriptors through entry points.

A descriptor is data. Loading one imports only the module that defines it, never the
runtime of the sensor or implementation it describes, so a checker can know what exists
without being able to run any of it.
"""

from importlib.metadata import entry_points
from typing import Protocol

from tiergen.interfaces.attribution import AttributionBackend
from tiergen.interfaces.infra import InfraBackend, InfraDescriptor
from tiergen.interfaces.sensor import SensorDescriptor

GROUP = "tiergen.sensors"
INFRA_GROUP = "tiergen.infra"
INFRA_BACKEND_GROUP = "tiergen.infra.backends"
ATTRIB_GROUP = "tiergen.attrib"


class _HasId(Protocol):
    @property
    def id(self) -> str: ...


def load_group[T: _HasId](group: str, cls: type[T]) -> dict[str, T]:
    """Every descriptor of type ``cls`` registered under ``group``, by id.

    The entry-point name must equal the descriptor's id, so the two cannot drift apart.
    """
    found: dict[str, T] = {}
    for ep in entry_points(group=group):
        descriptor = ep.load()
        if not isinstance(descriptor, cls):
            raise TypeError(f"entry point {ep.name!r} in {group} is not a {cls.__name__}")
        if descriptor.id != ep.name:
            raise ValueError(
                f"entry point {ep.name!r} in {group} names a descriptor with id {descriptor.id!r}"
            )
        found[descriptor.id] = descriptor
    return found


def load_sensors() -> dict[str, SensorDescriptor]:
    """Every installed sensor descriptor, by id."""
    return load_group(GROUP, SensorDescriptor)


def load_infra() -> dict[str, InfraDescriptor]:
    """Every installed infrastructure backend descriptor, by id."""
    return load_group(INFRA_GROUP, InfraDescriptor)


def load_infra_backends(only: set[str] | None = None) -> dict[str, InfraBackend]:
    """The installed infrastructure backend runtimes, by id, each constructed.

    Unlike a descriptor, a backend has a runtime behind it, so ``only`` names the ids to
    load and the rest are not imported.
    """
    found: dict[str, InfraBackend] = {}
    for ep in entry_points(group=INFRA_BACKEND_GROUP):
        if only is not None and ep.name not in only:
            continue
        backend = ep.load()()
        if not isinstance(backend, InfraBackend):
            raise TypeError(
                f"entry point {ep.name!r} in {INFRA_BACKEND_GROUP} is not an InfraBackend"
            )
        if backend.id != ep.name:
            raise ValueError(
                f"entry point {ep.name!r} in {INFRA_BACKEND_GROUP} names a backend "
                f"with id {backend.id!r}"
            )
        found[backend.id] = backend
    return found


def load_attrib_backends(only: set[str] | None = None) -> dict[str, AttributionBackend]:
    """The installed attribution backends, by entry-point name, each constructed; ``only``
    names the ones to load, as for the infrastructure backends."""
    found: dict[str, AttributionBackend] = {}
    for ep in entry_points(group=ATTRIB_GROUP):
        if only is not None and ep.name not in only:
            continue
        backend = ep.load()()
        if not isinstance(backend, AttributionBackend):
            raise TypeError(
                f"entry point {ep.name!r} in {ATTRIB_GROUP} is not an AttributionBackend"
            )
        found[ep.name] = backend
    return found
