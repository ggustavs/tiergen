"""What the agent gives an implementation, and what it writes down afterwards.

The runtime's identity chain, as data: a ``LabelKey`` is handed to a primitive before it
runs and is everything a label is except the outcome; an ``InvocationRecord`` is what the
agent logs when it has run, and is what attribution joins to by principal and interval and
what ``assemble`` turns into confirmed labels keyed by the sensor's connection ids.
"""

from dataclasses import dataclass
from typing import Literal

from tiergen.core.ir import Endpoint, Platform

Outcome = Literal["succeeded", "failed"]


def invocation_id(instance: str, behaviour: str, n: int) -> str:
    """``lab/workstation[0]/browse#17``: the ``n``th invocation of a behaviour on an instance.

    With the per-instance seed streams of ``tiergen.core.sampling`` this makes labels a
    function of the IR and the seed, whatever order the agents start in.
    """
    return f"{instance}/{behaviour}#{n}"


@dataclass(frozen=True, slots=True)
class Peer:
    """One instance a tie reaches: its address on the segment the source shares with it or
    routes to, and what it serves there, so a primitive knows the port as well as the host."""

    instance: str
    address: str
    served: tuple[Endpoint, ...]


@dataclass(frozen=True, slots=True)
class LabelKey:
    """A label before its outcome exists: what an invocation is about to do, and as whom.

    ``targets`` are the instance ids the action was aimed at, one for ``single`` and
    ``optional`` ties and for ``select="one"``, several for ``select="all"``.
    """

    scenario: str
    instance: str
    behaviour: str
    action: str
    invocation: str
    impl: str
    variant: str | None
    targets: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AttributionKey:
    """What the kernel-level observer on a platform sees an invocation as.

    Linux: the invocation's cgroup, by path. Windows: the job object, by its root process
    id. The platform tag keeps the two from being compared.
    """

    platform: Platform
    principal: str


@dataclass(frozen=True, slots=True)
class ClockStamp:
    """When, on the host that ran it: wall clock, monotonic clock, and the host's measured
    offset from the capture host's clock, all in seconds, so the join can place the interval
    on the pcap's timeline."""

    wall: float
    monotonic: float
    offset: float


@dataclass(frozen=True, slots=True)
class InvocationRecord:
    """What the agent logs once a primitive has run.

    ``outcome`` is what the tool reported: traffic from a failed exploit is real traffic
    and keeps its label, with ``outcome`` "failed". ``start`` and ``end`` are on the host's
    wall clock; ``clock`` carries what is needed to move them onto the capture host's.
    """

    key: LabelKey
    principal: AttributionKey
    start: float
    end: float
    outcome: Outcome
    clock: ClockStamp
