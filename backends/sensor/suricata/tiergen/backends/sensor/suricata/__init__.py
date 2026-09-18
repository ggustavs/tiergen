"""Suricata: eve.json flow records as the required core, app-layer events as APP_EVENTS.

Descriptor only. The ingest and label runtime lands in this package in M1.
"""

from tiergen.interfaces import Capability, SensorDescriptor

DESCRIPTOR = SensorDescriptor(
    id="suricata",
    versions=("7.0.7",),
    modes=("offline", "live"),
    capabilities=frozenset(
        {
            Capability.APP_EVENTS,
            Capability.TLS_JA4,
            Capability.TLS_JA3,
            Capability.HTTP_USER_AGENT,
        }
    ),
)
