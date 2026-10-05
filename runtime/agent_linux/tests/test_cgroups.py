"""The cgroup context against a fake hierarchy. Linux only, like the agent."""

import logging
import os
import sys
from pathlib import Path

import pytest

from tiergen.runtime.agent_linux.cgroups import CgroupAttribution, PidAttribution, choose

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="the Linux agent's cgroups")


def _hierarchy(root: Path) -> Path:
    root.mkdir()
    (root / "cgroup.controllers").write_text("cpu memory pids\n")
    (root / "cgroup.procs").write_text("")
    return root


def test_each_invocation_gets_its_own_cgroup_and_the_process_comes_back(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    root = _hierarchy(tmp_path / "cg")
    log = logging.getLogger("test.cgroups")
    with caplog.at_level(logging.INFO, logger=log.name):
        attribution = choose(log, root)
    assert isinstance(attribution, CgroupAttribution)
    assert "cgroups under" in caplog.text
    with attribution.enter("lab/ws[0]/browse#1") as key:
        assert key.principal == "cgroup:/tiergen/lab-ws[0]-browse#1"
        procs = root / "tiergen" / "lab-ws[0]-browse#1" / "cgroup.procs"
        assert procs.read_text() == str(os.getpid())
        procs.unlink()  # a cgroup's virtual files vanish with it; a plain file would block rmdir
    assert not (root / "tiergen" / "lab-ws[0]-browse#1").exists()
    assert (root / "cgroup.procs").read_text() == str(os.getpid())


def test_without_a_writable_hierarchy_the_key_is_the_process_id(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    log = logging.getLogger("test.cgroups")
    (tmp_path / "v1").mkdir()
    with caplog.at_level(logging.WARNING, logger=log.name):
        attribution = choose(log, tmp_path / "v1")
    assert isinstance(attribution, PidAttribution)
    assert "not a cgroup v2 hierarchy" in caplog.text
    with attribution.enter("x") as key:
        assert key == key.__class__("linux", f"pid:{os.getpid()}")
    if os.geteuid() == 0:
        pytest.skip("root can write anywhere")
    sealed = _hierarchy(tmp_path / "sealed")
    sealed.chmod(0o555)
    try:
        with caplog.at_level(logging.WARNING, logger=log.name):
            attribution = choose(log, sealed)
    finally:
        sealed.chmod(0o755)
    assert isinstance(attribution, PidAttribution)
    assert "is not writable" in caplog.text
