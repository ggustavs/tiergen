"""The workspace members an agent host installs, and where to find their sources.

The Docker backend copies them into an image context; the libvirt backend builds them into
wheels for the run ISO. Both need the same list and the same way from a module to the
member directory holding its ``pyproject.toml``.
"""

from importlib.util import find_spec
from pathlib import Path

from tiergen.interfaces.infra import BackendError

AGENT_MEMBERS: dict[str, tuple[str, str]] = {
    "linux": ("tiergen-agent-linux", "tiergen.runtime.agent_linux"),
}
"""Per platform, the agent's distribution name and module."""

MEMBERS: tuple[tuple[str, str], ...] = (
    ("tiergen-core", "tiergen.core"),
    ("tiergen-protocols", "tiergen.protocols"),
    ("tiergen-interfaces", "tiergen.interfaces"),
    ("tiergen-impls-base", "tiergen.impls._base"),
    ("tiergen-behaviour", "tiergen.runtime.behaviour"),
    ("tiergen-impl-httpx", "tiergen.impls.httpx"),
    ("tiergen-impl-nginx", "tiergen.impls.nginx"),
    ("tiergen-impl-nmap", "tiergen.impls.nmap"),
)
"""Distribution name and module of every member an agent imports, the agents aside."""


def member_root(module: str) -> Path:
    """The directory holding the ``pyproject.toml`` of the member ``module`` is in."""
    found = find_spec(module)
    if found is None or found.origin is None:
        raise BackendError(f"{module} is not installed; the agent host needs it")
    for parent in Path(found.origin).parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise BackendError(f"{module} is not installed from a workspace member")


def workspace_root(module: str = "tiergen.core") -> Path:
    """The workspace root: the ancestor of a member that holds ``uv.lock``."""
    for parent in member_root(module).parents:
        if (parent / "uv.lock").is_file():
            return parent
    raise BackendError("the workspace root (the directory with uv.lock) was not found")
