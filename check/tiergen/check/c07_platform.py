"""Check 7: a binding's platform suits the kind and every implementation chosen for it.

The third clause, that the host capabilities an implementation needs are grantable by the
infrastructure backend for that host type, needs a backend and is reported as not computed.
"""

from collections.abc import Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error, not_computed

ID = "C07"


def check(ctx: Context) -> Iterator[Diagnostic]:
    for i, binding in enumerate(ctx.scenario.bindings):
        kind = ctx.kind(binding.kind)
        platform = binding.host.platform
        if kind is not None and platform not in kind.platforms:
            allowed = ", ".join(kind.platforms)
            yield error(
                ID,
                f"bindings[{i}].host.platform",
                f"kind {kind.name!r} allows {allowed}, not {platform}",
            )
        for j, selection in enumerate(binding.impls):
            for choice in ctx.choices(selection) or {}:
                impl = ctx.impls.get(choice.split(":", 1)[0])
                if impl is None:
                    continue  # check 8 reports it
                path = f"bindings[{i}].impls[{j}].choices[{choice!r}]"
                if platform not in impl.host.platforms:
                    yield error(ID, path, f"{impl.id} does not run on {platform}")
                for capability in impl.host.capabilities:
                    yield not_computed(
                        ID,
                        path,
                        f"{impl.id} needs host capability {capability!r}; whether a "
                        f"{platform} {binding.host.host_type} can be granted it depends on the "
                        "infrastructure backend, which M0 does not have",
                    )
