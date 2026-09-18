"""Protocol signatures with expected traffic shapes. One module per protocol, no tool deps."""

from collections.abc import Mapping
from types import MappingProxyType

from tiergen.protocols import dns, http, kerberos, scan, smb, ssh
from tiergen.protocols.signature import Param, Signature, TrafficShape

_MODULES = (http, dns, smb, kerberos, ssh, scan)

SIGNATURES: Mapping[str, Signature] = MappingProxyType(
    {signature.id: signature for module in _MODULES for signature in module.SIGNATURES}
)
"""Every known signature, by id."""

__all__ = ["SIGNATURES", "Param", "Signature", "TrafficShape"]
