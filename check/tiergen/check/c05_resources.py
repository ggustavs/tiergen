"""Check 5: every resource reference resolves, and what it resolves to has the declared shape.

This is the only check that reports a missing or ill-shaped resource. A parameter is never
defaulted: a scenario that names a resource it does not have is ill formed.
"""

from collections.abc import Iterator
from typing import Any

from tiergen.check.context import Context, Floats
from tiergen.check.diagnostics import Diagnostic, error
from tiergen.core.codec import CodecError, decode
from tiergen.core.ir import Action, Distribution, Endpoint, FitProvenance

ID = "C05"

OPAQUE = None
"""In place of a shape: the resource only has to exist, as a sensor's configuration does."""


def references(ctx: Context) -> Iterator[tuple[str, str, Any]]:
    """Every (path, resource name, expected shape) in the scenario."""
    s = ctx.scenario
    for k, kind in enumerate(s.kinds):
        for b, behaviour in enumerate(kind.behaviours):
            base = f"kinds[{k}].behaviours[{b}]"
            p = behaviour.process
            for field, value, shape in (
                ("process.states", p.states, tuple[str, ...]),
                ("process.initial", p.initial, Floats),
                ("process.transitions", p.transitions, tuple[Floats, ...]),
                ("process.dwell", p.dwell, tuple[Distribution, ...]),
                ("process.rate", p.rate, Floats),
                ("action_map", behaviour.action_map, dict[str, Action | None]),
            ):
                if isinstance(value, str):
                    yield f"{base}.{field}", value, shape
            # Distribution parameters may be resources too, whether dwell is inline or not.
            for d, distribution in enumerate(ctx.dwell(p) or ()):
                if isinstance(distribution.params, str):
                    yield f"{base}.process.dwell[{d}].params", distribution.params, Floats
    for i, binding in enumerate(s.bindings):
        if binding.host.manifest is not None:
            yield f"bindings[{i}].host.manifest", binding.host.manifest, tuple[Endpoint, ...]
        for j, selection in enumerate(binding.impls):
            if isinstance(selection.choices, str):
                yield f"bindings[{i}].impls[{j}].choices", selection.choices, dict[str, float]
    yield "topology", s.topology, OPAQUE
    for i, sensor in enumerate(s.sensors):
        yield f"sensors[{i}].config", sensor.config, OPAQUE
    if isinstance(s.fit_provenance, str):
        yield "fit_provenance", s.fit_provenance, FitProvenance


def check(ctx: Context) -> Iterator[Diagnostic]:
    for path, name, shape in references(ctx):
        if not ctx.resources.exists(name):
            yield error(ID, path, f"resource {name!r} does not exist")
        elif shape is not OPAQUE:
            try:
                decode(shape, ctx.resources.get(name))
            except KeyError:
                yield error(ID, path, f"resource {name!r} is not JSON")
            except CodecError as err:
                yield error(ID, path, f"resource {name!r} has the wrong shape: {err}")
