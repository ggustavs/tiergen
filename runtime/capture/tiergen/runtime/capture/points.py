"""Which bridges each capture point listens on, read from the run directory alone.

The scenario names its capture points; the topology says which segments each observes and
whether frames reach the sensor tagged; the run state says which Linux bridge each segment
became. Nothing else is needed, and nothing here talks to a daemon.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from tiergen.core.codec import from_json
from tiergen.core.ir import Scenario, Topology
from tiergen.core.resolve import Resolver
from tiergen.core.resources import DirResources
from tiergen.interfaces import RunState


class CaptureError(RuntimeError):
    """Capture cannot proceed; the message says what is missing or what failed."""


@dataclass(frozen=True, slots=True)
class Point:
    """One capture point as dumpcap sees it: the segments in the order the file's
    interfaces will have, the bridge of each, the VLAN id of each (None if untagged), and
    whether the sensor gets the frames tagged."""

    name: str
    segments: tuple[str, ...]
    bridges: tuple[str, ...]
    vlans: tuple[int | None, ...]
    tagged: bool

    @property
    def vlan_by_interface(self) -> dict[int, int]:
        return {i: v for i, v in enumerate(self.vlans) if v is not None}


@dataclass(frozen=True, slots=True)
class Run:
    """A run directory after ``tiergen infra up``: the IR, its topology, and one run state
    per backend that is up."""

    scenario: Scenario
    topology: Topology
    states: dict[str, RunState] = field(default_factory=dict[str, RunState])

    @property
    def bridges(self) -> dict[str, str]:
        """Segment to bridge over every backend; they share bridges by name (section 10)."""
        found: dict[str, str] = {}
        for state in self.states.values():
            found.update(state.bridges)
        return found


def load_run(run_dir: Path) -> Run:
    scenario = from_json(Scenario, json.loads((run_dir / "scenario.json").read_text("utf-8")))
    topology = Resolver(DirResources(run_dir / "models")).topology(scenario)
    if topology is None:
        raise CaptureError(f"{run_dir}: the scenario's topology does not resolve")
    states = {
        p.name[len("state.") : -len(".json")]: from_json(RunState, json.loads(p.read_text("utf-8")))
        for p in sorted(run_dir.glob("state.*.json"))
    }
    if not states:
        raise CaptureError(f"{run_dir}: no run state; is the run up?")
    return Run(scenario, topology, states)


def capture_points(
    scenario: Scenario, topology: Topology, bridges: Mapping[str, str]
) -> list[Point]:
    """The scenario's active capture points over the bridges the run state names."""
    segments = {s.name: s for s in topology.segments}
    by_name = {cp.name: cp for cp in topology.capture_points}
    points: list[Point] = []
    for name in scenario.capture_points:
        cp = by_name[name]  # check 9 held the name
        missing = [s for s in cp.segments if s not in bridges]
        if missing:
            raise CaptureError(
                f"capture point {name!r}: no bridge in the run state for {', '.join(missing)}"
            )
        points.append(
            Point(
                name,
                tuple(cp.segments),
                tuple(bridges[s] for s in cp.segments),
                tuple(segments[s].vlan for s in cp.segments),
                cp.tagged,
            )
        )
    return points
