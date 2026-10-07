"""Shared by sensor backends.

A sensor runtime runs its image over one capture point's pcap through the daemon and reads
its own logs into the common event model; what is common to both halves lives here: the
image run, Zeek's two log formats, and the driver that walks a run's sensors and points.
"""

from tiergen.backends.sensor._base.runner import SensorError, run_image
from tiergen.backends.sensor._base.zeeklog import read_zeek_log

__all__ = ["SensorError", "read_zeek_log", "run_image"]
