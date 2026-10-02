"""The nmap runtime against this host; skipped without the binary."""

import os
import shutil
import socket
from collections.abc import Iterator
from dataclasses import dataclass
from random import Random

import pytest

from tiergen.core.ir import Endpoint
from tiergen.core.records import LabelKey, Peer
from tiergen.impls.nmap.runtime import NmapRuntime, command

pytestmark = pytest.mark.skipif(shutil.which("nmap") is None, reason="nmap is not installed")


@dataclass(frozen=True, slots=True)
class Ctx:
    label: LabelKey
    invocation: str
    targets: tuple[Peer, ...]
    ties: dict[str, tuple[Peer, ...]]
    variant: str | None
    rng: Random


def ctx(*targets: Peer) -> Ctx:
    label = LabelKey(
        "s",
        "lab/atk[0]",
        "recon",
        "syn_scan",
        "lab/atk[0]/recon#1",
        "scan.nmap",
        None,
        tuple(t.instance for t in targets),
    )
    return Ctx(label, label.invocation, targets, {"targets": targets}, None, Random(1))


@pytest.fixture
def listener() -> Iterator[Peer]:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen()
        yield Peer("lab/web[0]", "127.0.0.1", (Endpoint("http", s.getsockname()[1], "tcp"),))


def test_the_command_is_nmaps_own_without_name_resolution() -> None:
    assert command("scan.tcp_syn", "1-1024", ("10.0.0.1", "10.0.0.2")) == [
        "nmap",
        "-sS",
        "-n",
        "-p",
        "1-1024",
        "--host-timeout",
        "300s",
        "10.0.0.1",
        "10.0.0.2",
    ]


def test_a_connect_scan_succeeds_and_a_raw_scan_without_privilege_fails(listener: Peer) -> None:
    runtime = NmapRuntime()
    port = listener.served[0].port
    assert runtime.run(ctx(listener), "scan.tcp_connect", ports=str(port)) == "succeeded"
    assert runtime.run(ctx(), "scan.tcp_connect", ports=str(port)) == "failed"
    assert runtime.run(ctx(listener), "scan.ping", ports=str(port)) == "failed"
    if os.geteuid() != 0:
        assert runtime.run(ctx(listener), "scan.tcp_syn", ports=str(port)) == "failed"
