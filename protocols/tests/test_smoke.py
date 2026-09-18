from importlib import import_module


def test_import() -> None:
    assert import_module("tiergen.protocols").__name__ == "tiergen.protocols"
