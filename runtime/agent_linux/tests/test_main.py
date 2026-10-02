"""The agent process end to end, without a container: services, forked behaviours, records.

Linux only, like the agent: it forks.
"""

import logging
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from agent_support import FakeAttribution, FakeImpl, FakeService, program

from tiergen.impls._base import PrimitiveImpl, ServiceImpl
from tiergen.runtime.agent_linux.main import run
from tiergen.runtime.agent_linux.records import read_records, setup_logging

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="the Linux agent forks")


def test_run_starts_services_forks_behaviours_and_writes_records(tmp_path: Path) -> None:
    p = replace(
        program(duration=1.5, idle=0.05, active=0.02),
        services=("http.serve",),
        impls={"http.get": {"http.fake": 1.0}, "http.serve": {"http.fakesrv": 1.0}},
    )
    service = FakeService()
    out = tmp_path / "out"
    out.mkdir()
    log = setup_logging(out)

    def primitive(impl_id: str) -> PrimitiveImpl:
        return FakeImpl()

    def services(impl_id: str) -> ServiceImpl:
        assert impl_id == "http.fakesrv"
        return service

    status = run(
        p, out, primitive=primitive, service=services, attribution=FakeAttribution(), log=log
    )
    for handler in list(log.handlers):
        log.removeHandler(handler)
        handler.close()
    assert status == 0
    assert service.started == [out / "http.fakesrv"]
    assert (out / "http.fakesrv").is_dir()
    assert service.stopped == 1
    assert service.checks >= 2
    records = read_records(out / "invocations.jsonl")
    assert len(records) > 3
    assert [r.key.invocation for r in records[:2]] == ["lab/ws[0]/browse#1", "lab/ws[0]/browse#2"]
    assert all(r.outcome == "succeeded" for r in records)
    assert all(r.clock.monotonic <= r.end - r.start + r.clock.monotonic for r in records)
    text = (out / "agent.log").read_text()
    assert "http.fakesrv serves http/80" in text
    assert "behaviour 'browse' runs as" in text
    assert "done, 0 failure(s)" in text
    logging.getLogger("tiergen.agent").handlers.clear()


def test_a_service_without_a_runtime_is_logged_and_the_host_stays_up(tmp_path: Path) -> None:
    p = replace(
        program(duration=0.5, idle=0.05, active=0.02),
        services=("smb.serve",),
        impls={"http.get": {"http.fake": 1.0}, "smb.serve": {"smb.none": 1.0}},
    )
    out = tmp_path / "out"
    out.mkdir()
    log = setup_logging(out)

    def no_service(impl_id: str) -> ServiceImpl:
        raise LookupError(f"no runtime is registered for implementation {impl_id!r}")

    status = run(
        p,
        out,
        primitive=lambda _: FakeImpl(),
        service=no_service,
        attribution=FakeAttribution(),
        log=log,
    )
    for handler in list(log.handlers):
        log.removeHandler(handler)
        handler.close()
    assert status == 1
    text = (out / "agent.log").read_text()
    assert "smb.none for smb.serve cannot start; the host stays up without it" in text
    assert "behaviour 'browse' runs as" in text
    assert read_records(out / "invocations.jsonl")
    logging.getLogger("tiergen.agent").handlers.clear()
