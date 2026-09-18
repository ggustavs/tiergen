"""The common event model: what every sensor's output is mapped into.

``ConnEvent`` is the required core, the floor a sensor must meet. ``AppEvent`` exists only
for sensors that declare the APP_EVENTS capability. tiergen never reconstructs flows; these
are the sensor's own connections and records, renamed into one schema.

Both events keep the sensor's raw record in ``raw``. Nothing in core, fit or fidelity may
read ``raw``. A field a consumer needs is promoted to a declared capability first; reading
``raw`` instead is a bypass of the capability query and should fail review.
"""

from dataclasses import dataclass
from typing import Literal

from tiergen.core.codec import JsonValue

ConnState = Literal["attempted", "established", "closed", "reset", "rejected", "other"]


@dataclass(frozen=True, slots=True)
class SensorFlowId:
    """A sensor's native connection identity: Zeek ``uid``, Suricata ``flow_id``.

    Ids from different sensors are never comparable, so the sensor is part of the id.
    """

    sensor: str
    native: str


@dataclass(frozen=True, slots=True)
class FiveTuple:
    """Originator and responder endpoints, and the transport as the sensor names it."""

    orig_addr: str
    orig_port: int
    resp_addr: str
    resp_port: int
    proto: str


@dataclass(frozen=True, slots=True)
class ConnEvent:
    """One connection as the sensor saw it. The required core.

    ``start`` is seconds since the epoch. ``duration`` and the four counters are None when
    the sensor left them unset for this connection; None is not zero.
    """

    flow: SensorFlowId
    five_tuple: FiveTuple
    start: float
    duration: float | None
    orig_bytes: int | None
    resp_bytes: int | None
    orig_pkts: int | None
    resp_pkts: int | None
    state: ConnState
    raw: dict[str, JsonValue]


@dataclass(frozen=True, slots=True)
class AppEvent:
    """One per-request or per-operation record under a connection. Needs APP_EVENTS.

    ``index`` orders the events of one connection and, with ``flow``, is the identity a
    sub-connection label attaches to. ``fields`` holds normalised values, including the
    fingerprints of whichever capabilities the sensor declares.
    """

    flow: SensorFlowId
    index: int
    ts: float
    protocol: str
    fields: dict[str, JsonValue]
    raw: dict[str, JsonValue]


type Event = ConnEvent | AppEvent
