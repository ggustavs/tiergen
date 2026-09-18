"""Discovery of implementation descriptors through the ``tiergen.impls`` entry-point group.

Core never imports implementations at load time, so an implementation that is not
installed is simply unresolved, and check 8 says so.
"""

from tiergen.impls._base.descriptor import ImplDescriptor
from tiergen.interfaces.registry import load_group

GROUP = "tiergen.impls"


def load_impls() -> dict[str, ImplDescriptor]:
    """Every installed implementation descriptor, by id."""
    return load_group(GROUP, ImplDescriptor)
