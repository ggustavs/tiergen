from importlib import import_module


def test_import() -> None:
    assert import_module("tiergen.core").__name__ == "tiergen.core"
