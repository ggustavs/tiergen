"""Capabilities: what a sensor offers above the required core.

The required core is ``ConnEvent``. Everything else a consumer wants it must ask for by
name here and degrade explicitly when the sensor does not declare it. A missing capability
makes a result "not computed", never zero and never a silent default.
"""

from dataclasses import dataclass
from enum import Enum, auto


class Capability(Enum):
    """A named, typed extension to the common event model.

    The IR and reports refer to a capability by its ``name``. Adding a member touches
    neither ``ConnEvent`` nor any core consumer.
    """

    APP_EVENTS = auto()
    """Per-request or per-operation records under a connection. Enables sub-connection labels."""
    TLS_JA4 = auto()
    TLS_JA3 = auto()
    HTTP_USER_AGENT = auto()
    SSH_STRINGS = auto()
    SMB_DIALECT = auto()
    X509 = auto()


@dataclass(frozen=True, slots=True)
class CapabilityInfo:
    """One sensor's claim about one capability.

    ``schema`` names the typed shape the capability adds to ``AppEvent.fields``.
    ``coverage`` is the fraction of applicable events on which the field is populated. It
    starts as the sensor's own claim and is overwritten by the value ``fit`` measures on
    the real logs, so consumers see the number for this network.
    """

    schema: str
    coverage: float
