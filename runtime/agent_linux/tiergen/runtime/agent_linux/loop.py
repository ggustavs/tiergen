"""One behaviour's loop: states, holding times, actions, and the invocations they become.

Everything that varies is handed in (the clock, the implementations, the attribution and
the record sink), so the loop runs unchanged under a fake clock in the tests and in a forked
process on a host. Its draws come from three streams named by the behaviour's id,
``instance/behaviour``, so one behaviour's draws never shift another's, and an
implementation drawing from ``ctx.rng`` never shifts a holding time.

A state's action runs on entry; the holding time is drawn after the action returns and is
held in operational time, which the rate curve turns into wall time. The schedule's events
for this behaviour (``start``, ``stop``) and for its instance (``set_rate``) are applied as
their time comes, a ``stop`` abandoning the state and the next ``start`` drawing afresh.
"""

import logging
import traceback
from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import datetime
from random import Random
from typing import Protocol

from tiergen.core.ir import Choice, ParamScalar, ScheduleEvent
from tiergen.core.program import Program, ResolvedAction, ResolvedBehaviour
from tiergen.core.records import (
    AttributionKey,
    ClockStamp,
    InvocationRecord,
    LabelKey,
    Outcome,
    Peer,
    invocation_id,
)
from tiergen.core.sampling import rng, weighted
from tiergen.impls._base import ImplRef, PrimitiveImpl
from tiergen.runtime.agent_linux.sampling import advance, dwell


class Clock(Protocol):
    """Scenario time and wall time, as the loop sees them."""

    def now(self) -> float:
        """Seconds since the agent's t=0, monotonic."""
        ...

    def sleep(self, seconds: float) -> None: ...

    def stamp(self) -> ClockStamp:
        """Wall clock, monotonic clock and the measured offset, now."""
        ...


class Attribution(Protocol):
    """How the kernel will see an invocation: a context the loop runs it in."""

    def enter(self, invocation: str) -> AbstractContextManager[AttributionKey]: ...


@dataclass(frozen=True, slots=True)
class InvocationContext:
    """The ``Context`` an implementation is handed, as data."""

    label: LabelKey
    invocation: str
    targets: tuple[Peer, ...]
    ties: Mapping[str, tuple[Peer, ...]]
    variant: str | None
    rng: Random


def stream_id(instance: str, behaviour: str) -> str:
    """What names a behaviour's streams: the prefix of its invocation ids."""
    return f"{instance}/{behaviour}"


def _draw(random: Random, weights: tuple[float, ...]) -> int:
    return random.choices(range(len(weights)), weights=weights, k=1)[0]


class BehaviourLoop:
    def __init__(
        self,
        program: Program,
        behaviour: ResolvedBehaviour,
        *,
        clock: Clock,
        primitive: Callable[[str], PrimitiveImpl],
        attribution: Attribution,
        sink: Callable[[InvocationRecord], None],
        log: logging.Logger | None = None,
    ) -> None:
        self.program = program
        self.behaviour = behaviour
        self.clock = clock
        self.primitive = primitive
        self.attribution = attribution
        self.sink = sink
        self.log = log or logging.getLogger(__name__)
        key = stream_id(program.instance, behaviour.name)
        self.behaviour_rng = rng(program.seed, key, "behaviour")
        self.selection_rng = rng(program.seed, key, "selection")
        self.impl_rng = rng(program.seed, key, "impl")
        self.start_local = datetime.fromisoformat(program.start)
        self.events: list[ScheduleEvent] = sorted(
            (
                e
                for e in program.schedule
                if e.op == "set_rate" or (e.op in ("start", "stop") and e.arg == behaviour.name)
            ),
            key=lambda e: e.at_s,
        )
        self.n = 0
        self._loaded: dict[str, PrimitiveImpl] = {}

    def run(self) -> None:
        """Run until the program's duration has passed on the clock."""
        b = self.behaviour
        duration = self.program.duration_s
        pending = list(self.events)
        factor = 1.0
        active = False
        state: int | None = None
        left = 0.0  # operational seconds still to hold in the state
        while True:
            now = self.clock.now()
            while pending and pending[0].at_s <= now:
                event = pending.pop(0)
                if event.op == "start":
                    if not active:
                        active, state = True, None
                elif event.op == "stop":
                    active, state = False, None
                elif event.op == "set_rate":
                    assert not isinstance(event.arg, str | None)  # load_program held this
                    factor = float(event.arg)
                else:
                    self.log.warning(
                        "run_sequence at %g s: not implemented by this agent", event.at_s
                    )
            if now >= duration:
                return
            horizon = min(duration, pending[0].at_s) if pending else duration
            if not active:
                self.clock.sleep(horizon - now)
                continue
            if state is None:
                state = _draw(self.behaviour_rng, b.initial)
                left = self._enter(state)
                continue
            wall, done = advance(left, now, horizon - now, self.start_local, b.rate, factor)
            self.clock.sleep(wall)
            left -= done
            if left <= 0:
                state = _draw(self.behaviour_rng, b.transitions[state])
                left = self._enter(state)

    def _enter(self, state: int) -> float:
        """Run the state's action, if any, and draw the holding time that follows it."""
        name = self.behaviour.states[state]
        action = self.behaviour.action_map.get(name)
        if action is not None:
            self._invoke(name, action)
        return dwell(self.behaviour_rng, self.behaviour.dwell[state])

    def _param(self, value: ParamScalar | Choice) -> ParamScalar:
        if isinstance(value, Choice):
            return value.options[_draw(self.selection_rng, value.weights)]
        return value

    def _invoke(self, name: str, action: ResolvedAction) -> None:
        program = self.program
        peers = program.peers.get(action.tie, ())
        if action.select == "one":
            targets = (peers[self.selection_rng.randrange(len(peers))],) if peers else ()
        else:
            targets = peers
        if not targets:
            self.log.info("%s: no peer on tie %r; nothing to run", name, action.tie)
            return
        self.n += 1
        invocation = invocation_id(program.instance, self.behaviour.name, self.n)
        ref = ImplRef.parse(weighted(self.selection_rng, program.impls[action.signature]))
        params = {k: self._param(v) for k, v in action.params.items()}
        label = LabelKey(
            program.scenario,
            program.instance,
            self.behaviour.name,
            name,
            invocation,
            ref.impl,
            ref.variant,
            tuple(p.instance for p in targets),
        )
        ctx = InvocationContext(
            label, invocation, targets, program.peers, ref.variant, self.impl_rng
        )
        with self.attribution.enter(invocation) as principal:
            begin = self.clock.stamp()
            outcome: Outcome = "failed"
            try:
                impl = self._loaded.get(ref.impl) or self._loaded.setdefault(
                    ref.impl, self.primitive(ref.impl)
                )
                outcome = impl.run(ctx, action.signature, **params)
            except Exception:
                self.log.error("%s raised:\n%s", invocation, traceback.format_exc().rstrip())
            end = self.clock.stamp()
        self.sink(InvocationRecord(label, principal, begin.wall, end.wall, outcome, begin))
