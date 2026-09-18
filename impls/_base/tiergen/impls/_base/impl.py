"""The runtime interface of a primitive implementation. Nothing in M0 implements it."""

from collections.abc import Mapping
from random import Random
from typing import Protocol

from tiergen.core.codec import JsonValue
from tiergen.core.labels import Label, Outcome


class Context(Protocol):
    """What an invocation is given by the agent that runs it."""

    @property
    def label(self) -> Label:
        """The label this invocation emits. No primitive runs without one."""
        ...

    @property
    def ties(self) -> Mapping[str, tuple[str, ...]]:
        """Each tie of the actor's kind, resolved to data-plane addresses."""
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
