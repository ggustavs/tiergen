"""Check 1: tie targets exist, and multiplicities are satisfiable by the instance counts.

Multiplicities follow the multitier reading: ``single`` is exactly one peer, ``optional``
zero or one, ``multiple`` any number including none. Only ``single`` constrains counts.
"""

from collections.abc import Iterator

from tiergen.check._solver import unsatisfiable
from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error

ID = "C01"


def check(ctx: Context) -> Iterator[Diagnostic]:
    s = ctx.scenario
    names = {k.name for k in s.kinds}
    for name in sorted(names - set(s.instances)):
        yield error(ID, "instances", f"kind {name!r} has no instance count")
    for name, count in s.instances.items():
        if name not in names:
            yield error(ID, f"instances[{name!r}]", f"{name!r} is not a kind of this scenario")
        elif count < 0:
            yield error(ID, f"instances[{name!r}]", f"instance count {count} is negative")

    counts = {name: count for name, count in s.instances.items() if name in names and count >= 0}
    needs: list[tuple[str, str]] = []
    where: list[tuple[str, str]] = []
    for k, kind in enumerate(s.kinds):
        for t, tie in enumerate(kind.ties):
            path = f"kinds[{k}].ties[{t}]"
            if tie.target_kind not in names:
                yield error(
                    ID,
                    f"{path}.target_kind",
                    f"tie {tie.name!r} targets unknown kind {tie.target_kind!r}",
                )
            elif tie.multiplicity == "single" and kind.name in counts and tie.target_kind in counts:
                needs.append((kind.name, tie.target_kind))
                where.append((path, tie.name))
    for i in unsatisfiable(counts, needs):
        source, target = needs[i]
        path, tie_name = where[i]
        yield error(
            ID,
            path,
            f"tie {tie_name!r} is single, but there are {counts[source]} {source!r} "
            f"and no {target!r} for them to reach",
        )
