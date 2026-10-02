from dataclasses import replace
from pathlib import Path

import pytest
from agent_support import program

from tiergen.cli.main import main
from tiergen.core.ir import Distribution, ScheduleEvent
from tiergen.runtime.agent_linux.program import ProgramError, load_program, validate

EXAMPLES = Path(__file__).parents[3] / "examples"


def test_the_built_examples_load(tmp_path: Path) -> None:
    for name in ("linux_slice", "hq_lan", "two_teams"):
        assert (
            main(["build", str(EXAMPLES / name / "scenario.py"), "--out", str(tmp_path / name)])
            == 0
        )
        for path in sorted((tmp_path / name).glob("program.*.json")):
            load_program(path)
    ws = load_program(tmp_path / "linux_slice" / "program.lab-workstation-0.json")
    assert [b.name for b in ws.behaviours] == ["browse"]
    assert [(e.at_s, e.op, e.arg) for e in ws.schedule] == [(0.0, "start", "browse")]
    web = load_program(tmp_path / "linux_slice" / "program.lab-web_server-0.json")
    assert web.services == ("http.serve",)


def test_what_the_checks_cannot_see_is_held_at_load() -> None:
    validate(program())
    b = program().behaviours[0]
    bad = [
        (replace(b, dwell=(Distribution("gamma", (1.0,)), b.dwell[1])), "unknown family"),
        (replace(b, dwell=(Distribution("exponential", (0.0,)), b.dwell[1])), "positive mean"),
        (
            replace(b, dwell=(Distribution("weibull", (1.0,)), b.dwell[1])),
            "shape and a positive scale",
        ),
        (replace(b, dwell=(Distribution("empirical", ()), b.dwell[1])), "non-negative samples"),
        (replace(b, dwell=b.dwell[:1]), "1 dwell distributions for 2 states"),
        (replace(b, rate=(1.0,) * 25), "24 or 168 entries"),
    ]
    for behaviour, message in bad:
        with pytest.raises(ProgramError, match=message):
            validate(replace(program(), behaviours=(behaviour,)))
    with pytest.raises(ProgramError, match=r"no implementation selected for 'http\.get'"):
        validate(replace(program(), impls={}))
    with pytest.raises(ProgramError, match="names no behaviour"):
        validate(replace(program(), schedule=(ScheduleEvent(0.0, "lab/ws", "start", "office"),)))
    with pytest.raises(ProgramError, match="set_rate"):
        validate(replace(program(), schedule=(ScheduleEvent(0.0, "lab/ws", "set_rate", -1.0),)))
    with pytest.raises(ProgramError, match="services"):
        validate(replace(program(), services=("http.serve",)))


def test_a_file_that_is_not_a_program_is_a_program_error(tmp_path: Path) -> None:
    (tmp_path / "p.json").write_text("{}")
    with pytest.raises(ProgramError, match=r"p\.json"):
        load_program(tmp_path / "p.json")
