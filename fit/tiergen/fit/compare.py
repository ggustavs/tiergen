"""What a process looks like to a sensor: its projection onto the acting states.

A silent state is invisible, so a chain with one is seen as the chain over the acting
states that the visits in between induce: ``P_obs = P_AA + P_AI (I - P_II)^-1 P_IA``, the
initial distribution likewise, and a state's observed dwell is its own dwell plus the
silent dwells until the next action, which is what a fit of the observable chain
estimates. The recovery tests compare a fit to this, not to the raw matrix.
"""

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from tiergen.core.ir import Action
from tiergen.stats.streams import Floats


@dataclass(frozen=True, slots=True)
class Projection:
    states: tuple[str, ...]
    initial: tuple[float, ...]
    transitions: tuple[tuple[float, ...], ...]
    silent_mean: tuple[float, ...]
    """Expected silent dwell that follows each acting state before the next action, in
    operational seconds, for the exponential-dwell case where it has a closed form:
    ``P_AI (I - P_II)^-1 m_I`` with ``m_I`` the silent means."""


def projection(
    states: Sequence[str],
    initial: Sequence[float],
    transitions: Sequence[Sequence[float]],
    action_map: dict[str, Action | None],
    silent_means: Sequence[float] | None = None,
) -> Projection:
    acting = [i for i, s in enumerate(states) if action_map.get(s) is not None]
    silent = [i for i, s in enumerate(states) if action_map.get(s) is None]
    P = np.asarray(transitions, dtype=np.float64)
    pi = np.asarray(initial, dtype=np.float64)
    if silent:
        inv: Floats = np.linalg.inv(np.eye(len(silent)) - P[np.ix_(silent, silent)])
        through: Floats = inv @ P[np.ix_(silent, acting)]
        p_obs: Floats = P[np.ix_(acting, acting)] + P[np.ix_(acting, silent)] @ through
        pi_obs: Floats = pi[acting] + pi[silent] @ through
        means = (
            P[np.ix_(acting, silent)] @ inv @ np.asarray(silent_means, dtype=np.float64)[silent]
            if silent_means is not None
            else np.zeros(len(acting))
        )
    else:
        p_obs, pi_obs, means = P, pi, np.zeros(len(acting))
    return Projection(
        tuple(states[i] for i in acting),
        tuple(float(v) for v in pi_obs),
        tuple(tuple(float(v) for v in row) for row in p_obs),
        tuple(float(v) for v in means),
    )
