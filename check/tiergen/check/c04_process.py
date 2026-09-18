"""Check 4: each semi-Markov process is well formed.

Initial distribution and transition rows are stochastic, every state is reachable, there
is one dwell distribution per state, and a rate curve has 24 or 168 entries.
"""

import math
from collections.abc import Iterator, Sequence

from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic, error

ID = "C04"
TOLERANCE = 1e-9


def _stochastic(row: Sequence[float]) -> str | None:
    if any(p < 0 for p in row):
        return "has a negative entry"
    total = math.fsum(row)
    if abs(total - 1.0) > TOLERANCE:
        return f"sums to {total:g}, not 1"
    return None


def check(ctx: Context) -> Iterator[Diagnostic]:
    for k, kind in enumerate(ctx.scenario.kinds):
        for b, behaviour in enumerate(kind.behaviours):
            p = behaviour.process
            path = f"kinds[{k}].behaviours[{b}].process"
            states = ctx.states(p)
            if states is None:
                continue
            n = len(states)
            if n == 0:
                yield error(ID, f"{path}.states", "a process needs at least one state")
                continue

            initial = ctx.initial(p)
            if initial is not None:
                if len(initial) != n:
                    yield error(ID, f"{path}.initial", f"has {len(initial)} entries for {n} states")
                    initial = None
                elif problem := _stochastic(initial):
                    yield error(ID, f"{path}.initial", problem)
                    initial = None

            matrix = ctx.transitions(p)
            if matrix is not None:
                if len(matrix) != n or any(len(row) != n for row in matrix):
                    yield error(ID, f"{path}.transitions", f"is not {n} by {n}")
                    matrix = None
                else:
                    problems = [(i, _stochastic(row)) for i, row in enumerate(matrix)]
                    for i, problem in problems:
                        if problem:
                            yield error(
                                ID, f"{path}.transitions[{i}]", f"row for {states[i]!r} {problem}"
                            )
                    if any(problem for _, problem in problems):
                        matrix = None  # reachability over a broken matrix says nothing

            if initial is not None and matrix is not None:
                seen = {i for i, prob in enumerate(initial) if prob > 0}
                frontier = list(seen)
                while frontier:
                    i = frontier.pop()
                    for j, prob in enumerate(matrix[i]):
                        if prob > 0 and j not in seen:
                            seen.add(j)
                            frontier.append(j)
                for i in sorted(set(range(n)) - seen):
                    yield error(ID, f"{path}.states[{i}]", f"state {states[i]!r} is unreachable")

            dwell = ctx.dwell(p)
            if dwell is not None and len(dwell) != n:
                yield error(ID, f"{path}.dwell", f"has {len(dwell)} distributions for {n} states")

            rate = ctx.rate(p)
            if rate is not None and len(rate) not in (24, 168):
                yield error(
                    ID, f"{path}.rate", f"has {len(rate)} entries; a rate curve has 24 or 168"
                )
