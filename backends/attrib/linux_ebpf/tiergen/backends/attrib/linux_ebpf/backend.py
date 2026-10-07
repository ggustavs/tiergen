"""``LinuxEbpf``: the collector as a privileged helper through the Docker daemon.

``start`` finds each container's cgroup through its init process (``/proc/<pid>/cgroup`` on
the host) and the cgroup's kernel id by ``stat``, writes them to ``attrib/containers.json``,
and starts the collector with those cgroups, the host's cgroup tree read-only, and the run's
``attrib/`` directory for its events; it waits for the collector's ``start`` line. ``stop``
stops and removes the helper. ``records`` joins the events against the containers.
"""

import json
import os
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from tiergen.backends.attrib._base import join, read_events
from tiergen.backends.infra.docker import image
from tiergen.backends.infra.docker._client import Client, DaemonClient
from tiergen.backends.infra.docker.backend import RUN_LABEL, container_name
from tiergen.core.codec import from_json, to_json
from tiergen.core.ir import Platform
from tiergen.interfaces import AttributionRecord, BackendError, RunManifest, RunState

NAME = "tiergen/attrib-linux"
CGROUP_ROOT = Path("/sys/fs/cgroup")
EVENTS = "events.jsonl"
CONTAINERS = "containers.json"
ATTRIB_MOUNT = "/tiergen/attrib"
READY_TIMEOUT = 20.0


def spec() -> image.Spec:
    """The collector image: its Dockerfile and the ``bpf`` sources, nothing from Python."""
    bpf = files(__package__) / "bpf"
    sources = tuple(
        (f"bpf/{name}", Path(str(bpf / name)))
        for name in ("attrib.bpf.c", "collector.c", "vmlinux_min.h", "Makefile")
    )
    return image.Spec(NAME, (files(__package__) / "Dockerfile").read_text("utf-8"), (), sources)


@dataclass(frozen=True, slots=True)
class Container:
    """A run container as the collector needs it: its cgroup on the host, and that cgroup's
    kernel id, which is what every event names it by."""

    instance: str
    cgroup: str
    id: int


def cgroup_of(pid: int, root: Path = CGROUP_ROOT) -> tuple[str, int]:
    """The cgroup v2 path of a process and the cgroup's kernel id, from the host."""
    for line in Path(f"/proc/{pid}/cgroup").read_text("utf-8").splitlines():
        hierarchy, _, path = line.partition(":")
        if hierarchy == "0":
            _, _, path = path.partition(":")
            return path, os.stat(root / path.lstrip("/")).st_ino
    raise BackendError(f"process {pid} is not in a cgroup v2 hierarchy")


def helper_name(run: str) -> str:
    return f"tiergen-{run}-attrib"


class LinuxEbpf:
    platform: Platform = "linux"

    def __init__(
        self,
        client: Callable[[], Client] = DaemonClient,
        cgroup: Callable[[int], tuple[str, int]] = cgroup_of,
        cgroup_root: Path = CGROUP_ROOT,
    ) -> None:
        self._connect = client
        self._cgroup = cgroup
        self._root = cgroup_root

    def start(self, manifest: RunManifest, state: RunState, run_dir: Path) -> None:
        client = self._connect()
        out = run_dir.resolve() / "attrib"
        out.mkdir(parents=True, exist_ok=True)
        if (out / EVENTS).exists():
            raise BackendError(f"{out / EVENTS} exists: attribution already ran here")
        containers: list[Container] = []
        for host in manifest.hosts:
            pid = client.pid(container_name(manifest.run, host.instance))
            path, cgroup_id = self._cgroup(pid)
            containers.append(Container(host.instance, path, cgroup_id))
        depths = {c.cgroup.strip("/").count("/") + 1 for c in containers}
        if len(depths) != 1:
            raise BackendError(f"the containers' cgroups sit at different depths: {sorted(depths)}")
        (out / CONTAINERS).write_text(json.dumps(to_json(containers), indent=2) + "\n", "utf-8")
        tag = image.ensure(client, spec(), state)
        command = [
            "tiergen-attrib-collector",
            "--depth",
            str(depths.pop()),
            "--out",
            f"{ATTRIB_MOUNT}/{EVENTS}",
            *(str(self._root / c.cgroup.lstrip("/")) for c in containers),
        ]
        client.start_helper(
            helper_name(manifest.run),
            tag,
            command,
            {RUN_LABEL: manifest.run},
            [(self._root, str(self._root), True), (out, ATTRIB_MOUNT, False)],
        )
        deadline = time.monotonic() + READY_TIMEOUT
        while not (out / EVENTS).is_file() or not (out / EVENTS).read_text("utf-8").startswith("{"):
            if time.monotonic() > deadline:
                logs = client.logs(helper_name(manifest.run))
                client.remove_container(helper_name(manifest.run))
                raise BackendError(f"the collector did not start: {logs.strip() or 'no output'}")
            time.sleep(0.2)

    def stop(self, run_dir: Path) -> None:
        client = self._connect()
        state = json.loads((run_dir / "attrib" / CONTAINERS).read_text("utf-8"))
        run = _run_of(run_dir)
        del state
        client.stop_helper(helper_name(run))
        client.remove_container(helper_name(run))

    def records(self, run_dir: Path) -> Iterator[AttributionRecord]:
        out = run_dir / "attrib"
        containers = from_json(
            tuple[Container, ...], json.loads((out / CONTAINERS).read_text("utf-8"))
        )
        joined = join(read_events(out / EVENTS), {c.id: c.instance for c in containers})
        yield from joined.records


def _run_of(run_dir: Path) -> str:
    return json.loads((run_dir / "scenario.json").read_text("utf-8"))["name"]
