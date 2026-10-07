"""Capabilities: what a sensor offers above the required core.

The required core is ``ConnEvent``. Everything else a consumer wants it must ask for by
name here and degrade explicitly when the sensor does not declare it. A missing capability
makes a result "not computed", never zero and never a silent default.
"""

from dataclasses import dataclass
from enum import Enum, auto
from types import MappingProxyType


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
class Field:
    """One field a capability adds to ``AppEvent.fields``: its name and its JSON type."""

    name: str
    type: str


@dataclass(frozen=True, slots=True)
class Schema:
    """The typed shape a capability adds. ``APP_EVENTS`` adds no field of its own: it is
    the presence of ``AppEvent``s at all, whose ``protocol`` is one of ``PROTOCOLS``."""

    name: str
    fields: tuple[Field, ...]


PROTOCOLS = ("http", "tls", "dns", "ssh", "smb", "kerberos", "ntlm", "dce_rpc", "rdp")
"""What ``AppEvent.protocol`` may say, whatever the sensor calls its own log."""

SCHEMAS = MappingProxyType(
    {
        Capability.APP_EVENTS: Schema("app_events", ()),
        Capability.TLS_JA4: Schema("tls_ja4", (Field("ja4", "str"),)),
        Capability.TLS_JA3: Schema("tls_ja3", (Field("ja3", "str"),)),
        Capability.HTTP_USER_AGENT: Schema("http_user_agent", (Field("user_agent", "str"),)),
        Capability.SSH_STRINGS: Schema(
            "ssh_strings", (Field("client", "str"), Field("server", "str"))
        ),
        Capability.SMB_DIALECT: Schema("smb_dialect", (Field("dialect", "str"),)),
        Capability.X509: Schema(
            "x509", (Field("subject", "str"), Field("issuer", "str"), Field("fingerprint", "str"))
        ),
    }
)
"""The schema of every capability, defined once between the sensors: what each adds to
``AppEvent.fields`` and under which protocol's events it appears is the sensor's to map,
the names and types are not."""


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
