"""The guest backend against a fake daemon (the collector image) and a fake guest agent."""

import json
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

from tiergen.backends.attrib.linux_ebpf import guest as module
from tiergen.backends.attrib.linux_ebpf.guest import COLLECTOR, GUEST_EVENTS, LinuxEbpfGuest
from tiergen.backends.infra.libvirt._client import Exec
from tiergen.interfaces import Attachment, BackendError, HostSpec, HostState, RunManifest, RunState

from .test_backend import START, line

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="the Linux collector")

WS = HostSpec(
    "lab/ws[0]",
    "ws",
    "linux",
    "lab-ws-0",
    "template:linux-agent",
    (),
    (),
    (Attachment("lan", "10.0.0.2"),),
    agent=True,
)
DC = HostSpec(
    "lab/dc[0]", "dc", "windows", "lab-dc-0", "win", (), (), (Attachment("lan", "10.0.0.10"),)
)
MANIFEST = RunManifest("r", "libvirt", (), (WS, DC))


def _state() -> RunState:
    return RunState(
        "r",
        "libvirt",
        hosts={
            "lab/ws[0]": HostState("tiergen-r-lab-ws-0", "u1"),
            "lab/dc[0]": HostState("d", "u2"),
        },
    )


class FakeDaemon:
    def image_id(self, tag: str) -> str | None:
        return "sha256:collector"

    def build_image(self, tag: str, context: Path) -> str:
        raise AssertionError("the image existed")

    def archive(self, image: str, path: str) -> bytes:
        assert path == "/usr/local/bin/tiergen-attrib-collector"
        return b"\x7fELF collector"


SUBTREE_FOUND = Exec(0, "4242\n", "")


class FakeGuests:
    def __init__(self, events: str = START, subtree: Exec = SUBTREE_FOUND) -> None:
        self.calls: list[tuple[object, ...]] = []
        self.files: dict[str, bytes] = {}
        self.events = events
        self.subtree = subtree

    def guest_write(self, domain: str, path: str, data: bytes) -> None:
        self.calls.append(("write", domain, path, data))

    def guest_exec(
        self, domain: str, path: str, args: Sequence[str] = (), timeout_s: float = 300.0
    ) -> Exec:
        self.calls.append(("exec", domain, args[-1]))
        if "stat -c %i" in args[-1]:
            return self.subtree
        if "nohup" in args[-1]:
            self.files[GUEST_EVENTS] = self.events.encode()
            return Exec(0, "", "")
        return Exec(0, "", "")

    def guest_read(self, domain: str, path: str) -> bytes:
        try:
            return self.files[path]
        except KeyError:
            raise BackendError(f"{path}: no such file") from None


def _backend(guests: FakeGuests) -> LinuxEbpfGuest:
    return LinuxEbpfGuest(FakeDaemon, lambda: guests)  # type: ignore[arg-type]


def test_start_puts_the_collector_in_every_linux_guest_on_the_agent_subtree(
    tmp_path: Path,
) -> None:
    guests = FakeGuests()
    state = _state()
    _backend(guests).start(MANIFEST, state, tmp_path)
    assert state.images["tiergen/attrib-linux"] == "sha256:collector"
    assert json.loads((tmp_path / "attrib" / "guests.json").read_text()) == [
        {"instance": "lab/ws[0]", "domain": "tiergen-r-lab-ws-0", "id": 4242}
    ]
    assert guests.calls[0] == ("write", "tiergen-r-lab-ws-0", COLLECTOR, b"\x7fELF collector")
    domains = {c[1] for c in guests.calls}
    assert domains == {"tiergen-r-lab-ws-0"}
    started = next(c[2] for c in guests.calls if c[0] == "exec" and "nohup" in str(c[2]))
    assert "--depth 1" in str(started)
    assert "/sys/fs/cgroup/tiergen" in str(started)
    with pytest.raises(BackendError, match="already ran"):
        _backend(guests).start(MANIFEST, state, tmp_path)


def test_stop_pulls_the_events_and_records_join_them_to_the_guest(tmp_path: Path) -> None:
    events = (
        START
        + line("connect", 5001, 4242, sk=7)
        + line("close", 5001, 4242, sk=7, ts_ns=1_700_000_001_000_000_000)
        + line("connect", 1, 9999)
    )
    guests = FakeGuests(events)
    backend = _backend(guests)
    backend.start(MANIFEST, _state(), tmp_path)
    backend.stop(tmp_path)
    assert ("exec", "tiergen-r-lab-ws-0", f"pkill -INT -f {COLLECTOR}; sleep 1") in guests.calls
    assert (tmp_path / "attrib" / "guests" / "lab-ws-0" / "events.jsonl").read_text() == events
    records = list(backend.records(tmp_path))
    assert [(r.instance, r.principal.principal) for r in records] == [("lab/ws[0]", "cgroup:5001")]
    assert records[0].end - records[0].start == pytest.approx(1.0)


def test_a_guest_without_the_subtree_or_a_silent_collector_is_an_error(tmp_path: Path) -> None:
    missing = FakeGuests(subtree=Exec(1, "", "stat: cannot statx: No such file"))
    with pytest.raises(BackendError, match="no agent cgroup subtree"):
        _backend(missing).start(MANIFEST, _state(), tmp_path)
    silent = FakeGuests(events="")
    silent.files[module.GUEST_LOG] = b"libbpf: failed to load"
    module.READY_TIMEOUT = 0.3
    try:
        with pytest.raises(BackendError, match="did not start: libbpf: failed to load"):
            _backend(silent).start(MANIFEST, _state(), tmp_path / "b")
    finally:
        module.READY_TIMEOUT = 20.0


def test_a_manifest_without_linux_agents_records_nothing(tmp_path: Path) -> None:
    guests = FakeGuests()
    backend = _backend(guests)
    backend.start(RunManifest("r", "libvirt", (), (DC,)), _state(), tmp_path)
    assert guests.calls == []
    backend.stop(tmp_path)
    assert list(backend.records(tmp_path)) == []
