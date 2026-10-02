"""The runtime interface of a primitive implementation."""

from collections.abc import Mapping
from random import Random
from typing import Protocol

from tiergen.core.codec import JsonValue
from tiergen.core.records import LabelKey, Outcome, Peer


class Context(Protocol):
    """What an invocation is given by the agent that runs it."""

    @property
    def label(self) -> LabelKey:
        """The label this invocation will carry. No primitive runs without one."""
        ...

    @property
    def invocation(self) -> str:
        """The invocation id, ``label.invocation``, for anything the implementation names."""
        ...

    @property
    def targets(self) -> tuple[Peer, ...]:
        """The peers this invocation is aimed at: one for ``select="one"``, every peer of the
        tie for ``select="all"``. The same instances as ``label.targets``, with addresses."""
        ...

    @property
    def ties(self) -> Mapping[str, tuple[Peer, ...]]:
        """Each tie of the actor's kind, resolved to the peers it reaches: address and the
        endpoints served there, so the port is known as well as the host."""
        ...

    @property
    def variant(self) -> str | None:
        """The implementation variant selected for this instance."""
        ...

    @property
    def rng(self) -> Random:
        """Seeded per instance from the scenario seed. The only source of randomness."""
        ...


class PrimitiveImpl(Protocol):
    """Runs the signatures a package provides, on the client actor's host.

    The agent calls ``run`` inside the invocation's cgroup (Linux) or job object (Windows),
    which is what lets attribution tie the traffic to ``ctx.label``.
    """

    def run(self, ctx: Context, signature: str, **params: JsonValue) -> Outcome:
        """Run ``signature`` once. A tool failure is an outcome, not an exception."""
        ...
