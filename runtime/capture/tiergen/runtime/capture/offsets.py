"""Per-host clock offsets, written beside the captures so the join never guesses.

A Docker host shares the capture host's kernel clock, so its offset is zero by
construction and the method says so. A VM's clock is its own; measuring it is phase B's,
and until then its entry says ``unmeasured`` with no number rather than a zero.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from tiergen.core.codec import to_json
from tiergen.interfaces import RunState

OFFSETS = "offsets.json"


@dataclass(frozen=True, slots=True)
class ClockOffset:
    """Seconds to add to the host's wall clock to get the capture host's, and how it was
    known. ``None`` means not known, never zero."""

    offset_s: float | None
    method: str


def offsets(states: Mapping[str, RunState]) -> dict[str, ClockOffset]:
    found: dict[str, ClockOffset] = {}
    for backend, state in states.items():
        for instance in state.hosts:
            found[instance] = (
                ClockOffset(0.0, "shared-kernel")
                if backend == "docker"
                else ClockOffset(None, "unmeasured")
            )
    return found


def write_offsets(out: Path, found: Mapping[str, ClockOffset]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / OFFSETS).write_text(json.dumps(to_json(dict(found)), indent=2) + "\n", "utf-8")
