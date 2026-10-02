"""The agent's image, built from the workspace the command runs from.

The build context is the Dockerfile beside this module plus the source of every package the
agent needs, found through the installed distributions, with tests and caches left out. The
tag carries a hash of that context, so a source change makes a new image and an unchanged
one is reused; the id of what actually ran goes into the run state.
"""

import hashlib
import shutil
from importlib.resources import files
from importlib.util import find_spec
from pathlib import Path

from tiergen.interfaces import BackendError

NAME = "tiergen/base-linux"
PACKAGES = (
    ("core", "tiergen.core"),
    ("protocols", "tiergen.protocols"),
    ("interfaces", "tiergen.interfaces"),
    ("impls/_base", "tiergen.impls._base"),
    ("impls/httpx", "tiergen.impls.httpx"),
    ("impls/nginx", "tiergen.impls.nginx"),
    ("impls/nmap", "tiergen.impls.nmap"),
    ("runtime/agent_linux", "tiergen.runtime.agent_linux"),
)
"""Where each package sits in the context, and the module that finds its source."""
SKIP = {"__pycache__", "tests", ".venv"}


def dockerfile() -> str:
    return (files(__package__) / "Dockerfile").read_text(encoding="utf-8")


def _member_root(module: str) -> Path:
    """The directory holding the ``pyproject.toml`` of the member that ``module`` is in."""
    spec = find_spec(module)
    if spec is None or spec.origin is None:
        raise BackendError(f"{module} is not installed; the agent image needs it")
    for parent in Path(spec.origin).parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise BackendError(f"{module} is not installed from a workspace member; cannot build the image")


def _ignore(directory: str, names: list[str]) -> set[str]:
    return {n for n in names if n in SKIP or n.endswith(".egg-info")}


def context(into: Path) -> Path:
    """Assemble the build context under ``into`` and return it."""
    into.mkdir(parents=True, exist_ok=True)
    (into / "Dockerfile").write_text(dockerfile(), encoding="utf-8")
    for where, module in PACKAGES:
        shutil.copytree(_member_root(module), into / where, ignore=_ignore, dirs_exist_ok=True)
    return into


def digest(ctx: Path) -> str:
    """Twelve hex digits over every file of the context, by relative path and content."""
    h = hashlib.blake2b(digest_size=6)
    for path in sorted(p for p in ctx.rglob("*") if p.is_file()):
        h.update(str(path.relative_to(ctx)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def tag(ctx: Path) -> str:
    return f"{NAME}:{digest(ctx)}"
