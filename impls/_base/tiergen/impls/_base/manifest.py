"""Loading ``impl.toml`` into an ``ImplDescriptor``."""

import tomllib
from importlib.resources.abc import Traversable
from pathlib import Path

from tiergen.core.codec import CodecError, from_json
from tiergen.impls._base.descriptor import ImplDescriptor


class ManifestError(ValueError):
    """An ``impl.toml`` is malformed. The message names the file and the offending path."""


def parse_manifest(text: str, source: str) -> ImplDescriptor:
    """Decode the text of an ``impl.toml``. ``source`` names it in error messages."""
    try:
        descriptor = from_json(ImplDescriptor, tomllib.loads(text))
    except (tomllib.TOMLDecodeError, CodecError) as err:
        raise ManifestError(f"{source}: {err}") from err
    if (descriptor.kind == "service") != (descriptor.service is not None):
        raise ManifestError(
            f"{source}: a [service] table is required for, and only for, kind 'service'"
        )
    if descriptor.catalog and descriptor.kind != "adapter":
        raise ManifestError(f"{source}: only kind 'adapter' may have a catalog")
    return descriptor


def load_manifest(source: Path | Traversable) -> ImplDescriptor:
    """Read and decode an ``impl.toml`` from a path or a package resource."""
    return parse_manifest(source.read_text(encoding="utf-8"), str(source))
