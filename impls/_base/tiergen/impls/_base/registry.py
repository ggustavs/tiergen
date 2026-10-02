"""Discovery of implementation descriptors through the ``tiergen.impls`` entry-point group.

Core never imports implementations at load time, so an implementation that is not
installed is simply unresolved, and check 8 says so.
"""

from importlib.metadata import entry_points

from tiergen.impls._base.descriptor import ImplDescriptor
from tiergen.interfaces.registry import load_group

GROUP = "tiergen.impls"
RUNTIME_GROUP = "tiergen.impls.runtimes"


def load_impls() -> dict[str, ImplDescriptor]:
    """Every installed implementation descriptor, by id."""
    return load_group(GROUP, ImplDescriptor)


def load_runtime(impl_id: str) -> object:
    """The runtime of one implementation, constructed: the ``PrimitiveImpl``, ``ServiceImpl``
    or ``AdapterImpl`` registered under ``tiergen.impls.runtimes`` by the descriptor's id.

    Only the agent calls this, on the host that runs the implementation; nothing else
    imports a runtime. ``LookupError`` if the package registers none.
    """
    for ep in entry_points(group=RUNTIME_GROUP, name=impl_id):
        return ep.load()()
    raise LookupError(f"no runtime is registered for implementation {impl_id!r}")
