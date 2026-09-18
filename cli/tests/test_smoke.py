from importlib import import_module


def test_import() -> None:
    assert import_module("tiergen.cli").__name__ == "tiergen.cli"
