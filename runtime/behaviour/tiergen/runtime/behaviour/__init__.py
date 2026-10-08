"""The behaviour loop, shared by every agent and by the simulator.

A behaviour is a semi-Markov process over states whose actions become invocations. The
loop runs one against whatever it is handed: a clock, the implementations, an attribution
context and a record sink. The Linux agent hands it the wall clock, the installed runtimes
and a cgroup per invocation; the simulator hands it a clock that jumps and an
implementation that records. Nothing here belongs to a platform.
"""

from tiergen.runtime.behaviour.loop import (
    Attribution,
    BehaviourLoop,
    Clock,
    InvocationContext,
    stream_id,
)
from tiergen.runtime.behaviour.sampling import advance, dwell, multiplier

__all__ = [
    "Attribution",
    "BehaviourLoop",
    "Clock",
    "InvocationContext",
    "advance",
    "dwell",
    "multiplier",
    "stream_id",
]
