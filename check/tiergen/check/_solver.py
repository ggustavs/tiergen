# pyright: basic
"""The only module that touches z3, whose Python API is not fully typed."""

from collections.abc import Mapping, Sequence

import z3


def unsatisfiable(counts: Mapping[str, int], needs: Sequence[tuple[str, str]]) -> list[int]:
    """Indices of the requirements that cannot hold under ``counts``.

    ``needs[i] = (source, target)`` requires at least one ``target`` instance whenever
    there is a ``source`` instance. Each requirement is tried on its own against the fixed
    counts, so every violation is found, not just a minimal core.
    """
    n = {kind: z3.Int(kind) for kind in counts}
    solver = z3.Solver()
    for kind, count in counts.items():
        solver.add(n[kind] == count)
    failed: list[int] = []
    for i, (source, target) in enumerate(needs):
        solver.push()
        solver.add(z3.Implies(n[source] > 0, n[target] >= 1))
        if solver.check() != z3.sat:
            failed.append(i)
        solver.pop()
    return failed
