"""Check 3: every behaviour state maps to exactly one signature or is explicitly silent."""

from collections.abc import Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error

ID = "C03"


def check(ctx: Context) -> Iterator[Diagnostic]:
    for k, kind in enumerate(ctx.scenario.kinds):
        for b, behaviour in enumerate(kind.behaviours):
            path = f"kinds[{k}].behaviours[{b}]"
            states = ctx.states(behaviour.process)
            actions = ctx.action_map(behaviour)
            if states is None or actions is None:
                continue
            for state in states:
                if state not in actions:
                    yield error(
                        ID,
                        f"{path}.action_map",
                        f"state {state!r} has no entry; use None for a silent state",
                    )
            for state, act in actions.items():
                entry = f"{path}.action_map[{state!r}]"
                if state not in states:
                    yield error(
                        ID, entry, f"{state!r} is not a state of behaviour {behaviour.name!r}"
                    )
                if act is None:
                    continue
                signature = ctx.signatures.get(act.signature)
                if signature is None:
                    yield error(ID, f"{entry}.signature", f"unknown signature {act.signature!r}")
                elif signature.role != "client":
                    yield error(
                        ID,
                        f"{entry}.signature",
                        f"{act.signature} is a server signature; it belongs in a binding, "
                        "not an action",
                    )
