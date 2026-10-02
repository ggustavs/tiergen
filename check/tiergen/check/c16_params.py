"""Check 16: every action gives its signature's parameters usable values.

Required parameters are present, no parameter is unknown, literals and choice options have
the declared type, and a choice has one positive weight per option. A choice held in a
resource is resolved by check 5; one that does not resolve is skipped here.
"""

import math
from collections.abc import Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error
from tiergen.core.ir import Choice, ChoiceRef, ParamScalar
from tiergen.protocols.signature import ParamType

ID = "C16"


def _fits(value: ParamScalar, declared: ParamType) -> bool:
    if isinstance(value, bool):  # bool is an int; keep it out of the numeric types
        return declared == "bool"
    if declared == "str":
        return isinstance(value, str)
    if declared == "int":
        return isinstance(value, int)
    return declared == "float" and isinstance(value, (int, float))


def check(ctx: Context) -> Iterator[Diagnostic]:
    for kind in ctx.scenario.kinds:
        for path, act in ctx.actions(kind):
            signature = ctx.signatures.get(act.signature)
            if signature is None or signature.role != "client":
                continue  # check 3 reports these
            tie = next((t for t in kind.ties if t.name == act.tie), None)
            if tie is not None:
                if tie.multiplicity == "multiple" and act.select is None:
                    yield error(
                        ID,
                        f"{path}.select",
                        f"tie {act.tie!r} is multiple: say whether {act.signature} hits all "
                        "its targets or one",
                    )
                elif tie.multiplicity != "multiple" and act.select is not None:
                    yield error(
                        ID,
                        f"{path}.select",
                        f"tie {act.tie!r} is {tie.multiplicity}; select means nothing there",
                    )
            declared = {p.name: p for p in signature.params}
            for name in sorted(
                n for n, p in declared.items() if p.required and n not in act.params
            ):
                yield error(ID, f"{path}.params", f"{act.signature} requires parameter {name!r}")
            for name, value in act.params.items():
                where = f"{path}.params[{name!r}]"
                param = declared.get(name)
                if param is None:
                    known = ", ".join(declared) or "none"
                    yield error(
                        ID, where, f"{act.signature} has no parameter {name!r}; it has: {known}"
                    )
                    continue
                choice = ctx.choice(value) if isinstance(value, (Choice, ChoiceRef)) else None
                if isinstance(value, ChoiceRef) and choice is None:
                    continue
                options = choice.options if choice else (value,)
                for option in options:
                    if not isinstance(option, (Choice, ChoiceRef)) and not _fits(
                        option, param.type
                    ):
                        yield error(
                            ID, where, f"{option!r} is not a {param.type}, which {name!r} is"
                        )
                if choice is None:
                    continue
                if not choice.options:
                    yield error(ID, where, "a choice needs at least one option")
                if len(choice.weights) != len(choice.options):
                    yield error(
                        ID,
                        where,
                        f"{len(choice.options)} options but {len(choice.weights)} weights",
                    )
                if any(not (math.isfinite(w) and w > 0) for w in choice.weights):
                    yield error(ID, where, "every weight must be positive")
