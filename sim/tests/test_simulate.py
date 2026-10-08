import json
from dataclasses import replace
from pathlib import Path

import pytest
from loop_support import EPOCH, FakeAttribution, FakeClock, FakeImpl, program

from tiergen.core.codec import decode
from tiergen.core.events import AppEvent, ConnEvent
from tiergen.core.loader import load_scenario
from tiergen.core.records import AttributionKey, InvocationRecord
from tiergen.core.resources import DirResources
from tiergen.impls._base import PrimitiveImpl
from tiergen.runtime.behaviour import BehaviourLoop
from tiergen.sim import Simulated, simulate, simulate_programs, write
from tiergen.sim.simulate import SimError

EXAMPLES = Path(__file__).parents[2] / "examples"
WS, WEB, ATK = "lab/workstation[0]", "lab/web_server[0]", "lab/attacker[0]"


def _through_the_loop(seed: int) -> list[InvocationRecord]:
    p = program(seed=seed, duration=3600)
    records: list[InvocationRecord] = []

    def primitive(impl_id: str) -> PrimitiveImpl:
        return FakeImpl()

    BehaviourLoop(
        p,
        p.behaviours[0],
        clock=FakeClock(),
        primitive=primitive,
        attribution=FakeAttribution(),
        sink=records.append,
    ).run()
    return records


def test_the_simulator_runs_the_loop_the_agent_runs() -> None:
    for seed in (1, 2):
        expected = _through_the_loop(seed)
        got, calls = simulate_programs({"lab/ws[0]": program(seed=seed, duration=3600)}, EPOCH)
        same = [
            replace(r, principal=AttributionKey("linux", f"fake:{r.key.invocation}")) for r in got
        ]
        assert same == expected
        assert set(calls) == {r.key.invocation for r in got}
        assert all(
            c.signature == "http.get" and c.params["path"] in ("/", "/news") for c in calls.values()
        )


@pytest.fixture(scope="module")
def slice_run() -> Simulated:
    scenario = load_scenario(EXAMPLES / "linux_slice" / "scenario.py")
    resources = DirResources(EXAMPLES / "linux_slice" / "models")
    return simulate(scenario, resources, duration_s=3600)


def test_linux_slice_simulated_browses_and_scans(slice_run: Simulated) -> None:
    sim = slice_run
    browsing = [r for r in sim.records if r.key.instance == WS]
    scans = [r for r in sim.records if r.key.instance == ATK]
    assert len(browsing) > 50
    assert {r.key.action for r in browsing} == {"web_get"}
    assert scans
    assert {r.key.action for r in scans} == {"syn_scan"}
    epoch = sim.records[0].start - sim.records[0].clock.monotonic
    assert min(r.start for r in scans) >= epoch + 30, "recon starts at 30 s"
    assert sim.records == sorted(sim.records, key=lambda r: (r.start, r.key.invocation))
    assert all(
        r.outcome == "succeeded" and r.principal.principal.startswith("sim:") for r in sim.records
    )

    ws, web, atk = (sim.plan.addresses[i]["lan"] for i in (WS, WEB, ATK))
    conns = [e for e in sim.events if isinstance(e, ConnEvent)]
    apps = [e for e in sim.events if isinstance(e, AppEvent)]
    http = [c for c in conns if c.five_tuple.orig_addr == ws]
    assert len(http) == len(browsing)
    assert {
        (c.five_tuple.resp_addr, c.five_tuple.resp_port, c.five_tuple.proto, c.state) for c in http
    } == {(web, 80, "tcp", "closed")}
    assert len({c.five_tuple.orig_port for c in http[:100]}) == 100
    probes = [c for c in conns if c.five_tuple.orig_addr == atk]
    assert len(probes) == 1024 * len(scans)
    assert {c.five_tuple.resp_port for c in probes} == set(range(1, 1025))
    assert all(c.state == "rejected" for c in probes)
    assert len(apps) == len(http)
    assert {a.flow for a in apps} == {c.flow for c in http}
    assert all(a.protocol == "http" and a.fields["method"] == "GET" for a in apps)
    uris = {str(a.fields["uri"]) for a in apps}
    assert uris == {"/", "/news"}
    assert all(e.flow.sensor == "sim" and e.flow.capture_point == "all" for e in sim.events)
    assert [e.ts if isinstance(e, AppEvent) else e.start for e in sim.events] == sorted(
        e.ts if isinstance(e, AppEvent) else e.start for e in sim.events
    )


def test_a_simulation_is_a_function_of_the_scenario_and_the_seed(slice_run: Simulated) -> None:
    scenario = load_scenario(EXAMPLES / "linux_slice" / "scenario.py")
    resources = DirResources(EXAMPLES / "linux_slice" / "models")
    again = simulate(scenario, resources, duration_s=3600)
    assert again.records == slice_run.records
    assert again.events == slice_run.events
    other = simulate(scenario, resources, duration_s=3600, seed=7)
    assert other.records != slice_run.records
    assert other.scenario.seed == 7
    only = simulate(scenario, resources, duration_s=600, instances=[WS])
    assert {r.key.instance for r in only.records} == {WS}
    assert set(only.programs) == {WS}
    with pytest.raises(SimError, match="no such instance"):
        simulate(scenario, resources, duration_s=1, instances=["lab/nobody[0]"])


def test_a_simulation_writes_a_run_directory_the_fit_can_read(
    slice_run: Simulated, tmp_path: Path
) -> None:
    write(slice_run, tmp_path / "run")
    run = tmp_path / "run"
    assert (run / "scenario.json").is_file()
    assert json.loads((run / "addresses.json").read_text())["addresses"][WS]["lan"]
    assert sorted(p.name for p in run.glob("program.*.json")) == [
        "program.lab-attacker-0.json",
        "program.lab-web_server-0.json",
        "program.lab-workstation-0.json",
    ]
    lines = (run / "out" / "lab-workstation-0" / "invocations.jsonl").read_text().splitlines()
    assert len(lines) == sum(1 for r in slice_run.records if r.key.instance == WS)
    assert (run / "out" / "lab-web_server-0" / "invocations.jsonl").read_text() == ""
    events = [
        decode(ConnEvent | AppEvent, json.loads(line))
        for line in (run / "sensors" / "sim" / "all" / "events.jsonl").read_text().splitlines()
    ]
    assert events == slice_run.events
