"""Backend Protocols: Sensor, InfraBackend, AttributionBackend."""

from tiergen.interfaces.attribution import AttributionBackend, AttributionRecord
from tiergen.interfaces.capability import Capability, CapabilityInfo
from tiergen.interfaces.infra import InfraBackend
from tiergen.interfaces.sensor import Sensor, SensorDescriptor

__all__ = [
    "AttributionBackend",
    "AttributionRecord",
    "Capability",
    "CapabilityInfo",
    "InfraBackend",
    "Sensor",
    "SensorDescriptor",
]
