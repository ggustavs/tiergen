import json
from collections.abc import Iterator, Sequence
from pathlib import Path

import pytest

from tiergen.backends.infra._base import build_manifests
from tiergen.core.addressing import plan_addresses
from tiergen.core.codec import from_json, to_json
from tiergen.core.ir import Platform
from tiergen.core.loader import load_scenario
from tiergen.core.resolve import Resolver
from tiergen.core.resources import DirResources
from tiergen.core.routing import plan_routes
from tiergen.impls._base import load_impls
from tiergen.interfaces import (
    AttributionRecord,
    BackendError,
    HostState,
    RunManifest,
    RunRecord,
    RunState,
)
from tiergen.runtime.capture.dumpcap import CaptureState, Running
from tiergen.runtime.capture.points import Point
from tiergen.runtime.scheduler import RUN, Ports, SchedulerError, run_id, run_scenario

EXAMPLES = Path(__file__).parents[3] / "examples"


class Clock:
    def __init__(self) -> None:
        self.t = 1_000_000.0

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += seconds


class FakeInfra:
    id = "docker"

    def __init__(self, seen: list[str]) -> None:
        self.seen = seen

    def up(self, manifest: RunManifest, run_dir: Path, start: bool = True) -> RunState:
        self.seen.append(f"up {manifest.run} start={start}")
        return RunState(
            manifest.run,
            self.id,
            {h.instance: HostState(f"c-{h.hostname}", f"id-{h.hostname}") for h in manifest.hosts},
            {n.name: n.bridge for n in manifest.networks},
            {"tiergen/base-linux": "sha256:agent"},
        )

    def start(self, manifest: RunManifest, state: RunState) -> None:
        self.seen.append(f"start {manifest.run}")

    def down(self, manifest: RunManifest) -> None:
        self.seen.append(f"down {manifest.run}")

    def quiesce(self, manifest: RunManifest, state: RunState) -> None:
        self.seen.append(f"quiesce {manifest.run}")


class FakeAttrib:
    platform: Platform = "linux"

    def __init__(self, seen: list[str]) -> None:
        self.seen = seen

    def start(self, manifest: RunManifest, state: RunState, run_dir: Path) -> None:
        self.seen.append(f"attrib start {len(state.hosts)}")
        state.images["tiergen/attrib-collector"] = "sha256:collector"

    def stop(self, run_dir: Path) -> None:
        self.seen.append("attrib stop")

    def records(self, run_dir: Path) -> Iterator[AttributionRecord]:
        yield from ()


class FakeCapture:
    def __init__(self, seen: list[str], clock: Clock, fail: bool = False) -> None:
        self.seen = seen
        self.clock = clock
        self.fail = fail

    def start(self, run: str, found: Sequence[Point], out: Path) -> CaptureState:
        self.seen.append(f"capture start {' '.join(p.name for p in found)}")
        if self.fail:
            raise BackendError("dumpcap is not installed")
        return CaptureState(
            run,
            self.clock.now(),
            tuple(
                Running(p.name, 0, f"{p.name}.pcapng", p.segments, p.bridges, p.vlans, p.tagged)
                for p in found
            ),
        )

    def stop(self, out: Path) -> CaptureState:
        self.seen.append("capture stop")
        running = Running("lan-span", 0, "lan-span.pcapng", ("lan",), ("tg-lan",), (None,), False)
        return CaptureState("r", 0.0, (running,), self.clock.now(), {"lan-span": 0})


@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    """linux_slice as tiergen build writes it, without the agents' programs."""
    scenario = load_scenario(EXAMPLES / "linux_slice" / "scenario.py")
    resources = DirResources(EXAMPLES / "linux_slice" / "models")
    topology = Resolver(resources).topology(scenario)
    assert topology is not None
    plan, _ = plan_addresses(scenario, topology)
    routes, _ = plan_routes(scenario, topology, plan)
    manifests = build_manifests(scenario, topology, plan, routes, load_impls(), resources)
    run = tmp_path / "run"
    run.mkdir()
    (run / "models").mkdir()
    (run / "scenario.json").write_text(json.dumps(to_json(scenario)))
    for backend, manifest in manifests.items():
        (run / f"manifest.{backend}.json").write_text(json.dumps(to_json(manifest)))
    return run


def _ports(seen: list[str], clock: Clock, fail_capture: bool = False) -> Ports:
    capture = FakeCapture(seen, clock, fail_capture)
    return Ports(
        infra=lambda only: {"docker": FakeInfra(seen)},
        attrib=lambda only: {"linux_ebpf": FakeAttrib(seen)},
        capture_start=capture.start,
        capture_stop=capture.stop,
        clock=clock.now,
        sleep=clock.sleep,
    )


def test_a_run_goes_up_in_order_waits_its_time_and_comes_down_in_reverse(run_dir: Path) -> None:
    seen: list[str] = []
    clock = Clock()
    lines: list[str] = []
    record = run_scenario(run_dir, 60, _ports(seen, clock), lines.append)
    assert seen == [
        "up linux_slice start=False",
        "attrib start 3",
        "quiesce linux_slice",
        "capture start lan-span",
        "start linux_slice",
        "capture stop",
        "attrib stop",
        "down linux_slice",
    ]
    assert record == from_json(RunRecord, json.loads((run_dir / RUN).read_text()))
    assert record.run == run_id("linux_slice", 1_000_000.0)
    assert (record.scenario, record.started, record.duration_s) == (
        "linux_slice",
        1_000_000.0,
        60.0,
    )
    assert record.states["docker"].images == {
        "tiergen/base-linux": "sha256:agent",
        "tiergen/attrib-collector": "sha256:collector",
    }
    assert set(record.states["docker"].hosts) == {
        "lab/workstation[0]",
        "lab/web_server[0]",
        "lab/attacker[0]",
    }
    assert not (run_dir / "state.docker.json").exists()
    offsets = json.loads((run_dir / "capture" / "offsets.json").read_text())
    assert offsets["lab/attacker[0]"] == {"offset_s": 0.0, "method": "shared-kernel"}
    assert "agents started; scenario time runs for 60 s" in lines
    assert "lan-span: capture/lan-span.pcapng, 0 packet(s) tagged" in lines


def test_without_a_length_the_run_lasts_the_scenario_s_duration(run_dir: Path) -> None:
    clock = Clock()
    record = run_scenario(run_dir, None, _ports([], clock))
    assert record.duration_s == 3600.0


def test_a_failure_on_the_way_up_takes_down_what_came_up_and_leaves_no_record(
    run_dir: Path,
) -> None:
    seen: list[str] = []
    with pytest.raises(BackendError, match="dumpcap is not installed"):
        run_scenario(run_dir, 60, _ports(seen, Clock(), fail_capture=True))
    assert seen == [
        "up linux_slice start=False",
        "attrib start 3",
        "quiesce linux_slice",
        "capture start lan-span",
        "attrib stop",
        "down linux_slice",
    ]
    assert not (run_dir / RUN).exists()
    assert not (run_dir / "state.docker.json").exists()


def test_the_run_id_is_the_scenario_and_the_utc_second_it_started() -> None:
    assert run_id("linux_slice", 1_790_000_000.0) == "linux_slice-20260921T141320Z"


def test_an_unbuilt_directory_is_refused_before_anything_is_loaded(tmp_path: Path) -> None:
    with pytest.raises(SchedulerError, match="holds no manifest"):
        run_scenario(tmp_path, 1, Ports(infra=lambda only: {}, attrib=lambda only: {}))
