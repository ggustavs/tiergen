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
    assert out == "hq_lan: 0 errors, 0 warnings, 0 not computed\n"


def test_check_passes_with_a_warning(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", _scenario("hq_lan_capgap")]) == 0
    out = capsys.readouterr().out
    assert "warnings:\n  C14  sensors[1].capabilities" in out
    assert "SMB_DIALECT" in out


def test_check_fails_an_ill_formed_scenario(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", _scenario("hq_lan_broken")]) == 1
    out = capsys.readouterr().out
    assert all(f"  {check}  " in out for check in ("C01", "C04", "C05", "C09", "C10", "C12"))
    assert "hq_lan_broken: 10 errors" in out


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


def test_build_writes_a_self_contained_run_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "run1"
    assert main(["build", _scenario("linux_slice"), "--out", str(out)]) == 0
    assert "wrote" in capsys.readouterr().out
    assert sorted(p.name for p in out.iterdir()) == [
        "addresses.json",
        "manifest.docker.json",
        "models",
        "program.lab-attacker-0.json",
        "program.lab-web_server-0.json",
        "program.lab-workstation-0.json",
        "routes.json",
        "scenario.json",
    ]
    program = json.loads((out / "program.lab-workstation-0.json").read_text())
    assert program["hostname"] == "lab-workstation-0"
    assert program["peers"]["web"] == [
        {
            "instance": "lab/web_server[0]",
            "address": "10.20.0.80",
            "served": [{"protocol": "http", "port": 80, "transport": "tcp"}],
        }
    ]
    assert program["behaviours"][0]["action_map"]["web_get"]["params"]["path"]["options"] == [
        "/",
        "/news",
    ]
    manifest = json.loads((out / "manifest.docker.json").read_text())
    assert [h["instance"] for h in manifest["hosts"]] == [
        "lab/workstation[0]",
        "lab/web_server[0]",
        "lab/attacker[0]",
    ]

    plan = json.loads((out / "addresses.json").read_text())
    assert plan["gateways"] == {"lan": "10.20.0.1", "mgmt": "10.98.0.1"}
    assert plan["addresses"]["lab/web_server[0]"] == {"lan": "10.20.0.80", "mgmt": "10.98.0.3"}
    assert plan["addresses"]["lab/workstation[0]"] == {"lan": "10.20.0.2", "mgmt": "10.98.0.2"}

    # The run directory checks on its own: IR as JSON, with its resources beside it.
    assert main(["check", str(out / "scenario.json")]) == 0
    assert "0 errors, 0 warnings" in capsys.readouterr().out


def test_build_writes_nothing_for_a_scenario_with_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "run1"
    assert main(["build", _scenario("hq_lan_broken"), "--out", str(out)]) == 1
    assert "nothing written" in capsys.readouterr().err
    assert not out.exists()


def test_build_refuses_a_directory_that_is_not_empty(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "keep.txt").write_text("mine")
    assert main(["build", _scenario("linux_slice"), "--out", str(tmp_path)]) == 2
    assert "not an empty directory" in capsys.readouterr().err
    assert [p.name for p in tmp_path.iterdir()] == ["keep.txt"]


def test_infra_needs_a_built_run_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["infra", "up", str(tmp_path)]) == 2
    assert "holds no manifest" in capsys.readouterr().err


def test_capture_needs_a_run_that_is_up(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        main(["build", str(EXAMPLES / "linux_slice" / "scenario.py"), "--out", str(tmp_path / "r")])
        == 0
    )
    assert main(["capture", "start", str(tmp_path / "r")]) == 2
    assert "is the run up" in capsys.readouterr().err
    assert main(["capture", "stop", str(tmp_path / "r")]) == 2
    assert "nothing is capturing" in capsys.readouterr().err


def test_attrib_needs_a_run_that_is_up(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert (
        main(["build", str(EXAMPLES / "linux_slice" / "scenario.py"), "--out", str(tmp_path / "r")])
        == 0
    )
    assert main(["attrib", "start", str(tmp_path / "r")]) == 2
    assert "is the run up" in capsys.readouterr().err


def test_sensors_need_a_stopped_capture(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    scenario = EXAMPLES / "linux_slice" / "scenario.py"
    assert main(["build", str(scenario), "--out", str(tmp_path / "r")]) == 0
    assert main(["sensors", "run", str(tmp_path / "r")]) == 2
    assert "has the capture been stopped" in capsys.readouterr().err


def test_run_needs_a_built_directory(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run", str(tmp_path), "--for", "1"]) == 2
    assert "holds no manifest" in capsys.readouterr().err


def test_assemble_needs_a_run_that_completed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["assemble", str(tmp_path)]) == 2
    assert "scenario.json" in capsys.readouterr().err
