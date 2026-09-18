"""Static checker over the scenario IR."""

from tiergen.check.diagnostics import Diagnostic, Severity
from tiergen.check.run import CHECKS, run_checks

__all__ = ["CHECKS", "Diagnostic", "Severity", "run_checks"]
