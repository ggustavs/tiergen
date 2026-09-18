"""Implementation interfaces, manifest schema, entry-point registry."""

from tiergen.impls._base.adapter import AdapterImpl
from tiergen.impls._base.descriptor import (
    CatalogEntry,
    Fingerprint,
    HostRequirements,
    ImplDescriptor,
    ServiceTable,
)
from tiergen.impls._base.impl import Context, PrimitiveImpl
from tiergen.impls._base.manifest import ManifestError, load_manifest, parse_manifest
from tiergen.impls._base.registry import load_impls
from tiergen.impls._base.service import ServiceImpl

__all__ = [
    "AdapterImpl",
    "CatalogEntry",
    "Context",
    "Fingerprint",
    "HostRequirements",
    "ImplDescriptor",
    "ManifestError",
    "PrimitiveImpl",
    "ServiceImpl",
    "ServiceTable",
    "load_impls",
    "load_manifest",
    "parse_manifest",
]
