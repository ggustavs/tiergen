"""Check 8: every signature a kind uses resolves to installed implementations, usably weighted."""

import math
from collections.abc import Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error

ID = "C08"


def check(ctx: Context) -> Iterator[Diagnostic]:
    s = ctx.scenario
    for kind in s.kinds:
        binding = ctx.binding(kind.name)
        if binding is None:
            continue  # check 6 reports a kind with instances and no binding
        bound = {selection.signature for selection in binding.impls}
        used = {
            act.signature
            for _, act in ctx.actions(kind)
            if (sig := ctx.signatures.get(act.signature)) and sig.role == "client"
        }  # check 3 reports an unknown or a server signature in an action
        for signature in sorted(used - bound):
            yield error(
                ID,
                f"bindings[{s.bindings.index(binding)}].impls",
                f"kind {kind.name!r} uses {signature}, which no implementation is selected for",
            )

    for i, binding in enumerate(s.bindings):
        for j, selection in enumerate(binding.impls):
            path = f"bindings[{i}].impls[{j}]"
            if selection.signature not in ctx.signatures:
                yield error(ID, f"{path}.signature", f"unknown signature {selection.signature!r}")
                continue
            choices = ctx.choices(selection)
            if choices is None:
                continue
            if not choices:
                yield error(
                    ID, f"{path}.choices", f"no implementation is offered for {selection.signature}"
                )
            for choice, weight in choices.items():
                where = f"{path}.choices[{choice!r}]"
                impl_id, _, variant = choice.partition(":")
                impl = ctx.impls.get(impl_id)
                if impl is None:
                    yield error(ID, where, f"implementation {impl_id!r} is not installed")
                else:
                    if selection.signature not in impl.provides:
                        yield error(ID, where, f"{impl_id} does not provide {selection.signature}")
                    if variant and variant not in impl.variants:
                        yield error(ID, where, f"{impl_id} has no variant {variant!r}")
                if not (math.isfinite(weight) and weight > 0):
                    yield error(ID, where, f"weight {weight!r} is not positive")

    for e, event in enumerate(s.schedule):
        if event.op != "run_sequence" or not isinstance(event.arg, str):
            continue  # check 12 reports a run_sequence without a string argument
        adapter_id, _, entry = event.arg.partition(":")
        adapter = ctx.impls.get(adapter_id)
        if adapter is None or adapter.kind != "adapter":
            yield error(ID, f"schedule[{e}].arg", f"{adapter_id!r} is not an installed adapter")
        elif entry not in {c.id for c in adapter.catalog}:
            yield error(
                ID, f"schedule[{e}].arg", f"adapter {adapter_id} has no catalog entry {entry!r}"
            )
