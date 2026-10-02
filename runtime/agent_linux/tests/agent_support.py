"""Fakes for the loop: a clock that jumps, an implementation that records, an attribution
that keys by invocation, and a two-state program like linux_slice's workstation."""

import contextlib
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path
from random import Random

from tiergen.core.codec import JsonValue
from tiergen.core.ir import Choice, Distribution, Endpoint, ScheduleEvent, Select
from tiergen.core.program import Program, ResolvedAction, ResolvedBehaviour
from tiergen.core.records import AttributionKey, ClockStamp, Outcome, Peer
from tiergen.impls._base import Context, ServiceContext

START = "2026-10-05T08:00:00+02:00"  # a Monday
EPOCH = 1_000_000_000.0


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        assert seconds >= 0
        self.t += seconds

    def stamp(self) -> ClockStamp:
        return ClockStamp(EPOCH + self.t, self.t, 0.0)


@dataclass(frozen=True, slots=True)
class Call:
    invocation: str
    signature: str
    params: dict[str, JsonValue]
    targets: tuple[str, ...]
    variant: str | None


@dataclass
class FakeImpl:
    """Records each call. ``draws`` samples from ``ctx.rng`` per call; ``raises`` after
    ``raise_after`` calls, once."""

    draws: int = 0
    raise_at: int | None = None
    calls: list[Call] = field(default_factory=list[Call])

    def run(self, ctx: Context, signature: str, **params: JsonValue) -> Outcome:
        self.calls.append(
            Call(
                ctx.invocation,
                signature,
                params,
                tuple(p.instance for p in ctx.targets),
                ctx.variant,
            )
        )
        for _ in range(self.draws):
            ctx.rng.random()
        if self.raise_at is not None and len(self.calls) == self.raise_at:
            raise RuntimeError("the tool blew up")
        return "succeeded"


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


class FakeAttribution:
    @contextlib.contextmanager
    def enter(self, invocation: str) -> Generator[AttributionKey]:
        yield AttributionKey("linux", f"fake:{invocation}")


def program(
    *,
    seed: int = 1,
    duration: float = 600.0,
    schedule: tuple[ScheduleEvent, ...] | None = None,
    rate: tuple[float, ...] | None = None,
    select: Select | None = "one",
    peers: int = 2,
    idle: float = 20.0,
    active: float = 2.0,
    impls: dict[str, float] | None = None,
) -> Program:
    browse = ResolvedBehaviour(
        "browse",
        ("idle", "web_get"),
        (1.0, 0.0),
        ((0.0, 1.0), (0.7, 0.3)),
        (Distribution("exponential", (idle,)), Distribution("exponential", (active,))),
        rate,
        {
            "idle": None,
            "web_get": ResolvedAction(
                "http.get", "web", {"path": Choice(("/", "/news"), (0.8, 0.2))}, select
            ),
        },
    )
    web = tuple(
        Peer(f"lab/web[{i}]", f"10.0.0.{80 + i}", (Endpoint("http", 80, "tcp"),))
        for i in range(peers)
    )
    return Program(
        scenario="s",
        instance="lab/ws[0]",
        group="lab",
        kind="ws",
        platform="linux",
        hostname="lab-ws-0",
        seed=seed,
        start=START,
        duration_s=duration,
        behaviours=(browse,),
        impls={"http.get": impls or {"http.fake": 1.0}},
        services=(),
        peers={"web": web},
        routes=(),
        schedule=schedule
        if schedule is not None
        else (ScheduleEvent(0.0, "lab/ws", "start", "browse"),),
        forwards=False,
        credentials=None,
    )


def seeded(seed: int) -> Random:
    return Random(seed)
