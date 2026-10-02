"""Port scans through nmap.

The descriptor is loaded here; the runtime is ``tiergen.impls.nmap.runtime``, registered
under ``tiergen.impls.runtimes`` and imported only by the agent.
"""

from importlib.resources import files

from tiergen.impls._base import load_manifest

DESCRIPTOR = load_manifest(files(__name__) / "impl.toml")
