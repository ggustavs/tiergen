import json
from collections.abc import Iterator, Mapping
from pathlib import Path

import pytest

from tiergen.backends.assemble import AssembleError, assemble
from tiergen.backends.assemble.assemble import FLAGGED, MANIFEST, RUN
from tiergen.core.addressing import plan_addresses
from tiergen.core.codec import from_json, to_json
from tiergen.core.events import ConnEvent, ConnState, Event, FiveTuple, SensorFlowId
from tiergen.core.ir import Platform, SensorSpec
from tiergen.core.labels import Flag, Label
from tiergen.core.loader import load_scenario
from tiergen.core.program import build_programs, programs_by_file
from tiergen.core.records import AttributionKey, ClockStamp, InvocationRecord, LabelKey
from tiergen.core.resolve import Resolver
from tiergen.core.resources import DirResources
from tiergen.core.routing import plan_routes
from tiergen.interfaces import AttributionRecord, HostState, RunManifest, RunRecord, RunState
from tiergen.interfaces.capability import Capability, CapabilityInfo
from tiergen.protocols import SIGNATURES
from tiergen.runtime.capture.dumpcap import CaptureState, Running
from tiergen.runtime.capture.offsets import ClockOffset, write_offsets

EXAMPLES = Path(__file__).parents[3] / "examples"
SERVERS = frozenset(s.id for s in SIGNATURES.values() if s.role == "server")
WS, WEB, ATK = "lab/workstation[0]", "lab/web_server[0]", "lab/attacker[0]"


class FakeSensor:
    """Yields the same two connections for every spec: the browsing and one probe."""

    def __init__(self, spec: SensorSpec, capture_point: str, addresses: dict[str, str]) -> None:
        self.id = spec.impl
        self.name = spec.name
        self.capture_point = capture_point
        self.version = spec.version
        self.addresses = addresses

    def run(self, pcap: Path, config: Path, out: Path) -> str:
        assert pcap.name == "lan-span.pcapng"
        out.mkdir(parents=True, exist_ok=True)
        return f"{self.id}@sha256:{self.name}"

    def capabilities(self) -> Mapping[Capability, CapabilityInfo]:
        return {}

    def ingest(self, native_logs: Path) -> Iterator[Event]:
        ws, web, atk = (self.addresses[i] for i in (WS, WEB, ATK))
        yield self._conn("c1", FiveTuple(ws, 40112, web, 80, "tcp"), 100.2, "closed")
        yield self._conn("c2", FiveTuple(atk, 50000, web, 22, "tcp"), 200.01, "rejected")
        yield self._conn(
            "c3", FiveTuple("10.20.0.1", 5353, "224.0.0.251", 5353, "udp"), 110.0, "other"
        )

    def flow_key(self, event: Event) -> SensorFlowId:
        return event.flow

    def _conn(self, native: str, five: FiveTuple, start: float, state: ConnState) -> ConnEvent:
        return ConnEvent(
            SensorFlowId(self.name, self.capture_point, native),
            five,
            start,
            1.0,
            1,
            1,
            1,
            1,
            state,
            {},  # type: ignore[arg-type]
        )


class FakeAttribution:
    platform: Platform = "linux"

    def __init__(self, addresses: dict[str, str]) -> None:
        self.addresses = addresses

    def start(self, manifest: RunManifest, state: RunState, run_dir: Path) -> None: ...

    def stop(self, run_dir: Path) -> None: ...

    def records(self, run_dir: Path) -> Iterator[AttributionRecord]:
        ws, web, atk = (self.addresses[i] for i in (WS, WEB, ATK))
        browse = FiveTuple(ws, 40112, web, 80, "tcp")
        yield AttributionRecord(
            WS, AttributionKey("linux", "cgroup:4242"), browse, 100.0, 100.9, 31
        )
        yield AttributionRecord(WEB, AttributionKey("linux", "cgroup:9"), browse, 100.0, 100.9, 12)
        yield AttributionRecord(
            ATK,
            AttributionKey("linux", "cgroup:7"),
            FiveTuple(atk, 50000, web, 22, "tcp"),
            200.0,
            200.0,
        )


