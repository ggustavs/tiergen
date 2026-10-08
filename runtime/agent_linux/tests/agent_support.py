"""Fakes for the agent's tests: the loop's fakes, and a service that records."""

from dataclasses import dataclass, field
from pathlib import Path

from loop_support import EPOCH, START, Call, FakeAttribution, FakeClock, FakeImpl, program

from tiergen.core.ir import Endpoint
from tiergen.impls._base import ServiceContext

__all__ = [
    "EPOCH",
    "START",
    "Call",
    "FakeAttribution",
    "FakeClock",
    "FakeImpl",
    "FakeService",
    "program",
]


@dataclass
class FakeService:
    started: list[Path] = field(default_factory=list[Path])
    stopped: int = 0
    checks: int = 0

    def start(self, ctx: ServiceContext) -> None:
        self.started.append(ctx.out)

    def healthcheck(self, ctx: ServiceContext) -> bool:
        self.checks += 1
        return self.checks >= 2

    def stop(self, ctx: ServiceContext) -> None:
        self.stopped += 1

    def served(self) -> tuple[Endpoint, ...]:
        return (Endpoint("http", 80, "tcp"),)
