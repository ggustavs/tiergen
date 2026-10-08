"""The run's manifest: what ran, from what, with what, and what came out. With the run
directory and the images it names, the dataset can be made again."""

import hashlib
from dataclasses import dataclass
from importlib.metadata import distributions
from pathlib import Path

ABSENT = ("conformance.md", "fidelity.md")
"""Reports the design lists under ``assemble`` that need measured implementation profiles
and a fitted model (M2, M3); named here so their absence is stated, not implied."""


@dataclass(frozen=True, slots=True)
class SensorEntry:
    """A sensor as it ran: the pinned image and the digest that actually ran, and the
    capabilities the scenario declared for this configuration."""

    impl: str
    version: str
    image: str
    digest: str
    capabilities: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HostEntry:
    backend: str
    name: str
    id: str


@dataclass(frozen=True, slots=True)
class Counts:
    """Flags are counted by ``kind/reason``."""

    invocations: int
    attribution: int
    connections: dict[str, int]
    labels: dict[str, int]
    flags: dict[str, int]


@dataclass(frozen=True, slots=True)
class Manifest:
    """``run`` is the run id; ``started`` and ``ran_s`` are when the agents were started on
    the capture host's clock and how long they ran, which is less than ``duration_s`` when
    the run was cut short. ``tool`` is every installed tiergen distribution by version.
    ``images`` is every image a host, collector or sensor ran from, by the name used, with
    the id or digest that ran."""

    run: str
    scenario: str
    seed: int
    duration_s: float
    started: float
    ran_s: float
    scenario_sha256: str
    tool: dict[str, str]
    images: dict[str, str]
    hosts: dict[str, HostEntry]
    capture: dict[str, str]
    sensors: dict[str, SensorEntry]
    tolerance_s: float
    counts: Counts
    absent: tuple[str, ...] = ABSENT


def tool_versions() -> dict[str, str]:
    found = {
        d.metadata["Name"]: d.version
        for d in distributions()
        if str(d.metadata["Name"]).startswith("tiergen-")
    }
    return dict(sorted(found.items()))


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
