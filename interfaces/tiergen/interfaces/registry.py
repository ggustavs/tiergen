"""Discovery of descriptors through entry points.

A descriptor is data. Loading one imports only the module that defines it, never the
runtime of the sensor or implementation it describes, so a checker can know what exists
without being able to run any of it.
"""

from importlib.metadata import entry_points
from typing import Protocol

from tiergen.interfaces.sensor import SensorDescriptor

GROUP = "tiergen.sensors"


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
