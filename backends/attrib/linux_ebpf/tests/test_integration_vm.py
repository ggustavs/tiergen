"""Against the system libvirt and a daemon: ``vm_slice`` from one command to labels.

A Linux guest browses a container's web server; the collector runs inside the guest and
the labels name its invocations. Skipped without libvirt, the ``tiergen`` pool, the Linux
template, xorriso, dumpcap, or a daemon with its user-namespace remap.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from tiergen.backends.attrib.linux_ebpf.backend import spec
from tiergen.backends.infra.docker import image
from tiergen.backends.infra.docker._client import DaemonClient
from tiergen.backends.infra.docker.backend import DockerBackend
from tiergen.backends.infra.libvirt._client import LibvirtClient
from tiergen.backends.infra.libvirt.backend import POOL, LibvirtBackend
from tiergen.cli.main import main
from tiergen.core.codec import from_json
from tiergen.core.labels import Flag, Label
from tiergen.interfaces import BackendError, RunManifest, RunRecord, RunState

EXAMPLES = Path(__file__).parents[4] / "examples"
pytestmark = [pytest.mark.vm, pytest.mark.docker]


@pytest.fixture(scope="module")
def guests() -> LibvirtClient:
    try:
        c = LibvirtClient()
        volumes = c.volumes(POOL)
    except BackendError as err:
        pytest.skip(str(err))
    if "template-linux-agent.qcow2" not in volumes:
        pytest.skip("the Linux agent template is not in the pool")
    for tool in ("xorriso", "dumpcap"):
        if shutil.which(tool) is None:
            pytest.skip(f"{tool} is not installed")
    return c


@pytest.fixture(scope="module")
def daemon() -> DaemonClient:
    try:
        client = DaemonClient()
    except BackendError as err:
        pytest.skip(str(err))
    if client.userns() is None:
        pytest.skip("the daemon runs without a user-namespace remap (design decision 4.19)")
    return client


def _release(out: Path, image: str, depth: int) -> None:
    """What the containers wrote belongs to the remapped root; a container as that root
    removes it."""
    subprocess.run(
        [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{out}:/o",
            image,
            "find",
            "/o",
            "-mindepth",
            str(depth),
            "-delete",
        ],
        check=True,
        capture_output=True,
    )


def test_vm_slice_from_one_command_to_labels(
    tmp_path: Path, guests: LibvirtClient, daemon: DaemonClient
) -> None:
    run_dir = tmp_path / "vm"
    assert main(["build", str(EXAMPLES / "vm_slice" / "scenario.py"), "--out", str(run_dir)]) == 0
    manifests = {
        b: from_json(RunManifest, json.loads((run_dir / f"manifest.{b}.json").read_text()))
        for b in ("docker", "libvirt")
    }
    assert [h.instance for h in manifests["libvirt"].hosts] == ["lab/workstation[0]"]
    # Both images first, so the collector starts seconds after the hosts.
    image.ensure(daemon, image.agent(), RunState("prebuild", "docker"))
    image.ensure(daemon, spec(), RunState("prebuild", "docker"))
    agent: str | None = None
    try:
        assert main(["run", str(run_dir), "--for", "60"]) == 0
        assert not [d for d in guests.domains() if d.startswith("tiergen-vm_slice-")]
        assert not [v for v in guests.volumes(POOL) if v.startswith("tiergen-vm_slice-")]
        record = from_json(RunRecord, json.loads((run_dir / "run.json").read_text()))
        agent = record.states["docker"].images[image.NAME]
        assert set(record.states) == {"docker", "libvirt"}
        ws = record.states["libvirt"].hosts["lab/workstation[0]"]
        assert ws.clock_offset_s is not None
        assert abs(ws.clock_offset_s) < 2.0
        offsets = json.loads((run_dir / "capture" / "offsets.json").read_text())
        assert offsets["lab/workstation[0]"]["method"] == "guest-agent"
        assert offsets["lab/web_server[0]"]["method"] == "shared-kernel"
        # The collector ran in the guest: its events came back through the agent.
        [guest] = json.loads((run_dir / "attrib" / "guests.json").read_text())
        assert guest["instance"] == "lab/workstation[0]"
        assert guest["id"] > 0
        assert (run_dir / "attrib" / "guests" / "lab-workstation-0" / "events.jsonl").is_file()
        assert (run_dir / "out" / "lab-workstation-0" / "invocations.jsonl").is_file()

        assert main(["assemble", str(run_dir)]) == 0
        summary = json.loads((run_dir / "manifest.json").read_text())
        assert summary["counts"]["invocations"] > 0
        for name in ("zeek", "suricata"):
            labels = [
                from_json(Label, json.loads(line))
                for line in (run_dir / f"labels.{name}.jsonl").read_text().splitlines()
            ]
            browsing = [lb for lb in labels if lb.signature == "http.get"]
            assert browsing, name
            assert {lb.key.instance for lb in browsing} == {"lab/workstation[0]"}
            assert {(lb.key.behaviour, lb.key.action, lb.key.impl) for lb in browsing} == {
                ("browse", "web_get", "http.httpx")
            }
            assert all(re.fullmatch(r"cgroup:\d+", lb.principal.principal) for lb in browsing)
        flags = [
            from_json(Flag, json.loads(line))
            for line in (run_dir / "flagged.jsonl").read_text().splitlines()
        ]
        assert not [f for f in flags if f.kind == "failed"], flags[:5]
        # The guest's OS does its own talking (NTP, link-local); none of it is an invocation.
        assert {(f.kind, f.reason) for f in flags} <= {("unattributed", "no_attribution")}, flags[
            :5
        ]

        assert main(["fit", str(run_dir), "--sensor", "zeek", "--out", str(run_dir / "fit")]) == 0
        states = json.loads((run_dir / "fit" / "workstation.browse.states.json").read_text())
        assert states == ["web_get"]
        print(
            f"vm_slice: {len(browsing)} browsing labels from the guest in suricata, "
            f"{len(flags)} flag(s), offset {ws.clock_offset_s:+.3f} s"
        )
    finally:
        LibvirtBackend().down(manifests["libvirt"])
        DockerBackend().down(manifests["docker"])
        if agent is not None:
            # Only the container's directory: the guest's outputs were unpacked by the user.
            _release(run_dir / "out" / "lab-web_server-0", agent, depth=1)
            if (run_dir / "sensors").is_dir():
                _release(run_dir / "sensors", agent, depth=3)
