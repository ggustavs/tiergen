"""Running the checks."""

from collections.abc import Callable, Iterator, Mapping

from tiergen.check import (
    c01_ties,
    c02_directed,
    c03_actions,
    c04_process,
    c05_resources,
    c06_interface,
    c07_platform,
    c08_impls,
    c09_planes,
    c10_addresses,
    c11_labels,
    c12_schedule,
    c13_sensors,
    c14_cross_sensor,
    c15_coverage,
    c16_params,
)
from tiergen.check.context import Context
from tiergen.check.diagnostics import Diagnostic
from tiergen.core.ir import Scenario
from tiergen.core.resources import Resources
from tiergen.impls._base import ImplDescriptor
from tiergen.interfaces import InfraDescriptor, SensorDescriptor
from tiergen.protocols import SIGNATURES, Signature

Check = Callable[[Context], Iterator[Diagnostic]]

CHECKS: tuple[tuple[str, Check], ...] = (
    ("C01", c01_ties.check),
    ("C02", c02_directed.check),
    ("C03", c03_actions.check),
    ("C04", c04_process.check),
    ("C05", c05_resources.check),
    ("C06", c06_interface.check),
    ("C07", c07_platform.check),
    ("C08", c08_impls.check),
    ("C09", c09_planes.check),
    ("C10", c10_addresses.check),
    ("C11", c11_labels.check),
    ("C12", c12_schedule.check),
    ("C13", c13_sensors.check),
    ("C14", c14_cross_sensor.check),
    ("C15", c15_coverage.check),
    ("C16", c16_params.check),
)


def run_checks(
    scenario: Scenario,
    resources: Resources,
    impls: Mapping[str, ImplDescriptor],
    sensors: Mapping[str, SensorDescriptor],
    infra: Mapping[str, InfraDescriptor],
    signatures: Mapping[str, Signature] = SIGNATURES,
) -> list[Diagnostic]:
    """Every diagnostic for ``scenario``, in check order."""
    ctx = Context(scenario, resources, impls, sensors, infra, signatures)
    return [diagnostic for _, check in CHECKS for diagnostic in check(ctx)]
