"""The runtime interface of a service implementation. Nothing in M0 implements it."""

from typing import Protocol

from tiergen.core.ir import Endpoint
from tiergen.impls._base.impl import Context


class ServiceImpl(Protocol):
    """A server process on a default-compiled host."""

    def start(self, ctx: Context) -> None: ...

    def healthcheck(self, ctx: Context) -> bool:
        """True once every endpoint in ``served`` accepts connections."""
        ...

    def stop(self, ctx: Context) -> None: ...

    def served(self) -> tuple[Endpoint, ...]:
        """The same endpoints the package's ``impl.toml`` declares under ``[service]``."""
        ...
