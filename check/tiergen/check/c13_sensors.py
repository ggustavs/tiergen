"""Check 13: every sensor is a registered implementation that can reproduce the pinned setup.

In M0 "can reproduce" means the descriptor lists the version and the mode. Whether the
configuration resource exists is check 5's. A registered sensor meets the required core by
construction: its descriptor would not exist otherwise.
"""

from collections.abc import Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error
from tiergen.interfaces import Capability

ID = "C13"


def check(ctx: Context) -> Iterator[Diagnostic]:
    sensors = ctx.scenario.sensors
    if not sensors:
        yield error(
            ID,
            "sensors",
            "a scenario needs at least one sensor; the sensor defines flows and events",
        )
    for i, spec in enumerate(sensors):
        path = f"sensors[{i}]"
        descriptor = ctx.sensors.get(spec.impl)
        if descriptor is None:
            yield error(ID, f"{path}.impl", f"sensor {spec.impl!r} is not installed")
            continue
        if spec.version not in descriptor.versions:
            known = ", ".join(descriptor.versions)
            yield error(
                ID,
                f"{path}.version",
                f"{spec.impl} {spec.version} cannot be reproduced; known versions: {known}",
            )
        if spec.mode not in descriptor.modes:
            yield error(ID, f"{path}.mode", f"{spec.impl} does not support {spec.mode} mode")
        for c, name in enumerate(spec.capabilities):
            if name not in Capability.__members__:
                yield error(ID, f"{path}.capabilities[{c}]", f"{name!r} is not a capability")
            elif Capability[name] not in descriptor.capabilities:
                yield error(ID, f"{path}.capabilities[{c}]", f"{spec.impl} cannot declare {name}")
