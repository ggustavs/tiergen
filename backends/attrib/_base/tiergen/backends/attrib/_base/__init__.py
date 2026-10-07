"""Shared by attribution backends: what a collector emits, and how it becomes records.

A collector is a process that prints one event per line; everything above that line is
here and in Python, whatever toolchain sits below it.
"""

from tiergen.backends.attrib._base.events import Event, EventKind, read_events
from tiergen.backends.attrib._base.join import Joined, join

__all__ = ["Event", "EventKind", "Joined", "join", "read_events"]
