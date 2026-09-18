import json
from pathlib import Path

import pytest

from tiergen.cli.main import main

EXAMPLES = Path(__file__).parents[2] / "examples"


def _scenario(name: str) -> str:
    return str(EXAMPLES / name / "scenario.py")


def test_check_passes_a_well_formed_scenario(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", _scenario("hq_lan")]) == 0
    out = capsys.readouterr().out
    assert "hq_lan: 0 errors, 0 warnings, 1 not computed" in out
    assert "net_raw" in out


def test_check_passes_with_a_warning(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", _scenario("hq_lan_capgap")]) == 0
    out = capsys.readouterr().out
    assert "warnings:\n  C14  sensors[1].capabilities" in out
    assert "SMB_DIALECT" in out


def test_check_fails_an_ill_formed_scenario(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", _scenario("hq_lan_broken")]) == 1
    out = capsys.readouterr().out
    assert all(f"  {check}  " in out for check in ("C01", "C04", "C05", "C12"))
    assert "hq_lan_broken: 5 errors" in out


def test_emitted_json_checks_the_same_as_the_python_it_came_from(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ir = tmp_path / "hq_lan.json"
    assert main(["check", _scenario("hq_lan_capgap"), "--emit-json", str(ir)]) == 0
    from_python = capsys.readouterr().out
    assert json.loads(ir.read_text())["name"] == "hq_lan_capgap"
    models = str(EXAMPLES / "hq_lan_capgap" / "models")
    assert main(["check", str(ir), "--models", models]) == 0
    assert capsys.readouterr().out == from_python


def test_models_defaults_to_the_directory_beside_the_scenario(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    ir = tmp_path / "hq_lan.json"
    main(["check", _scenario("hq_lan"), "--emit-json", str(ir)])
    capsys.readouterr()
    assert main(["check", str(ir)]) == 1
    assert "does not exist" in capsys.readouterr().out


@pytest.mark.parametrize("content", [None, "x = 1\n", "{not json"])
def test_a_scenario_that_cannot_be_loaded_exits_2(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], content: str | None
) -> None:
    path = tmp_path / ("scenario.json" if content == "{not json" else "scenario.py")
    if content is not None:
        path.write_text(content)
    assert main(["check", str(path)]) == 2
    assert "cannot load" in capsys.readouterr().err


def test_impls_list_filters(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["impls", "list", "--protocol", "smb", "--platform", "windows"]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines[0].split() == ["ID", "KIND", "PLATFORMS", "PROVIDES"]
    assert [line.split()[0] for line in lines[1:]] == ["smb.windows_native"]

    assert main(["impls", "list", "--kind", "service"]) == 0
    ids = [line.split()[0] for line in capsys.readouterr().out.splitlines()[1:]]
    assert ids == ["http.nginx", "smb.samba"]

    assert main(["impls", "list", "--protocol", "ssh"]) == 0
    assert capsys.readouterr().out == "no implementations match\n"
