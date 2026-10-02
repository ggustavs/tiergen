"""Reading a program: the one file an agent is given, held once before anything runs.

A program is data written by ``tiergen build`` with every resource inlined. What the checks
could not hold, because they never see what a dwell parameter means, is held here, so a
family the agent does not know or a parameter it cannot draw from is an error at load, not
at run time.
"""

import json
from pathlib import Path

from tiergen.core.codec import from_json
from tiergen.core.ir import Distribution
from tiergen.core.program import Program

FAMILIES = ("exponential", "lognormal", "weibull", "empirical")
"""``exponential``: (mean,). ``lognormal``: (mu, sigma) of the log. ``weibull``: (shape, scale).
``empirical``: the samples, drawn uniformly. All in seconds of operational time."""


class ProgramError(ValueError):
    """The program cannot be run as written; the message says which part and why."""


def load_program(path: Path) -> Program:
    try:
        program = from_json(Program, json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError) as err:  # CodecError and JSONDecodeError are ValueErrors
        raise ProgramError(f"{path}: {err}") from err
    validate(program)
    return program


def _dwell_problem(d: Distribution) -> str | None:
    params = d.params
    if isinstance(params, str):
        return f"parameters are the unresolved resource {params!r}"
    if d.family == "exponential":
        if len(params) != 1 or params[0] <= 0:
            return "exponential takes one positive mean"
    elif d.family == "lognormal":
        if len(params) != 2 or params[1] < 0:
            return "lognormal takes mu and a non-negative sigma"
    elif d.family == "weibull":
        if len(params) != 2 or params[0] <= 0 or params[1] <= 0:
            return "weibull takes a positive shape and a positive scale"
    elif d.family == "empirical":
        if not params or any(p < 0 for p in params):
            return "empirical takes one or more non-negative samples"
    else:
        return f"unknown family {d.family!r}; the agent knows {', '.join(FAMILIES)}"
    return None


def validate(program: Program) -> None:
    """Raise ``ProgramError`` for anything the loop would trip over."""
    for b in program.behaviours:
        where = f"behaviour {b.name!r}"
        if len(b.dwell) != len(b.states):
            raise ProgramError(
                f"{where}: {len(b.dwell)} dwell distributions for {len(b.states)} states"
            )
        for state, d in zip(b.states, b.dwell, strict=True):
            problem = _dwell_problem(d)
            if problem is not None:
                raise ProgramError(f"{where}, state {state!r}: {problem}")
        if b.rate is not None and len(b.rate) not in (24, 168):
            raise ProgramError(f"{where}: a rate curve has 24 or 168 entries, not {len(b.rate)}")
        for state, action in b.action_map.items():
            if state not in b.states:
                raise ProgramError(f"{where}: the action map names a state {state!r} it lacks")
            if action is not None and action.signature not in program.impls:
                raise ProgramError(
                    f"{where}, state {state!r}: no implementation selected for {action.signature!r}"
                )
    names = {b.name for b in program.behaviours}
    for event in program.schedule:
        if event.op in ("start", "stop") and event.arg not in names:
            raise ProgramError(
                f"schedule: {event.op} {event.arg!r} names no behaviour of this instance"
            )
        if event.op == "set_rate" and (isinstance(event.arg, str | None) or event.arg < 0):
            raise ProgramError(
                f"schedule: set_rate at {event.at_s:g} s has no non-negative multiplier"
            )
    for signature in program.services:
        if signature not in program.impls:
            raise ProgramError(f"services: no implementation selected for {signature!r}")
