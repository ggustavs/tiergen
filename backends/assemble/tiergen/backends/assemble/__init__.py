"""What ``tiergen assemble`` does: every configured sensor over the capture, the join of
invocation records, attribution records and each sensor's connections into per-sensor
labels, the flags for what the join could not explain, and the manifest."""

from tiergen.backends.assemble.assemble import AssembleError, Summary, assemble
from tiergen.backends.assemble.join import Joined, join, signatures
from tiergen.backends.assemble.manifest import Manifest

__all__ = ["AssembleError", "Joined", "Manifest", "Summary", "assemble", "join", "signatures"]
