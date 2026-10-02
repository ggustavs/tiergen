"""Check 12: schedule events reference defined targets, at times within the run.

A target is a group path (every instance under it), ``path/kind`` (every instance of that
kind under the group) or ``path/kind[i]`` (one instance), resolved by
``tiergen.core.groups.select``.
"""

from collections.abc import Iterator
from datetime import datetime

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error
from tiergen.core.groups import instance_ids, select

ID = "C12"


def check(ctx: Context) -> Iterator[Diagnostic]:
    s = ctx.scenario
    kind_of = {instance: kind for _, kind, instance in instance_ids(s)}
    try:
        moment = datetime.fromisoformat(s.start)
    except ValueError:
        moment = None
    if moment is None or moment.utcoffset() is None:
        yield error(
            ID,
            "start",
            f"{s.start!r} is not an ISO 8601 time with a UTC offset; the rate curves are in "
            "the network's local time and need an hour and a weekday to anchor to",
        )
    for e, event in enumerate(s.schedule):
        path = f"schedule[{e}]"
        if not 0 <= event.at_s <= s.duration_s:
            yield error(
                ID, f"{path}.at_s", f"{event.at_s:g} s is outside the run, 0 to {s.duration_s:g} s"
            )

        selected = select(s, event.target)
        if selected is None:
            yield error(
                ID,
                f"{path}.target",
                f"{event.target!r} names no group, kind or instance of this scenario",
            )
        elif not selected:
            yield error(ID, f"{path}.target", f"{event.target!r} selects no instance")
        named = {kind_of[i] for i in selected or ()}
        kinds = [k for name in sorted(named) if (k := ctx.kind(name)) is not None]

        arg = event.arg
        if event.op in ("start", "stop"):
            if not isinstance(arg, str):
                yield error(ID, f"{path}.arg", f"{event.op} takes the name of a behaviour")
            elif lacking := [k.name for k in kinds if arg not in {b.name for b in k.behaviours}]:
                yield error(
                    ID,
                    f"{path}.arg",
                    f"no behaviour {arg!r} on {', '.join(lacking)}; every targeted kind "
                    "must have it",
                )
        elif event.op == "set_rate":
            if isinstance(arg, str) or arg is None or arg < 0:
                yield error(ID, f"{path}.arg", "set_rate takes a non-negative rate multiplier")
        elif not isinstance(arg, str):
            yield error(ID, f"{path}.arg", "run_sequence takes 'adapter:catalog-entry'")
