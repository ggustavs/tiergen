"""Check 7: a binding's host is one its backend offers, and suits the kind and every implementation.

The platform is one the kind allows. The backend is installed and offers that platform and
host type. Every implementation chosen for the binding runs on the platform, and the host
capabilities it needs, such as ``net_raw``, are ones the backend can grant such a host.
"""

from collections.abc import Iterator

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error, warning
from tiergen.core.ir import HostRef
from tiergen.impls._base import ImplRef

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

        parsed_ref = HostRef.parse(host.ref)
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

        if offer is not None and offer.grantable is not None and binding.mac_oui is None:
            yield warning(
                ID,
                f"bindings[{i}].mac_oui",
                f"{binding.kind!r} has no MAC prefix, so its hosts get {host.backend}'s own, "
                "which a sensor can fingerprint as the substrate; fit the OUI or set one",
            )
        bases: dict[str, str] = {}
        for j, selection in enumerate(binding.impls):
            for choice in ctx.choices(selection) or {}:
                impl = ctx.impls.get(ImplRef.parse(choice).impl)
                if impl is None:
                    continue  # check 8 reports it
                path = f"bindings[{i}].impls[{j}].choices[{choice!r}]"
                if platform not in impl.host.platforms:
                    yield error(ID, path, f"{impl.id} does not run on {platform}")
                base = impl.host.image_base.get(platform)
                if base is not None and parsed_ref is not None and parsed_ref.kind == "default":
                    if bases and base not in bases.values():
                        other = next(iter(bases))
                        yield error(
                            ID,
                            path,
                            f"{impl.id} wants base image {base!r} but {other} wants "
                            f"{bases[other]!r}; one default host cannot be built from both",
                        )
                    bases.setdefault(impl.id, base)
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
