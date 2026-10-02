"""Check 11: the label tuple is unique per invocation, and nothing runs outside a labelled context.

Statically, that means the names a label is built from are unique where they must be, and
that a client implementation is only selected for a signature some action can invoke.
"""

from collections.abc import Iterable, Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error, warning

ID = "C11"


def _duplicates(names: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: set[str] = set()
    for name in names:
        (out if name in seen else seen).add(name)
    return sorted(out)


def check(ctx: Context) -> Iterator[Diagnostic]:
    s = ctx.scenario
    for name in _duplicates(k.name for k in s.kinds):
        yield error(ID, "kinds", f"kind name {name!r} is used twice")
    for k, kind in enumerate(s.kinds):
        path = f"kinds[{k}]"
        for name in _duplicates(t.name for t in kind.ties):
            yield error(ID, f"{path}.ties", f"tie name {name!r} is used twice")
        for name in _duplicates(b.name for b in kind.behaviours):
            yield error(ID, f"{path}.behaviours", f"behaviour name {name!r} is used twice")
        for b, behaviour in enumerate(kind.behaviours):
            for name in _duplicates(ctx.states(behaviour.process) or ()):
                yield error(
                    ID, f"{path}.behaviours[{b}].process.states", f"state {name!r} is listed twice"
                )

    kind_names = {k.name for k in s.kinds}
    seen: dict[str, int] = {}
    for g, group in enumerate(s.groups):
        if group.parent is not None and group.name in kind_names:
            parent = next((p for p in s.groups if p.path == group.parent), None)
            if parent is not None and parent.instances.get(group.name, 0) > 0:
                yield error(
                    ID,
                    f"groups[{g}].name",
                    f"group {group.path!r} is named like kind {group.name!r}, which its parent "
                    "holds: a schedule target could mean either",
                )
        if group.path in seen:
            yield error(
                ID,
                f"groups[{g}]",
                f"group path {group.path!r} is used twice (also groups[{seen[group.path]}])",
            )
        seen.setdefault(group.path, g)
    for g, group in enumerate(s.groups):
        if group.parent is not None and group.parent not in seen:
            yield error(
                ID, f"groups[{g}].parent", f"{group.parent!r} is not a group of this scenario"
            )
        if not group.name or any(c in group.name for c in "/[]"):
            yield error(
                ID, f"groups[{g}].name", f"{group.name!r} is not a group name: no '/', '[' or ']'"
            )

    for i, binding in enumerate(s.bindings):
        for name in _duplicates(sel.signature for sel in binding.impls):
            yield error(ID, f"bindings[{i}].impls", f"signature {name} is selected twice")
        kind = ctx.kind(binding.kind)
        if kind is None:
            continue
        invoked = {act.signature for _, act in ctx.actions(kind)}
        for j, selection in enumerate(binding.impls):
            signature = ctx.signatures.get(selection.signature)
            if signature and signature.role == "client" and selection.signature not in invoked:
                yield warning(
                    ID,
                    f"bindings[{i}].impls[{j}]",
                    f"no action of {kind.name!r} invokes {selection.signature}; "
                    "the selection can never run in a labelled context",
                )
