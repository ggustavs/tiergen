"""Check 15: every capability ``fit`` relied on has measured coverage above the scenario's floor."""

from collections.abc import Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, warning

ID = "C15"


def check(ctx: Context) -> Iterator[Diagnostic]:
    provenance = ctx.provenance()
    if provenance is None:
        return
    floor = ctx.scenario.coverage_floor
    for capability in provenance.capabilities_used:
        coverage = provenance.coverage.get(capability)
        if coverage is None:
            yield warning(
                ID,
                "fit_provenance.coverage",
                f"fit used {capability} but recorded no coverage for it",
            )
        elif coverage < floor:
            yield warning(
                ID,
                f"fit_provenance.coverage[{capability!r}]",
                f"{capability} is populated on {coverage:.0%} of applicable events, under the "
                f"{floor:.0%} floor; what was fitted from it is sparse",
            )
