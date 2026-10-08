"""What ``assemble`` writes: labels keyed by a sensor's own connection ids, and flags for
what the join could not explain. Both are data, so ``evaluate`` and anything after it read
a dataset with core alone.

A label is an invocation record confirmed by attribution and attached to one sensor's
connection: the record's key and outcome, the signature the state ran (from the IR, by
behaviour and state, so the record itself carries only what the agent observed), and the
attribution that confirmed it. A flag is one of the design's two (section 4.11): ``failed``,
an invocation with no observed traffic, and ``unattributed``, a sensor connection with no
invocation. Its reason says where the chain from invocation to kernel to sensor broke.
"""

from dataclasses import dataclass
from typing import Literal

from tiergen.core.events import FiveTuple, SensorFlowId
from tiergen.core.records import AttributionKey, LabelKey, Outcome

FlagKind = Literal["failed", "unattributed"]
FlagReason = Literal["no_attribution", "no_invocation", "no_connection"]
"""``no_attribution``: the kernel saw nothing (of the connection, or of the invocation).
``no_invocation``: the kernel saw the connection from a host of the run, but outside every
invocation; a service's own traffic. ``no_connection``: the kernel saw the invocation's
connections, and no sensor over any capture point reported one of them."""


@dataclass(frozen=True, slots=True)
class Label:
    """One sensor connection and the invocation that made it. ``observed`` is when the
    kernel saw the connection begin, seconds since the epoch on the capture host's clock;
    ``principal`` is the execution context it was seen from, equal to the record's."""

    flow: SensorFlowId
    key: LabelKey
    signature: str
    outcome: Outcome
    principal: AttributionKey
    observed: float


@dataclass(frozen=True, slots=True)
class Flag:
    """What the join could not explain, and where it stood when it gave up.

    An ``unattributed`` flag names the sensor connection (``flow``, ``five_tuple``) and
    ``at`` is its start. A ``failed`` flag names the invocation and ``at`` is its start.
    """

    kind: FlagKind
    reason: FlagReason
    at: float
    flow: SensorFlowId | None = None
    five_tuple: FiveTuple | None = None
    invocation: str | None = None
