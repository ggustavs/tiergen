"""The runtime interface of an adapter to an external framework. Nothing in M0 implements it."""

from collections.abc import Iterable
from typing import Protocol

from tiergen.core.codec import JsonValue
from tiergen.core.labels import Outcome
from tiergen.impls._base.descriptor import CatalogEntry
from tiergen.impls._base.impl import Context


class AdapterImpl(Protocol):
    """Runs entries of a framework's catalog, such as CALDERA abilities."""

    def catalog(self) -> Iterable[CatalogEntry]:
        """The same entries the package's ``impl.toml`` lists, so checks stay static."""
        ...

    def run(self, ctx: Context, catalog_id: str, **params: JsonValue) -> Outcome: ...
