from importlib import import_module


def test_import() -> None:
    assert import_module("tiergen.interfaces").__name__ == "tiergen.interfaces"
