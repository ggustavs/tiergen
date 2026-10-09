"""What ``tiergen fit`` does, for the part of section 11 M2 covers: from a run's sensor
events to each behaviour's observable chain, its dwell families and its rate curve, as
resources a scenario can reference, with a provenance and a report of what was unmapped.

The vocabulary comes from the scenario itself in M2: a connection is an action when its
responder is a peer of the action's tie on the signature's port and, where several actions
share a tie and a signature, when the request's path is one the action's parameters allow.
M4 derives the vocabulary from data. The chain is the observable one (design 4.7, 2026-10-09):
over the acting states, with the gap to the next action as a state's dwell; a silent state
is what the sensor cannot see, so none is fitted.
"""

from tiergen.fit.behaviour import Fitted, fit_behaviour
from tiergen.fit.compare import projection
from tiergen.fit.fit import FitError, Summary, fit_run
from tiergen.fit.ingest import Labelled, Unmapped, label
from tiergen.fit.vocabulary import Vocabulary, vocabulary

__all__ = [
    "FitError",
    "Fitted",
    "Labelled",
    "Summary",
    "Unmapped",
    "Vocabulary",
    "fit_behaviour",
    "fit_run",
    "label",
    "projection",
    "vocabulary",
]
