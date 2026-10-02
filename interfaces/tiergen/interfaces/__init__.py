"""Backend Protocols: Sensor, InfraBackend, AttributionBackend."""

from tiergen.interfaces.attribution import AttributionBackend, AttributionRecord
from tiergen.interfaces.capability import Capability, CapabilityInfo
from tiergen.interfaces.infra import HostOffer, InfraBackend, InfraDescriptor
from tiergen.interfaces.manifest import Attachment, HostSpec, NetworkSpec, RunManifest
from tiergen.interfaces.sensor import Sensor, SensorDescriptor

__all__ = [
    "Attachment",
    "AttributionBackend",
    "AttributionRecord",
    "Capability",
    "CapabilityInfo",
    "HostOffer",
    "HostSpec",
    "InfraBackend",
    "InfraDescriptor",
    "NetworkSpec",
    "RunManifest",
    "Sensor",
    "SensorDescriptor",
]
