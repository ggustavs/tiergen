"""Check 1: every group counts real kinds, every tie is wired, and wiring satisfies multiplicity.

A tie's targets are the instances of its target kind in the groups its wiring names
(``tiergen.core.groups.targets``). ``single`` needs exactly one such instance, ``optional``
at most one, ``multiple`` any number. Nothing is looked up by walking the tree, so a tie a
group leaves unwired is an error here, not a guess at run time.
"""

from collections.abc import Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error
from tiergen.core.ir import Tie

ID = "C01"


def check(ctx: Context) -> Iterator[Diagnostic]:
    s = ctx.scenario
    kinds = {k.name: k for k in s.kinds}
    group_paths = {g.path for g in s.groups}

    for k, kind in enumerate(s.kinds):
        for t, tie in enumerate(kind.ties):
            if tie.target_kind not in kinds:
                yield error(
                    ID,
                    f"kinds[{k}].ties[{t}].target_kind",
                    f"tie {tie.name!r} targets unknown kind {tie.target_kind!r}",
                )

    for g, group in enumerate(s.groups):
        path = f"groups[{g}]"
        for name, count in group.instances.items():
            if name not in kinds:
                yield error(
                    ID, f"{path}.instances[{name!r}]", f"{name!r} is not a kind of this scenario"
                )
            elif count < 0:
                yield error(
                    ID, f"{path}.instances[{name!r}]", f"instance count {count} is negative"
                )

        held = {name for name, count in group.instances.items() if name in kinds and count > 0}
        expected: dict[str, Tie] = {
            f"{name}.{tie.name}": tie for name in held for tie in kinds[name].ties
        }
        for key in sorted(set(expected) - set(group.wiring)):
            yield error(
                ID,
                f"{path}.wiring",
                f"{key} is not wired: say which groups' instances of "
                f"{expected[key].target_kind!r} it reaches from {group.path!r}",
            )
        for key, wired in group.wiring.items():
            where = f"{path}.wiring[{key!r}]"
            if key not in expected:
                kind_name, _, tie_name = key.partition(".")
                if kind_name in held and tie_name not in {t.name for t in kinds[kind_name].ties}:
                    yield error(ID, where, f"kind {kind_name!r} has no tie {tie_name!r}")
                elif kind_name not in held:
                    yield error(ID, where, f"{group.path!r} holds no {kind_name!r} to wire")
                continue
            tie = expected[key]
            if tie.target_kind not in kinds:
                continue  # reported above
            unknown = [p for p in wired if p not in group_paths]
            for p in unknown:
                yield error(ID, where, f"{p!r} is not a group of this scenario")
            if unknown or not wired:
                if not wired:
                    yield error(ID, where, f"{key} is wired to no group")
                continue
            total = sum(
                max(other.instances.get(tie.target_kind, 0), 0)
                for other in s.groups
                if other.path in wired
            )
            reach = ", ".join(repr(p) for p in wired)
            if tie.multiplicity == "single" and total != 1:
                yield error(
                    ID,
                    where,
                    f"{key} is single and must reach exactly one {tie.target_kind!r}; "
                    f"{reach} hold {total}",
                )
            elif tie.multiplicity == "optional" and total > 1:
                yield error(
                    ID,
                    where,
                    f"{key} is optional and may reach at most one {tie.target_kind!r}; "
                    f"{reach} hold {total}",
                )
