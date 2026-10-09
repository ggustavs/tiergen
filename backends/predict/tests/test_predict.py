from pathlib import Path

import pytest

from tiergen.backends.predict import predict, render
from tiergen.cli.main import main
from tiergen.core.loader import load_scenario
from tiergen.core.resources import DirResources

EXAMPLES = Path(__file__).parents[3] / "examples"


def test_a_prediction_has_a_row_per_kind_and_service_with_an_interval() -> None:
    scenario = load_scenario(EXAMPLES / "linux_slice" / "scenario.py")
    p = predict(
        scenario, DirResources(EXAMPLES / "linux_slice" / "models"), replicates=3, hours=1.0
    )
    assert (p.replicates, p.hours) == (3, 1.0)
    assert p.hosts == {"workstation": 1, "attacker": 1}
    by_key = {(r.kind, r.service): r for r in p.rows}
    web = by_key[("workstation", "tcp/80")]
    assert web.rate > 20
    assert web.rate_interval[0] < web.rate < web.rate_interval[1]
    assert 0 < web.gap_median < web.gap_p90
    probes = [r for r in p.rows if r.kind == "attacker"]
    assert len(probes) == 1024
    text = render(p)
    assert "| workstation | 1 | tcp/80 |" in text
    assert text.startswith("# Prediction for linux_slice")


def test_the_command_prints_the_table_and_refuses_an_ill_formed_scenario(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        main(
            [
                "predict",
                str(EXAMPLES / "linux_slice" / "scenario.py"),
                "--replicates",
                "2",
                "--hours",
                "0.5",
            ]
        )
        == 0
    )
    assert "| workstation | 1 | tcp/80 |" in capsys.readouterr().out
    assert main(["predict", str(EXAMPLES / "hq_lan_broken" / "scenario.py")]) == 1
