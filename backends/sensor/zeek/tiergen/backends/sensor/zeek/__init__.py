"""Zeek: conn.log as the required core, per-protocol logs as APP_EVENTS.

The descriptor; the runtime is ``tiergen.backends.sensor.zeek.runtime``, registered under
``tiergen.sensors.runtimes`` and loaded only by what runs sensors.
"""

from tiergen.interfaces import Capability, SensorDescriptor

DESCRIPTOR = SensorDescriptor(
    id="zeek",
    versions=("7.0", "7.0.11"),
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
