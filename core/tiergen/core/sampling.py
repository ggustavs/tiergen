"""Seeds and sampling: the one rule that makes a run a function of the IR and the seed.

Every random choice in a run is drawn from a stream named by the instance that draws it and
what it draws for, derived from the scenario seed by hashing. Streams are independent, so
an implementation that draws one extra sample does not shift every later dwell time, and
agents can start in any order. Weighted choices are sampled over their keys in sorted
order, so two equal dictionaries with different insertion order pick the same thing.
"""

import hashlib
from collections.abc import Mapping
from random import Random
from typing import Literal

Stream = Literal["behaviour", "selection", "impl"]
"""``behaviour``: the state and dwell draws of the behaviour loop. ``selection``: which
implementation and variant an instance uses per signature, and which targets an action hits.
``impl``: handed to the implementation as ``ctx.rng``."""


def instance_seed(seed: int, instance: str, stream: Stream) -> int:
    """A 64-bit seed for one stream of one instance, derived from the scenario seed."""
    digest = hashlib.blake2b(f"{seed}|{instance}|{stream}".encode(), digest_size=8).digest()
    return int.from_bytes(digest, "big")


def rng(seed: int, instance: str, stream: Stream) -> Random:
    return Random(instance_seed(seed, instance, stream))


def weighted(random: Random, weights: Mapping[str, float]) -> str:
    """One key, with probability proportional to its weight, over the keys in sorted order."""
    keys = sorted(weights)
    if not keys:
        raise ValueError("nothing to choose from")
    return random.choices(keys, weights=[weights[k] for k in keys], k=1)[0]
