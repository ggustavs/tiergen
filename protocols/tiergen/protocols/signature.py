"""Signatures: protocol-level primitives and the traffic each is expected to produce.

The IR references signatures, never tools. Attribution uses a signature's shape to match
observed connections to an invocation; conformance tests use it to check implementations.
"""

from dataclasses import dataclass
from typing import Literal

from tiergen.core.ir import Transport

ParamType = Literal["str", "int", "float", "bool"]
Role = Literal["client", "server"]
Reuse = Literal["none", "per_process", "per_session"]


@dataclass(frozen=True, slots=True)
class Param:
    """One typed parameter of a signature."""

    name: str
    type: ParamType
    required: bool = True


@dataclass(frozen=True, slots=True)
class TrafficShape:
    """The connections one invocation is expected to open.

    ``connections`` is an exact count or "many" when it depends on the parameters or the
    target. ``port`` is None when the destination port is the target endpoint's, or, for a
    scan, the parameters'. ``follow_on`` lists signatures whose traffic may accompany this
    one without being a separate invocation: a DNS lookup before an HTTP request, a
    Kerberos ticket before an SMB session. ``reuse`` says whether an invocation may ride on
    a connection an earlier one opened; if it may, per-request labels rely on ``AppEvent``s.
    """

    connections: int | Literal["many"]
    transport: Transport
    port: int | None
    follow_on: tuple[str, ...]
    reuse: Reuse


@dataclass(frozen=True, slots=True)
class Signature:
    """A protocol-level primitive.

    ``id`` is ``<protocol>.<name>``. A client signature is run by an action against a tie;
    ``endpoints`` lists the ``Endpoint.protocol`` values a tie's target may serve for the
    signature to make sense, and is empty when no served endpoint is needed, as for a scan.
    A server signature stands for serving ``endpoints``; it is selected in a binding and
    never appears in an action map.
    """

    id: str
    protocol: str
    role: Role
    endpoints: tuple[str, ...]
    params: tuple[Param, ...]
    shape: TrafficShape
