"""Backend Protocols: Sensor, InfraBackend, AttributionBackend."""

from tiergen.interfaces.attribution import AttributionBackend, AttributionRecord
from tiergen.interfaces.capability import Capability, CapabilityInfo
from tiergen.interfaces.infra import BackendError, HostOffer, InfraBackend, InfraDescriptor
from tiergen.interfaces.manifest import (
    Attachment,
    HostSpec,
    HostState,
    NetworkSpec,
    RouteSpec,
    RunManifest,
    RunState,
)
from tiergen.interfaces.sensor import Sensor, SensorDescriptor

__all__ = [
    "Attachment",
    "AttributionBackend",
    "AttributionRecord",
    "BackendError",
    "Capability",
    "CapabilityInfo",
    "HostOffer",
    "HostSpec",
    "HostState",
    "InfraBackend",
    "InfraDescriptor",
    "NetworkSpec",
    "RouteSpec",
    "RunManifest",
    "RunState",
    "Sensor",
    "SensorDescriptor",
]
