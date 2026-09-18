"""What a check reports."""

from dataclasses import dataclass
from typing import Literal

Severity = Literal["error", "warning", "not_computed"]


@dataclass(frozen=True, slots=True)
class Diagnostic:
    """One finding.

    ``check`` is the check's id, "C01" to "C15", numbered as in section 8 of the design
    document. ``path`` locates the finding in the IR, in the codec's path syntax.

    An ``error`` makes the scenario ill formed. A ``warning`` is a gap the engineer may
    accept knowingly. ``not_computed`` says part of a check could not run and names what was
    missing; it is never a pass.
    """

    check: str
    severity: Severity
    path: str
    message: str


def error(check: str, path: str, message: str) -> Diagnostic:
    return Diagnostic(check, "error", path, message)


def warning(check: str, path: str, message: str) -> Diagnostic:
    return Diagnostic(check, "warning", path, message)


def not_computed(check: str, path: str, message: str) -> Diagnostic:
    return Diagnostic(check, "not_computed", path, message)
