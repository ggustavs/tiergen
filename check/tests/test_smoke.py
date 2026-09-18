from importlib import import_module


def test_import() -> None:
    assert import_module("tiergen.check").__name__ == "tiergen.check"