def _invocation(
    instance: str, behaviour: str, action: str, n: int, cg: int, start: float, end: float
) -> InvocationRecord:
    key = LabelKey(
        "linux_slice", instance, behaviour, action, f"{instance}/{behaviour}#{n}", "x", None, (WEB,)
    )
    return InvocationRecord(
        key,
        AttributionKey("linux", f"cgroup:{cg}"),
        start,
        end,
        "succeeded",
        ClockStamp(start, 0.0, 0.0),
    )


@pytest.fixture
def run_dir(tmp_path: Path) -> Path:
    """A linux_slice run directory as build, a hand-driven run and capture stop leave it."""
    scenario = load_scenario(EXAMPLES / "linux_slice" / "scenario.py")
    resources = DirResources(EXAMPLES / "linux_slice" / "models")
    topology = Resolver(resources).topology(scenario)
    assert topology is not None
    plan, _ = plan_addresses(scenario, topology)
    routes, _ = plan_routes(scenario, topology, plan)
    programs = programs_by_file(
        build_programs(scenario, topology, plan, routes, Resolver(resources), SERVERS)
    )
    run = tmp_path / "run"
    run.mkdir()
    for name, value in [("scenario.json", scenario), ("addresses.json", plan), *programs.items()]:
        (run / name).write_text(json.dumps(to_json(value)))
    (run / "models").mkdir()
    for inst, lines in {
        "lab-workstation-0": [
            _invocation(WS, "browse", "web_get", 1, 4242, 99.9, 101.0),
            _invocation(WS, "browse", "web_get", 2, 4243, 150.0, 151.0),
        ],
        "lab-attacker-0": [_invocation(ATK, "recon", "syn_scan", 1, 7, 199.0, 230.0)],
    }.items():
        (run / "out" / inst).mkdir(parents=True)
        (run / "out" / inst / "invocations.jsonl").write_text(
            "".join(json.dumps(to_json(r)) + "\n" for r in lines)
        )
    capture = run / "capture"
    capture.mkdir()
    (capture / "lan-span.pcapng").write_bytes(b"")
    (capture / "capture.json").write_text(
        json.dumps(
            to_json(
                CaptureState(
                    "linux_slice",
                    90.0,
                    (
                        Running(
                            "lan-span", 0, "lan-span.pcapng", ("lan",), ("tg-lan",), (None,), False
                        ),
                    ),
                    400.0,
                )
            )
        )
    )
    write_offsets(capture, {i: ClockOffset(0.0, "shared-kernel") for i in (WS, WEB, ATK)})
    state = RunState(
        "linux_slice",
        "docker",
        {i: HostState(f"tiergen-linux_slice-{i}", f"id-{i}") for i in (WS, WEB, ATK)},
        {"lan": "tg-lan"},
        {"tiergen/base-linux": "sha256:agent", "tiergen/attrib-collector": "sha256:collector"},
    )
    (run / "state.docker.json").write_text(json.dumps(to_json(state)))
    return run


def _assemble(run: Path):
    plan = json.loads((run / "addresses.json").read_text())
    addresses = {i: by_seg["lan"] for i, by_seg in plan["addresses"].items()}
    return assemble(
        run,
        sensor_factory=lambda impl: lambda spec, point: FakeSensor(spec, point, addresses),
        attribution_loader=lambda wanted: {"linux_ebpf": FakeAttribution(addresses)},
    )


