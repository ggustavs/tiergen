"""dumpcap at the capture points: start them detached, stop them, finish the files.

One dumpcap per point writes ``<point>.pcapng`` with one interface per segment, in the
point's order, so interface id i is segment i. ``state.json`` holds the pids while the
capture runs; ``stop`` sends SIGINT, which makes dumpcap close the file cleanly, inserts the
802.1Q tags for tagged points, and leaves ``capture.json`` behind. Only a process whose
command line says dumpcap is ever signalled, so a reused pid is never shot.
"""

import json
import os
import signal
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path

from tiergen.core.codec import from_json, to_json
from tiergen.runtime.capture.pcapng import insert_tags
from tiergen.runtime.capture.points import CaptureError, Point

STATE = "state.json"
SUMMARY = "capture.json"
Spawn = Callable[[Sequence[str], Path], int]
"""Start a command detached with its stderr going to the given log file; the pid."""


@dataclass(frozen=True, slots=True)
class Running:
    point: str
    pid: int
    file: str
    segments: tuple[str, ...]
    bridges: tuple[str, ...]
    vlans: tuple[int | None, ...]
    tagged: bool


@dataclass(frozen=True, slots=True)
class CaptureState:
    """What is, or was, capturing: written while dumpcap runs and rewritten when stopped,
    with the count of packets each tagged point got its tags on."""

    run: str
    started: float
    captures: tuple[Running, ...]
    stopped: float | None = None
    tagged_packets: dict[str, int] = field(default_factory=dict[str, int])


def command(point: Point, file: Path) -> list[str]:
    args = ["dumpcap", "-q", "-w", str(file)]
    for bridge in point.bridges:
        args += ["-i", bridge]
    return args


def spawn(args: Sequence[str], log: Path) -> int:
    with log.open("ab") as err:
        return subprocess.Popen(
            list(args), stdout=subprocess.DEVNULL, stderr=err, start_new_session=True
        ).pid


def _alive(pid: int) -> bool:
    try:
        reaped, _ = os.waitpid(pid, os.WNOHANG)  # our child: reap it if it has exited
        if reaped == pid:
            return False
    except ChildProcessError:
        pass  # not our child: ask the kernel
    try:
        state = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[0]
    except OSError:
        return False
    return state != "Z"


def _is_dumpcap(pid: int) -> bool:
    try:
        return b"dumpcap" in Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return False


def _tail(log: Path) -> str:
    try:
        return log.read_text("utf-8", "replace").strip().splitlines()[-1]
    except (OSError, IndexError):
        return "no output"


def start(
    run: str, points: Sequence[Point], out: Path, spawner: Spawn = spawn, settle: float = 0.5
) -> CaptureState:
    """Start one dumpcap per point under ``out`` and record them in ``state.json``."""
    out.mkdir(parents=True, exist_ok=True)
    if (out / STATE).exists():
        raise CaptureError(f"{out / STATE} exists: a capture is running; stop it first")
    captures: list[Running] = []
    for point in points:
        file = out / f"{point.name}.pcapng"
        pid = spawner(command(point, file), out / f"{point.name}.log")
        captures.append(
            Running(
                point.name, pid, file.name, point.segments, point.bridges, point.vlans, point.tagged
            )
        )
    time.sleep(settle)
    dead = [c for c in captures if not _alive(c.pid)]
    if dead:
        for c in captures:
            if _alive(c.pid):
                os.kill(c.pid, signal.SIGINT)
        raise CaptureError(
            "; ".join(
                f"dumpcap for {c.point!r} exited: {_tail(out / f'{c.point}.log')}" for c in dead
            )
        )
    state = CaptureState(run, time.time(), tuple(captures))
    (out / STATE).write_text(json.dumps(to_json(state), indent=2) + "\n", "utf-8")
    return state


def stop(out: Path, timeout: float = 30.0) -> CaptureState:
    """Stop the capture recorded in ``out/state.json``, tag what needs tagging, and leave
    ``capture.json``."""
    path = out / STATE
    if not path.is_file():
        raise CaptureError(f"{path} is missing: nothing is capturing")
    state = from_json(CaptureState, json.loads(path.read_text("utf-8")))
    for c in state.captures:
        if _alive(c.pid) and _is_dumpcap(c.pid):
            os.kill(c.pid, signal.SIGINT)
    deadline = time.monotonic() + timeout
    while any(_alive(c.pid) and _is_dumpcap(c.pid) for c in state.captures):
        if time.monotonic() > deadline:
            for c in state.captures:
                if _alive(c.pid) and _is_dumpcap(c.pid):
                    os.kill(c.pid, signal.SIGTERM)
            break
        time.sleep(0.1)
    tagged: dict[str, int] = {}
    for c in state.captures:
        file = out / c.file
        if not file.is_file():
            raise CaptureError(f"{file} was not written; see {out / f'{c.point}.log'}")
        if c.tagged:
            vlans = {i: v for i, v in enumerate(c.vlans) if v is not None}
            draft = file.with_suffix(".tagging")
            tagged[c.point] = insert_tags(file, draft, vlans)
            os.replace(draft, file)
    final = replace(state, stopped=time.time(), tagged_packets=tagged)
    (out / SUMMARY).write_text(json.dumps(to_json(final), indent=2) + "\n", "utf-8")
    path.unlink()
    return final
