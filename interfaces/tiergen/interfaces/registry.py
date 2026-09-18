"""Discovery of sensor descriptors through the ``tiergen.sensors`` entry-point group.

Loading a descriptor imports only the module that defines it, never a sensor's runtime.
"""

from importlib.metadata import entry_points

from tiergen.interfaces.sensor import SensorDescriptor

GROUP = "tiergen.sensors"


def load_sensors() -> dict[str, SensorDescriptor]:
    """Every installed sensor descriptor, by id."""
    found: dict[str, SensorDescriptor] = {}
    for ep in entry_points(group=GROUP):
        descriptor = ep.load()
        if not isinstance(descriptor, SensorDescriptor):
            raise TypeError(f"entry point {ep.name!r} in {GROUP} is not a SensorDescriptor")
        if descriptor.id != ep.name:
            raise ValueError(
                f"entry point {ep.name!r} in {GROUP} names a descriptor with id {descriptor.id!r}"
            )
        found[descriptor.id] = descriptor
    return found
