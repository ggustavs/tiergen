"""Check 6: each kind with instances has one host binding, and the host serves the kind's interface.

A default host serves what its selected service implementations serve. A custom host, an
image or a VM template, serves what its manifest resource lists.
"""

from collections.abc import Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error
from tiergen.core.ir import Binding, Endpoint

ID = "C06"
CUSTOM = ("image:", "template:")


def _served_by_default_host(ctx: Context, binding: Binding) -> set[Endpoint]:
    """What is served whichever alternative is sampled: per selection, the endpoints every
    choice serves; across selections, their union."""
    served: set[Endpoint] = set()
    for selection in binding.impls:
        signature = ctx.signatures.get(selection.signature)
        if signature is None or signature.role != "server":
            continue
        tables = [
            set(impl.service.served)
            for choice in ctx.choices(selection) or {}
            if (impl := ctx.impls.get(choice.split(":", 1)[0])) and impl.service
        ]
        if tables:
            common = tables[0]
            for table in tables[1:]:
                common = common & table
            served |= common
    return served


def check(ctx: Context) -> Iterator[Diagnostic]:
    s = ctx.scenario
    names = {k.name for k in s.kinds}
    for i, binding in enumerate(s.bindings):
        if binding.kind not in names:
            yield error(
                ID, f"bindings[{i}].kind", f"{binding.kind!r} is not a kind of this scenario"
            )
        elif [b.kind for b in s.bindings].index(binding.kind) != i:
            yield error(ID, f"bindings[{i}]", f"kind {binding.kind!r} is bound twice")

    for k, kind in enumerate(s.kinds):
        binding = ctx.binding(kind.name)
        if binding is None:
            if s.instances.get(kind.name, 0) > 0:
                yield error(ID, f"kinds[{k}]", f"kind {kind.name!r} has instances but no binding")
            continue
        path = f"bindings[{s.bindings.index(binding)}]"
        host = binding.host
        if host.ref == "default":
            served = _served_by_default_host(ctx, binding)
            source = "its selected service implementations"
        elif host.ref.startswith(CUSTOM) and host.ref.split(":", 1)[1]:
            if host.manifest is None:
                yield error(
                    ID,
                    f"{path}.host.manifest",
                    f"custom host {host.ref!r} needs a manifest of what it serves",
                )
                continue
            manifest = ctx.host_manifest(host)
            if manifest is None:
                continue
            served = set(manifest)
            source = f"manifest {host.manifest!r}"
        else:
            yield error(
                ID,
                f"{path}.host.ref",
                f"{host.ref!r} is not 'default', 'image:<ref>' or 'template:<ref>'",
            )
            continue
        for endpoint in kind.serves:
            if endpoint not in served:
                yield error(
                    ID,
                    path,
                    f"kind {kind.name!r} serves {endpoint.protocol} on {endpoint.port}/"
                    f"{endpoint.transport}, which {source} do not provide",
                )
