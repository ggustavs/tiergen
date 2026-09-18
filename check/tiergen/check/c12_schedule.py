"""Check 12: schedule events reference defined targets, at times within the run."""

import re
from collections.abc import Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error

ID = "C12"
_TARGET = re.compile(r"(?P<kind>[^\[\]]+)(?:\[(?P<index>\d+)\])?")


def check(ctx: Context) -> Iterator[Diagnostic]:
    s = ctx.scenario
    for e, event in enumerate(s.schedule):
        path = f"schedule[{e}]"
        if not 0 <= event.at_s <= s.duration_s:
            yield error(
                ID, f"{path}.at_s", f"{event.at_s:g} s is outside the run, 0 to {s.duration_s:g} s"
            )

        match = _TARGET.fullmatch(event.target)
        kind = ctx.kind(match["kind"]) if match else None
        if match is None:
            yield error(ID, f"{path}.target", f"{event.target!r} is neither 'kind' nor 'kind[i]'")
        elif kind is None:
            yield error(ID, f"{path}.target", f"{match['kind']!r} is not a kind of this scenario")
        elif match["index"] is not None:
            count = s.instances.get(kind.name, 0)
            if int(match["index"]) >= count:
                yield error(
                    ID,
                    f"{path}.target",
                    f"{kind.name!r} has {count} instances; there is no {event.target}",
                )

        arg = event.arg
        if event.op in ("start", "stop"):
            if not isinstance(arg, str):
                yield error(ID, f"{path}.arg", f"{event.op} takes the name of a behaviour")
            elif kind is not None and arg not in {b.name for b in kind.behaviours}:
                yield error(ID, f"{path}.arg", f"{kind.name!r} has no behaviour {arg!r}")
        elif event.op == "set_rate":
            if isinstance(arg, str) or arg is None or arg < 0:
                yield error(ID, f"{path}.arg", "set_rate takes a non-negative rate multiplier")
        elif not isinstance(arg, str):
            yield error(ID, f"{path}.arg", "run_sequence takes 'adapter:catalog-entry'")
