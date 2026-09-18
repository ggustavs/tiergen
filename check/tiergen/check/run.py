"""Running the checks."""

from collections.abc import Callable, Iterator, Mapping

from tiergen.check import (
    c01_ties,
    c02_directed,
    c03_actions,
    c04_process,
    c05_resources,
    c11_labels,
    c12_schedule,
    c14_cross_sensor,
    c15_coverage,
)
from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic
from tiergen.core.ir import Scenario
from tiergen.core.resources import Resources
from tiergen.impls._base import ImplDescriptor
from tiergen.interfaces import SensorDescriptor
from tiergen.protocols import SIGNATURES, Signature

Check = Callable[[Context], Iterator[Diagnostic]]

CHECKS: tuple[tuple[str, Check], ...] = (
    ("C01", c01_ties.check),
    ("C02", c02_directed.check),
    ("C03", c03_actions.check),
    ("C04", c04_process.check),
    ("C05", c05_resources.check),
    ("C11", c11_labels.check),
    ("C12", c12_schedule.check),
    ("C14", c14_cross_sensor.check),
    ("C15", c15_coverage.check),
)
"""Checks 9 and 10 need an infrastructure backend and arrive with M1."""


def run_checks(
    scenario: Scenario,
    resources: Resources,
    impls: Mapping[str, ImplDescriptor],
    sensors: Mapping[str, SensorDescriptor],
    signatures: Mapping[str, Signature] = SIGNATURES,
) -> list[Diagnostic]:
    """Every diagnostic for ``scenario``, in check order."""
    ctx = Context(scenario, resources, impls, sensors, signatures)
    return [diagnostic for _, check in CHECKS for diagnostic in check(ctx)]
