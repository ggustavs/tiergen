"""The run ISO: what a guest gets of the run, as a read-only CD-ROM.

A guest has no mount of the run directory, so it receives a copy: the run's files (the IR,
the plan, the manifests, every program, the models), its own entry of the manifest with
addresses and MACs per attachment, the agent's wheels, and the bootstrap that applies all
of it. Written with xorriso (ISO 9660 with Rock Ridge and Joliet, so both Linux and Windows
read the names), then uploaded to the pool and attached to the domain.
"""

import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path

from tiergen.interfaces.infra import BackendError

LABEL = "TIERGEN"
SKIP = {"out", "capture", "attrib", "sensors", "fit", "run.json"}
"""What a run directory holds that a guest has no use for: outputs of this or earlier runs."""


def write_iso(target: Path, root: Path, label: str = LABEL) -> None:
    """``root``'s tree as an ISO at ``target``, with the volume label the guest mounts by."""
    if shutil.which("xorriso") is None:
        raise BackendError("xorriso is not installed; the libvirt backend writes a run ISO with it")
    command: Sequence[str] = [
        "xorriso",
        "-as",
        "mkisofs",
        "-quiet",
        "-o",
        str(target),
        "-V",
        label,
        "-r",
        "-J",
        "-joliet-long",
        str(root),
    ]
    done = subprocess.run(command, capture_output=True, text=True)
    if done.returncode != 0:
        raise BackendError(f"xorriso failed: {done.stderr.strip()}")


def stage_run(run_dir: Path, into: Path) -> None:
    """Copy the run directory's inputs under ``into/run``, outputs left out."""
    target = into / "run"
    target.mkdir(parents=True, exist_ok=True)
    for entry in run_dir.iterdir():
        if entry.name in SKIP or entry.name.startswith("state."):
            continue
        if entry.is_dir():
            shutil.copytree(entry, target / entry.name, dirs_exist_ok=True)
        else:
            shutil.copy2(entry, target / entry.name)
