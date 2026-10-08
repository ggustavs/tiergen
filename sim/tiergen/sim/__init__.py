"""A scenario simulated: the denotation of section 9, sampled.

The same behaviour loop the agents run, under a clock that jumps and an implementation
that records instead of acting, gives every invocation of every instance in seconds; the
signatures' traffic shapes turn those into the ``ConnEvent``s and ``AppEvent``s a sensor
on the wire would report. Exact with respect to the model, with no runtime in the way,
which is what the fit's recovery tests and the calibration of the statistical tests need,
and what ``predict`` summarises.
"""

from tiergen.sim.simulate import (
    SENSOR,
    Simulated,
    programs_for,
    simulate,
    simulate_programs,
    write,
)

__all__ = ["SENSOR", "Simulated", "programs_for", "simulate", "simulate_programs", "write"]
