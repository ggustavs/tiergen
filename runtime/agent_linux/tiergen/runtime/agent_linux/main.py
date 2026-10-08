"""``tiergen-agent <program.json>``: the process a Linux host runs for the whole scenario.

It loads the program, chooses how invocations are keyed, starts the services the instance
binds and waits for them to answer, holds at the gate if it was given one (``--go PATH``:
the scheduler creates the path once attribution and capture are in place, so every host's
scenario time starts at once), then forks one process per behaviour and waits for the
duration. Scenario time starts once the services are up and the gate is open. Services write under
``out/<impl id>``; the behaviours write ``out/invocations.jsonl``; everything logs to
``out/agent.log``.
"""

import argparse
import logging
import os
import signal
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from random import Random

from tiergen.core.ir import Endpoint
from tiergen.core.program import Program
from tiergen.core.records import ClockStamp
from tiergen.core.sampling import rng, weighted
from tiergen.impls._base import ImplRef, PrimitiveImpl, ServiceImpl, load_runtime
from tiergen.runtime.agent_linux.cgroups import choose
from tiergen.runtime.agent_linux.loop import Attribution, BehaviourLoop, Clock
from tiergen.runtime.agent_linux.program import ProgramError, load_program
from tiergen.runtime.agent_linux.records import Recorder, setup_logging

DEFAULT_OUT = Path("/tiergen/out")
HEALTH_TIMEOUT = 30.0


class MonotonicClock:
    """Scenario time from the agent's start; the clock offset is 0 until the scheduler
    (task 9) measures it against the capture host."""

    def __init__(self) -> None:
        self._t0 = time.monotonic()

    def now(self) -> float:
        return time.monotonic() - self._t0

    def sleep(self, seconds: float) -> None:
        if seconds > 0:
            time.sleep(seconds)

    def stamp(self) -> ClockStamp:
        return ClockStamp(time.time(), time.monotonic(), 0.0)


@dataclass(frozen=True, slots=True)
class ServiceContext:
    instance: str
    served: tuple[Endpoint, ...]
    out: Path
    rng: Random


def load_primitive(impl_id: str) -> PrimitiveImpl:
    runtime = load_runtime(impl_id)
    if not isinstance(runtime, PrimitiveImpl):
        raise TypeError(f"the runtime of {impl_id!r} is not a PrimitiveImpl")
    return runtime


def load_service(impl_id: str) -> ServiceImpl:
    runtime = load_runtime(impl_id)
    if not isinstance(runtime, ServiceImpl):
        raise TypeError(f"the runtime of {impl_id!r} is not a ServiceImpl")
    return runtime


def start_services(
    program: Program, out: Path, service: Callable[[str], ServiceImpl], log: logging.Logger
) -> tuple[list[tuple[ServiceImpl, ServiceContext]], int]:
    """Start one service per server signature and wait until each answers its healthcheck.

    A service that cannot be loaded, started or reached is logged and counted, not fatal:
    the host stays up with its addresses and routes, and the scheduler reads the log.
    """
    selection = rng(program.seed, program.instance, "selection")
    started: list[tuple[ServiceImpl, ServiceContext]] = []
    failed = 0
    for signature in program.services:
        ref = ImplRef.parse(weighted(selection, program.impls[signature]))
        try:
            impl = service(ref.impl)
            ctx = ServiceContext(
                program.instance,
                impl.served(),
                out / ref.impl,
                rng(program.seed, f"{program.instance}/{signature}", "impl"),
            )
            ctx.out.mkdir(parents=True, exist_ok=True)
            impl.start(ctx)
            started.append((impl, ctx))
            deadline = time.monotonic() + HEALTH_TIMEOUT
            while not impl.healthcheck(ctx):
                if time.monotonic() > deadline:
                    raise RuntimeError(f"did not answer within {HEALTH_TIMEOUT:g} s")
                time.sleep(0.2)
        except Exception:
            failed += 1
            log.exception(
                "%s for %s cannot start; the host stays up without it", ref.impl, signature
            )
            continue
        log.info("%s serves %s", ref.impl, ", ".join(f"{e.protocol}/{e.port}" for e in ctx.served))
    return started, failed


def run(
    program: Program,
    out: Path,
    *,
    primitive: Callable[[str], PrimitiveImpl],
    service: Callable[[str], ServiceImpl],
    attribution: Attribution,
    log: logging.Logger,
    clock: Clock | None = None,
    go: Path | None = None,
) -> int:
    """Services, the gate if any, then one process per behaviour, until the duration or
    SIGTERM."""
    services, failed = start_services(program, out, service, log)
    recorder = Recorder(out)
    children: list[int] = []
    stopped = False

    def terminate(signum: int, frame: object) -> None:
        nonlocal stopped
        stopped = True
        for pid in children:
            os.kill(pid, signal.SIGTERM)

    signal.signal(signal.SIGTERM, terminate)
    try:
        if go is not None:
            log.info("services up; holding at %s", go)
            while not stopped and not go.exists():
                time.sleep(0.2)
            log.info("released")
        clock = clock or MonotonicClock()
        for behaviour in program.behaviours:
            if stopped:
                break
            pid = os.fork()
            if pid == 0:
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                status = 1
                try:
                    BehaviourLoop(
                        program,
                        behaviour,
                        clock=clock,
                        primitive=primitive,
                        attribution=attribution,
                        sink=recorder.write,
                        log=log,
                    ).run()
                    status = 0
                except BaseException:
                    log.exception("behaviour %r stopped", behaviour.name)
                finally:
                    os._exit(status)
            children.append(pid)
            log.info("behaviour %r runs as %d", behaviour.name, pid)
        if children:
            for pid in children:
                _, status = os.waitpid(pid, 0)
                failed += os.waitstatus_to_exitcode(status) not in (0, -signal.SIGTERM)
        else:
            while not stopped and clock.now() < program.duration_s:
                clock.sleep(min(1.0, program.duration_s - clock.now()))
    finally:
        for impl, ctx in reversed(services):
            impl.stop(ctx)
        recorder.close()
    log.info("done%s, %d failure(s)", " (terminated)" if stopped else "", failed)
    return 1 if failed else 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tiergen-agent", description="Run one instance's program on this host."
    )
    parser.add_argument("program", type=Path, help="program.<instance>.json from tiergen build")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="where to write records")
    parser.add_argument(
        "--go",
        type=Path,
        metavar="PATH",
        help="hold after the services are up until this path exists",
    )
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    log = setup_logging(args.out)
    try:
        program = load_program(args.program)
    except ProgramError as err:
        log.error("%s", err)
        return 2
    log.info(
        "%s on %s: %d behaviour(s), %d service(s), %g s",
        program.instance,
        program.hostname,
        len(program.behaviours),
        len(program.services),
        program.duration_s,
    )
    try:
        return run(
            program,
            args.out,
            primitive=load_primitive,
            service=load_service,
            attribution=choose(log),
            log=log,
            go=args.go,
        )
    except Exception:
        log.exception("agent failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
