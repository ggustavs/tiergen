"""Zeek: conn.log as the required core, per-protocol logs as APP_EVENTS.

Descriptor only. The ingest and label runtime lands in this package in M1.
"""

from tiergen.interfaces import Capability, SensorDescriptor

DESCRIPTOR = SensorDescriptor(
    id="zeek",
    versions=("7.0",),
    modes=("offline", "live"),
    capabilities=frozenset(
        {
            Capability.APP_EVENTS,
            Capability.TLS_JA4,
            Capability.TLS_JA3,
            Capability.HTTP_USER_AGENT,
            Capability.SSH_STRINGS,
            Capability.SMB_DIALECT,
            Capability.X509,
        }
    ),
)
