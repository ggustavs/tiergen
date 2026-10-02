"""The runtime interface of a service implementation."""

from pathlib import Path
from random import Random
from typing import Protocol, runtime_checkable

from tiergen.core.ir import Endpoint


class ServiceContext(Protocol):
    """What a service is given by the agent that starts it.

    A service is not an invocation: it carries no label, aims at no peers, and runs for the
    whole scenario. It gets the instance it serves for, the endpoints its manifest promised,
    a directory under the run's outputs for its logs, and a seeded generator.
    """

    @property
    def instance(self) -> str: ...

    @property
    def served(self) -> tuple[Endpoint, ...]:
        """The endpoints the package's ``impl.toml`` declares under ``[service]``."""
        ...

    @property
    def out(self) -> Path:
        """A directory the service may write into. It is collected with the run."""
        ...

    @property
    def rng(self) -> Random: ...


@runtime_checkable
class ServiceImpl(Protocol):
    """A server process on a default-compiled host."""

    def start(self, ctx: ServiceContext) -> None: ...

    def healthcheck(self, ctx: ServiceContext) -> bool:
        """True once every endpoint in ``served`` accepts connections."""
        ...

    def stop(self, ctx: ServiceContext) -> None: ...

    def served(self) -> tuple[Endpoint, ...]:
        """The same endpoints the package's ``impl.toml`` declares under ``[service]``."""
        ...
