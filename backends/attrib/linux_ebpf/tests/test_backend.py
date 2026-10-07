"""The backend against a fake daemon and a fake cgroup lookup; the C runs in the daemon test.

Linux only, like the backend: cgroups and /proc.
"""

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest

from tiergen.backends.attrib.linux_ebpf.backend import LinuxEbpf, cgroup_of, helper_name, spec
from tiergen.interfaces import Attachment, BackendError, HostSpec, RunManifest, RunState

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="the Linux collector")

MANIFEST = RunManifest(
    "r",
    "docker",
    (),
    (
        HostSpec(
            "lab/ws[0]",
            "ws",
            "linux",
            "lab-ws-0",
            "img",
            (),
            (),
            (Attachment("lan", "10.0.0.2"),),
            agent=True,
        ),
        HostSpec(
            "lab/web[0]",
            "web",
            "linux",
            "lab-web-0",
            "img",
            (),
            (),
            (Attachment("lan", "10.0.0.80"),),
            agent=True,
        ),
    ),
)
PIDS = {"tiergen-r-lab-ws-0": 4001, "tiergen-r-lab-web-0": 4002}
CGROUPS = {
    4001: ("/system.slice/docker-aaa.scope", 1001),
    4002: ("/system.slice/docker-bbb.scope", 1002),
}


class FakeDaemon:
    """Only what the attribution backend asks of the facade."""

    def __init__(self, events: str = "", pids: Mapping[str, int] = PIDS) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.events = events
        self.pids = pids
        self.live: set[str] = set()

    def image_id(self, tag: str) -> str | None:
        return "sha256:collector"

    def build_image(self, tag: str, context: Path) -> str:
        raise AssertionError("the image existed")

    def pid(self, container: str) -> int:
        try:
            return self.pids[container]
        except KeyError:
            raise BackendError(f"container {container!r} does not exist") from None

    def start_helper(
        self,
        name: str,
        image: str,
        command: Sequence[str],
        labels: Mapping[str, str],
        mounts: Sequence[tuple[Path, str, bool]],
    ) -> str:
        self.calls.append(
            (
                "start",
                name,
                image,
                tuple(command),
                dict(labels),
                tuple((str(s), t, ro) for s, t, ro in mounts),
            )
        )
        self.live.add(name)
        out = next(Path(s) for s, t, _ in mounts if t == "/tiergen/attrib")
        (out / "events.jsonl").write_text(self.events)
        return "id-" + name

    def stop_helper(self, name: str, timeout: float = 10.0) -> None:
        self.calls.append(("stop", name))
        self.live.discard(name)

    def remove_container(self, name: str) -> None:
        self.calls.append(("rm", name))

    def logs(self, container: str) -> str:
        return "the collector said something"


def _line(ev: str, cg: int, container: int, **f: object) -> str:
    base: dict[str, object] = {
        "ev": ev,
        "ts_ns": 1_700_000_000_000_000_000,
        "cg": cg,
        "container_cg": container,
        "pid": 9,
        "tgid": 9,
        "proto": "tcp",
        "src": "10.0.0.2",
        "sport": 40000,
        "dst": "10.0.0.80",
        "dport": 80,
        "sk": 0,
    }
    base.update(f)
    return json.dumps(base) + "\n"


START = _line("start", 0, 0, proto="other", src="", dst="", sport=0, dport=0)


def test_start_finds_the_cgroups_and_runs_the_collector_on_them(tmp_path: Path) -> None:
    fake = FakeDaemon(START)
    backend = LinuxEbpf(lambda: fake, CGROUPS.__getitem__, cgroup_root=Path("/cg"))  # type: ignore[arg-type]
    state = RunState("r", "docker")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "scenario.json").write_text(json.dumps({"name": "r"}))
    backend.start(MANIFEST, state, run_dir)
    containers = json.loads((run_dir / "attrib" / "containers.json").read_text())
    assert containers == [
        {"instance": "lab/ws[0]", "cgroup": "/system.slice/docker-aaa.scope", "id": 1001},
        {"instance": "lab/web[0]", "cgroup": "/system.slice/docker-bbb.scope", "id": 1002},
    ]
    assert state.images["tiergen/attrib-linux"] == "sha256:collector"
    [(kind, name, image, command, labels, mounts)] = fake.calls
    assert (kind, name) == ("start", "tiergen-r-attrib")
    assert isinstance(image, str)
    assert image.startswith("tiergen/attrib-linux:")
    assert command == (
        "tiergen-attrib-collector",
        "--depth",
        "2",
        "--out",
        "/tiergen/attrib/events.jsonl",
        "/cg/system.slice/docker-aaa.scope",
        "/cg/system.slice/docker-bbb.scope",
    )
    assert labels == {"tiergen.run": "r"}
    assert mounts == (
        ("/cg", "/cg", True),
        (str(run_dir.resolve() / "attrib"), "/tiergen/attrib", False),
    )

    backend.stop(run_dir)
    assert fake.calls[1:] == [("stop", "tiergen-r-attrib"), ("rm", "tiergen-r-attrib")]
    with pytest.raises(BackendError, match="already ran"):
        backend.start(MANIFEST, state, run_dir)


def test_records_join_the_events_to_the_run_containers(tmp_path: Path) -> None:
    events = (
        START
        + _line("connect", 5001, 1001, sk=7)
        + _line("close", 5001, 1001, sk=7, ts_ns=1_700_000_001_000_000_000)
        + _line("packet", 6001, 1002, src="10.0.0.80")
        + _line("connect", 1, 9999)
    )
    fake = FakeDaemon(events)
    backend = LinuxEbpf(lambda: fake, CGROUPS.__getitem__)  # type: ignore[arg-type]
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "scenario.json").write_text(json.dumps({"name": "r"}))
    backend.start(MANIFEST, RunState("r", "docker"), run_dir)
    records = list(backend.records(run_dir))
    assert [(r.instance, r.principal.principal) for r in records] == [
        ("lab/ws[0]", "cgroup:5001"),
        ("lab/web[0]", "cgroup:6001"),
    ]
    assert records[0].end - records[0].start == pytest.approx(1.0)


def test_a_collector_that_never_starts_is_an_error_with_its_output(tmp_path: Path) -> None:
    fake = FakeDaemon("")
    backend = LinuxEbpf(lambda: fake, CGROUPS.__getitem__)  # type: ignore[arg-type]
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "scenario.json").write_text(json.dumps({"name": "r"}))
    import tiergen.backends.attrib.linux_ebpf.backend as module

    module.READY_TIMEOUT = 0.3
    try:
        with pytest.raises(BackendError, match="did not start: the collector said something"):
            backend.start(MANIFEST, RunState("r", "docker"), run_dir)
    finally:
        module.READY_TIMEOUT = 20.0
    assert ("rm", "tiergen-r-attrib") in fake.calls


def test_the_cgroup_of_this_process_is_found_and_the_image_spec_carries_the_sources() -> None:
    if not Path("/sys/fs/cgroup/cgroup.controllers").is_file():
        pytest.skip("no cgroup v2 here")
    import os

    path, cgroup_id = cgroup_of(os.getpid())
    assert path.startswith("/")
    assert cgroup_id > 0
    assert helper_name("linux_slice") == "tiergen-linux_slice-attrib"
    assert {where for where, _ in spec().files} == {
        "bpf/attrib.bpf.c",
        "bpf/collector.c",
        "bpf/vmlinux_min.h",
        "bpf/Makefile",
    }
    assert all(source.is_file() for _, source in spec().files)
