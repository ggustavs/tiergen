"""HTTP and HTTPS service through nginx.

Manifest only. The runtime lands in this package in M1.
"""

from importlib.resources import files

from tiergen.impls._base import load_manifest

DESCRIPTOR = load_manifest(files(__name__) / "impl.toml")
