"""``LinuxEbpfGuest``: the same collector inside a Linux guest, through the guest agent.

A guest's kernel is its own, so the collector runs there: ``start`` takes the binary out of
the collector image (built once by the Docker backend's image machinery, so nothing
compiles in the guest; a Debian guest with ``libbpf1`` and BTF runs it), writes it into
every Linux guest of the manifest through the agent, and starts it attached to the agent's
cgroup subtree, ``/sys/fs/cgroup/tiergen``, at depth 1, so every invocation's cgroup is a
child and the subtree's id is what events name the instance by. ``stop`` interrupts it and
pulls its events; ``records`` joins them per guest.
"""

import json
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from tiergen.backends.attrib._base import join, read_events
from tiergen.backends.attrib.linux_ebpf.backend import EVENTS, spec
from tiergen.backends.infra.docker import image
from tiergen.backends.infra.docker._client import Client as DockerClient
from tiergen.backends.infra.docker._client import DaemonClient
from tiergen.backends.infra.libvirt._client import Client as GuestClient
from tiergen.backends.infra.libvirt._client import LibvirtClient
from tiergen.core.codec import from_json, to_json
from tiergen.core.ir import Platform
from tiergen.core.program import flat_id
from tiergen.interfaces import AttributionRecord, BackendError, RunManifest, RunState

GUESTS = "guests.json"
COLLECTOR_IN_IMAGE = "/usr/local/bin/tiergen-attrib-collector"
COLLECTOR = "/tiergen/attrib-collector"
GUEST_EVENTS = "/tiergen/attrib-events.jsonl"
GUEST_LOG = "/tiergen/attrib.log"
SUBTREE = "/sys/fs/cgroup/tiergen"
READY_TIMEOUT = 20.0


@dataclass(frozen=True, slots=True)
class Guest:
    """A Linux guest the collector runs in: its domain, and the kernel id of the agent's
    cgroup subtree there, which every event names it by."""

    instance: str
    domain: str
    id: int


class LinuxEbpfGuest:
    platform: Platform = "linux"

    def __init__(
        self,
        docker: Callable[[], DockerClient] = DaemonClient,
        guests: Callable[[], GuestClient] = LibvirtClient,
    ) -> None:
        self._docker = docker
        self._guests = guests

    def start(self, manifest: RunManifest, state: RunState, run_dir: Path) -> None:
        out = run_dir.resolve() / "attrib"
        out.mkdir(parents=True, exist_ok=True)
        if (out / GUESTS).exists():
            raise BackendError(f"{out / GUESTS} exists: guest attribution already ran here")
        hosts = [h for h in manifest.hosts if h.platform == "linux" and h.agent]
        if not hosts:
            (out / GUESTS).write_text("[]\n", "utf-8")
            return
        docker = self._docker()
        tag = image.ensure(docker, spec(), state)
        binary = docker.archive(tag, COLLECTOR_IN_IMAGE)
        client = self._guests()
        guests: list[Guest] = []
        for host in hosts:
            domain = state.hosts[host.instance].name
            client.guest_write(domain, COLLECTOR, binary)
            # The agent makes the subtree when it starts, which may still be under way;
            # whichever comes first makes it.
            probe = client.guest_exec(
                domain,
                "/bin/sh",
                ["-c", f"chmod +x {COLLECTOR} && mkdir -p {SUBTREE} && stat -c %i {SUBTREE}"],
            )
            if probe.exit_code != 0:
                raise BackendError(
                    f"{domain}: no agent cgroup subtree at {SUBTREE}: {probe.err.strip()}"
                )
            started = client.guest_exec(
                domain,
                "/bin/sh",
                [
                    "-c",
                    f"nohup {COLLECTOR} --depth 1 --out {GUEST_EVENTS} {SUBTREE} "
                    f">{GUEST_LOG} 2>&1 &",
                ],
            )
            if started.exit_code != 0:
                raise BackendError(f"{domain}: cannot start the collector: {started.err.strip()}")
            deadline = time.monotonic() + READY_TIMEOUT
            while True:
                try:
                    head = client.guest_read(domain, GUEST_EVENTS)
                except BackendError:
                    head = b""
                if head.startswith(b"{"):
                    break
                if time.monotonic() > deadline:
                    log = client.guest_read(domain, GUEST_LOG).decode("utf-8", "replace")
                    raise BackendError(
                        f"{domain}: the collector did not start: {log.strip() or 'no output'}"
                    )
                time.sleep(0.2)
            guests.append(Guest(host.instance, domain, int(probe.out.strip())))
        (out / GUESTS).write_text(json.dumps(to_json(guests), indent=2) + "\n", "utf-8")

    def stop(self, run_dir: Path) -> None:
        out = run_dir / "attrib"
        guests = _guests(out)
        if not guests:
            return
        client = self._guests()
        for guest in guests:
            client.guest_exec(
                guest.domain, "/bin/sh", ["-c", f"pkill -INT -f {COLLECTOR}; sleep 1"]
            )
            events = client.guest_read(guest.domain, GUEST_EVENTS)
            target = out / "guests" / flat_id(guest.instance)
            target.mkdir(parents=True, exist_ok=True)
            (target / EVENTS).write_bytes(events)

    def records(self, run_dir: Path) -> Iterator[AttributionRecord]:
        out = run_dir / "attrib"
        for guest in _guests(out):
            path = out / "guests" / flat_id(guest.instance) / EVENTS
            if path.is_file():
                yield from join(read_events(path), {guest.id: guest.instance}).records


def _guests(out: Path) -> tuple[Guest, ...]:
    path = out / GUESTS
    if not path.is_file():
        return ()
    return from_json(tuple[Guest, ...], json.loads(path.read_text("utf-8")))
