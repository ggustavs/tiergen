"""Running the checks."""

from collections.abc import Callable, Iterator, Mapping

from tiergen.check import (
    c01_ties,
)
from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic
from tiergen.core.ir import Scenario
from tiergen.core.resources import Resources
from tiergen.impls._base import ImplDescriptor
from tiergen.interfaces import SensorDescriptor
from tiergen.protocols import SIGNATURES, Signature

Check = Callable[[Context], Iterator[Diagnostic]]

CHECKS: tuple[tuple[str, Check], ...] = (("C01", c01_ties.check),)
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
