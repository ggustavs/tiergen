"""Check 14: cross-sensor consistency between what ``fit`` used and what label sensors declare.

A model fitted at a richer sensor's resolution encodes features a poorer label sensor never
produces, and a detector trained on them is useless in that deployment. The gap is a
warning, because the engineer may accept it knowingly. A scenario that was not fitted has
no provenance and nothing to compare.
"""

from collections.abc import Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error, warning

ID = "C14"


def check(ctx: Context) -> Iterator[Diagnostic]:
    provenance = ctx.provenance()
    if provenance is None:
        return
    sensors = ctx.scenario.sensors
    fit_sensors = [s for s in sensors if s.role in ("fit", "both")]
    if len(fit_sensors) != 1:
        yield error(
            ID, "sensors", f"exactly one sensor must have a fit role; {len(fit_sensors)} do"
        )
    elif fit_sensors[0].impl != provenance.sensor:
        yield error(
            ID,
            f"sensors[{sensors.index(fit_sensors[0])}].role",
            f"the fit sensor is {fit_sensors[0].impl}, but the model was fitted from "
            f"{provenance.sensor}",
        )
    for i, spec in enumerate(sensors):
        if spec.role not in ("label", "both"):
            continue
        for capability in provenance.capabilities_used:
            if capability not in spec.capabilities:
                yield warning(
                    ID,
                    f"sensors[{i}].capabilities",
                    f"fit used {capability} from {provenance.sensor}, which label sensor "
                    f"{spec.impl} does not declare; features derived from it will be absent "
                    f"in a {spec.impl} deployment",
                )
