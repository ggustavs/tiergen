from dataclasses import replace

import pytest
from support import IMPLS, RESOURCES, good, only, run, with_binding

from tiergen.check import run_checks
from tiergen.core import ir
from tiergen.core.resources import DictResources
from tiergen.impls._base import CatalogEntry, HostRequirements, ImplDescriptor


def _choices(choices: dict[str, float]) -> ir.Scenario:
    return with_binding(good(), 0, impls=(ir.ImplSelection("http.get", choices),))


@pytest.mark.parametrize(
    ("choices", "path", "fragment"),
    [
        ({}, "choices", "no implementation is offered"),
        ({"http.ghost": 1.0}, "choices['http.ghost']", "not installed"),
        ({"scan.raw": 1.0}, "choices['scan.raw']", "does not provide http.get"),
        ({"http.cli:c": 1.0}, "choices['http.cli:c']", "no variant 'c'"),
        ({"http.cli:a": 0.0}, "choices['http.cli:a']", "not positive"),
        ({"http.cli:a": -1.0}, "choices['http.cli:a']", "not positive"),
    ],
)
def test_ill_formed_choices(choices: dict[str, float], path: str, fragment: str) -> None:
    # Other checks may object to the same choice; this one is about check 8 alone.
    [d] = [d for d in run(_choices(choices)) if d.check == "C08" and fragment in d.message]
    assert d.path == f"bindings[0].impls[0].{path}"


def test_a_used_signature_with_no_selection() -> None:
    [d] = only("C08", with_binding(good(), 0, impls=()))
    assert d.path == "bindings[0].impls"
    assert "http.get" in d.message


def test_an_unvarianted_choice_and_weights_that_do_not_sum_to_one_are_fine() -> None:
    assert only("C08", _choices({"http.cli": 3.0, "http.cli:b": 0.25})) == []


def test_choices_from_a_resource() -> None:
    s = with_binding(good(), 0, impls=(ir.ImplSelection("http.get", "cli.mix"),))
    [d] = only("C08", s, {**RESOURCES, "cli.mix": {"http.ghost": 1.0}})
    assert "not installed" in d.message


def test_unknown_signature_in_a_binding() -> None:
    selections = (*good().bindings[0].impls, ir.ImplSelection("http.teleport", {"http.cli": 1.0}))
    [d] = only("C08", with_binding(good(), 0, impls=selections))
    assert d.path == "bindings[0].impls[1].signature"


def test_run_sequence_names_an_installed_adapter_and_one_of_its_catalog_entries() -> None:
    adapter = ImplDescriptor(
        "attack.kit",
        "1",
        "adapter",
        (),
        HostRequirements(("linux",)),
        catalog=(CatalogEntry("recon", "Recon"),),
    )
    impls = {**IMPLS, adapter.id: adapter}
    store = DictResources(RESOURCES, frozenset({"lan.topology", "lan.rich", "lan.poor"}))

    def c08(arg: str) -> list[str]:
        s = replace(good(), schedule=(ir.ScheduleEvent(0, "cli", "run_sequence", arg),))
        return [d.message for d in run_checks(s, store, impls, {}) if d.check == "C08"]

    assert c08("attack.kit:recon") == []
    assert "no catalog entry 'exfil'" in c08("attack.kit:exfil")[0]
    assert "not an installed adapter" in c08("http.cli:recon")[0]
