"""Check 2: every action's signature is directed at a tie whose target can answer it."""

from collections.abc import Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error

ID = "C02"


def check(ctx: Context) -> Iterator[Diagnostic]:
    for kind in ctx.scenario.kinds:
        ties = {t.name: t for t in kind.ties}
        for path, act in ctx.actions(kind):
            signature = ctx.signatures.get(act.signature)
            if signature is None or signature.role != "client":
                continue  # check 3 reports these
            tie = ties.get(act.tie)
            if tie is None:
                yield error(ID, f"{path}.tie", f"kind {kind.name!r} has no tie {act.tie!r}")
                continue
            target = ctx.kind(tie.target_kind)
            if target is None or not signature.endpoints:
                continue  # an unknown target is check 1's; a scan needs no endpoint
            transport = signature.shape.transport
            if not any(
                e.protocol in signature.endpoints and e.transport == transport
                for e in target.serves
            ):
                wanted = " or ".join(signature.endpoints)
                yield error(
                    ID,
                    path,
                    f"{act.signature} over tie {act.tie!r} needs {target.name!r} to serve "
                    f"{wanted} on {transport}, and it does not",
                )