def test_the_assembly_writes_labels_per_sensor_the_flags_and_the_manifest(run_dir: Path) -> None:
    summary = _assemble(run_dir)
    assert summary.labels == {"zeek": 2, "suricata": 2}
    assert summary.flags == {"unattributed/no_attribution": 2, "failed/no_attribution": 1}
    for name in ("zeek", "suricata"):
        lines = (run_dir / f"labels.{name}.jsonl").read_text().splitlines()
        labels = [from_json(Label, json.loads(line)) for line in lines]
        assert [(lb.flow.native, lb.key.action, lb.signature) for lb in labels] == [
            ("c1", "web_get", "http.get"),
            ("c2", "syn_scan", "scan.tcp_syn"),
        ]
        assert all(lb.flow.sensor == name and lb.flow.capture_point == "lan-span" for lb in labels)
        assert (run_dir / "sensors" / name / "lan-span" / "events.jsonl").is_file()
    flags = [
        from_json(Flag, json.loads(line)) for line in (run_dir / FLAGGED).read_text().splitlines()
    ]
    assert [(f.kind, f.reason, f.flow.sensor if f.flow else f.invocation) for f in flags] == [
        ("unattributed", "no_attribution", "suricata"),
        ("unattributed", "no_attribution", "zeek"),
        ("failed", "no_attribution", "lab/workstation[0]/browse#2"),
    ]
    manifest = json.loads((run_dir / MANIFEST).read_text())
    assert (
        manifest["run"] == "linux_slice"
    )  # no run.json: a hand-driven run is named by its scenario
    assert (manifest["started"], manifest["ran_s"], manifest["duration_s"]) == (90.0, 310.0, 3600)
    assert manifest["scenario_sha256"].startswith("sha256:")
    assert "tiergen-assemble" in manifest["tool"]
    assert manifest["images"] == {
        "suricata:7.0.7": "suricata@sha256:suricata",
        "tiergen/attrib-collector": "sha256:collector",
        "tiergen/base-linux": "sha256:agent",
        "zeek:7.0.11": "zeek@sha256:zeek",
    }
    assert manifest["hosts"][WS] == {
        "backend": "docker",
        "name": f"tiergen-linux_slice-{WS}",
        "id": f"id-{WS}",
    }
    assert manifest["capture"] == {"lan-span": "lan-span.pcapng"}
    assert manifest["sensors"]["zeek"] == {
        "impl": "zeek",
        "version": "7.0.11",
        "image": "zeek:7.0.11",
        "digest": "zeek@sha256:zeek",
        "capabilities": ["APP_EVENTS"],
    }
    assert manifest["tolerance_s"] == 1.0
    assert manifest["counts"] == {
        "invocations": 3,
        "attribution": 3,
        "connections": {"zeek": 3, "suricata": 3},
        "labels": {"zeek": 2, "suricata": 2},
        "flags": {"unattributed/no_attribution": 2, "failed/no_attribution": 1},
    }
    assert manifest["absent"] == ["conformance.md", "fidelity.md"]


def test_a_run_record_names_the_run_and_carries_the_states(run_dir: Path) -> None:
    state = from_json(RunState, json.loads((run_dir / "state.docker.json").read_text()))
    (run_dir / "state.docker.json").unlink()
    (run_dir / RUN).write_text(
        json.dumps(
            to_json(
                RunRecord(
                    "linux_slice-20261008T090000Z", "linux_slice", 95.0, 60.0, {"docker": state}
                )
            )
        )
    )
    manifest = _assemble(run_dir).manifest
    assert (manifest.run, manifest.started, manifest.ran_s) == (
        "linux_slice-20261008T090000Z",
        95.0,
        60.0,
    )
    assert manifest.images["tiergen/base-linux"] == "sha256:agent"


def test_without_a_record_or_a_state_the_assembly_refuses(run_dir: Path) -> None:
    (run_dir / "state.docker.json").unlink()
    with pytest.raises(AssembleError, match=r"neither run\.json nor a run state"):
        _assemble(run_dir)


def test_an_unmeasured_clock_stops_the_join(run_dir: Path) -> None:
    write_offsets(run_dir / "capture", {WS: ClockOffset(None, "unmeasured")})
    with pytest.raises(AssembleError, match=r"offset of lab/workstation\[0\] is unmeasured"):
        _assemble(run_dir)
