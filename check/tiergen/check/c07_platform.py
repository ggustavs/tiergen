"""Check 7: a binding's host is one its backend offers, and suits the kind and every implementation.

The platform is one the kind allows. The backend is installed and offers that platform and
host type. Every implementation chosen for the binding runs on the platform, and the host
capabilities it needs, such as ``net_raw``, are ones the backend can grant such a host.
"""

from collections.abc import Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error

ID = "C07"


def check(ctx: Context) -> Iterator[Diagnostic]:
    for i, binding in enumerate(ctx.scenario.bindings):
        host = binding.host
        platform = host.platform
        kind = ctx.kind(binding.kind)
        if kind is not None and platform not in kind.platforms:
            allowed = ", ".join(kind.platforms)
            yield error(
                ID,
                f"bindings[{i}].host.platform",
                f"kind {kind.name!r} allows {allowed}, not {platform}",
            )

        backend = ctx.infra.get(host.backend)
        offer = backend.offer(platform, host.host_type) if backend else None
        if backend is None:
            yield error(
                ID,
                f"bindings[{i}].host.backend",
                f"infrastructure backend {host.backend!r} is not installed",
            )
        elif offer is None:
            offered = ", ".join(f"{o.platform} {o.host_type}" for o in backend.offers)
            yield error(
                ID,
                f"bindings[{i}].host",
                f"{backend.id} offers no {platform} {host.host_type}; it offers: {offered}",
            )

        for j, selection in enumerate(binding.impls):
            for choice in ctx.choices(selection) or {}:
                impl = ctx.impls.get(choice.split(":", 1)[0])
                if impl is None:
                    continue  # check 8 reports it
                path = f"bindings[{i}].impls[{j}].choices[{choice!r}]"
                if platform not in impl.host.platforms:
                    yield error(ID, path, f"{impl.id} does not run on {platform}")
                if offer is None or offer.grantable is None:
                    continue  # no such host, or a host that owns its kernel
                for capability in impl.host.capabilities:
                    if capability not in offer.grantable:
                        yield error(
                            ID,
                            path,
                            f"{impl.id} needs host capability {capability!r}, which {host.backend} "
                            f"cannot grant a {platform} {host.host_type}",
                        )
