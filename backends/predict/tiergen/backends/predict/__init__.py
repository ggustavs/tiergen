"""What ``tiergen predict`` does: the scenario simulated several times and summarised at
the common event level, per kind and service, with Monte Carlo intervals over the
replicates. Section 9's prediction, by sampling the denotation rather than solving it."""

from tiergen.backends.predict.predict import Prediction, Row, predict, render

__all__ = ["Prediction", "Row", "predict", "render"]
