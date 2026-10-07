"""Images the backend builds from the workspace, through the SDK, when the daemon lacks them.

A ``Spec`` names an image and says what goes into its build context: the Dockerfile, the
workspace members the image installs (found through the installed distributions, tests
and caches left out) and any further files. The tag carries a hash of that context, so a
source change makes a new image and an unchanged one is reused; the id of what actually
ran goes into the run state.
"""

import hashlib
import shutil
import tempfile
from dataclasses import dataclass
from importlib.resources import files
from importlib.util import find_spec
from pathlib import Path

from tiergen.backends.infra.docker._client import Client
from tiergen.interfaces import BackendError, RunState

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
"""Where each package sits in the agent image's context, and the module that finds its source."""
SKIP = {"__pycache__", "tests", ".venv"}


@dataclass(frozen=True, slots=True)
class Spec:
    """One image: its name, its Dockerfile, the members it installs (context path, module)
    and other files it needs (context path, source path)."""

    name: str
    dockerfile: str
    packages: tuple[tuple[str, str], ...] = ()
    files: tuple[tuple[str, Path], ...] = ()


def dockerfile() -> str:
    return (files(__package__) / "Dockerfile").read_text(encoding="utf-8")


def agent() -> Spec:
    return Spec(NAME, dockerfile(), PACKAGES)


def _member_root(module: str) -> Path:
    """The directory holding the ``pyproject.toml`` of the member that ``module`` is in."""
    found = find_spec(module)
    if found is None or found.origin is None:
        raise BackendError(f"{module} is not installed; the image needs it")
    for parent in Path(found.origin).parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise BackendError(f"{module} is not installed from a workspace member; cannot build the image")


def _ignore(directory: str, names: list[str]) -> set[str]:
    return {n for n in names if n in SKIP or n.endswith(".egg-info")}


def context(into: Path, spec: Spec) -> Path:
    """Assemble the build context under ``into`` and return it."""
    into.mkdir(parents=True, exist_ok=True)
    (into / "Dockerfile").write_text(spec.dockerfile, encoding="utf-8")
    for where, module in spec.packages:
        shutil.copytree(_member_root(module), into / where, ignore=_ignore, dirs_exist_ok=True)
    for where, source in spec.files:
        (into / where).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, into / where)
    return into


def digest(ctx: Path) -> str:
    """Twelve hex digits over every file of the context, by relative path and content."""
    h = hashlib.blake2b(digest_size=6)
    for path in sorted(p for p in ctx.rglob("*") if p.is_file()):
        h.update(str(path.relative_to(ctx)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def tag(ctx: Path, spec: Spec) -> str:
    return f"{spec.name}:{digest(ctx)}"


def ensure(client: Client, spec: Spec, state: RunState) -> str:
    """The image's tag for this workspace, built if the daemon lacks it; its id in the state."""
    with tempfile.TemporaryDirectory(prefix="tiergen-image-") as tmp:
        ctx = context(Path(tmp), spec)
        found = tag(ctx, spec)
        existing = client.image_id(found)
        state.images[spec.name] = (
            existing if existing is not None else client.build_image(found, ctx)
        )
    return found
