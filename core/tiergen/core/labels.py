"""The label tuple: what an invocation asserts about the traffic it produces."""

from dataclasses import dataclass
from typing import Literal

Outcome = Literal["succeeded", "failed"]


@dataclass(frozen=True, slots=True)
class Label:
    """Emitted when a primitive runs; unique per invocation.

    A label is an expectation until attribution joins observed connections to
    ``invocation``. ``outcome`` is what the tool reported: traffic from a failed exploit is
    real traffic and keeps its label, with ``outcome`` "failed". ``variant`` is None for an
    implementation that has no variants.
    """

    scenario: str
    instance: str
    behaviour: str
    action: str
    invocation: str
    impl: str
    variant: str | None
    expected_target: str
    outcome: Outcome
