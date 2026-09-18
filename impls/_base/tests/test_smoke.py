from importlib import import_module


def test_import() -> None:
    assert import_module("tiergen.impls._base").__name__ == "tiergen.impls._base"
