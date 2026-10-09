"""The tests are validated on the harness: type I near the level, power on the stated
perturbations. Seed counts are small here for CI; scripts/calibrate.py writes the table."""

import numpy as np
import pytest

from tiergen.core.ir import SemiMarkov
from tiergen.stats import (
    Interval,
    calibrate,
    markdown,
    power_for,
    render,
    report,
    run_test,
    statistics,
    two_sample,
)
from tiergen.stats.calibrate import Calibration, dump, load
from tiergen.stats.harness import (
    MARKS,
    WORKSTATION,
    Harness,
    office,
    perturb_transition,
    scale_dwell,
    scale_rate,
    streams_of,
)

HOSTS, HOURS, SEEDS, ROUNDS = 4, 2.0, 16, 100
CURVE = [0.2] * 8 + [1.0] * 10 + [0.2] * 6


@pytest.fixture(scope="module")
def truth() -> Harness:
    return office(HOSTS, rate=CURVE)


def test_the_harness_simulates_to_one_stream_per_workstation(truth: Harness) -> None:
    found = streams_of(truth, 1, hours=HOURS)
    assert len(found) == HOSTS
    assert all(len(s) > 20 for s in found)
    assert {m for s in found for m in s.marks} == set(MARKS.values())
    again = streams_of(truth, 1, hours=HOURS)
    assert again == found


def test_the_perturbations_change_only_what_they_name(truth: Harness) -> None:
    moved = perturb_transition(truth, "web_get", "api_get", 0.1)
    p = _process(moved)
    assert not isinstance(p.transitions, str)
    assert p.transitions[1] == pytest.approx((0.3, 0.2, 0.3, 0.2))
    assert sum(p.transitions[1]) == pytest.approx(1.0)
    with pytest.raises(ValueError, match=r"has no 0\.9 to move"):
        perturb_transition(truth, "web_get", "api_get", 0.9)
    slower = scale_dwell(truth, "wiki_get", 2.0)
    dwell = _process(slower).dwell
    assert not isinstance(dwell, str)
    assert dwell[2].params == pytest.approx((2.0 + np.log(2.0), 0.5))
    quiet = scale_rate(truth, 9, 0.5)
    curve = quiet.resources["ws.rate"]
    assert isinstance(curve, list)
    assert (curve[9], curve[8]) == (0.5, 1.0)


def test_every_shipped_test_is_calibrated_near_its_level_and_has_power(truth: Harness) -> None:
    rng = np.random.default_rng(3)
    alternatives = {
        "transition +0.1": perturb_transition(truth, "web_get", "api_get", 0.1),
        "dwell x1.25": scale_dwell(truth, "web_get", 1.25),
        "dwell x5": scale_dwell(truth, "web_get", 5.0),
    }
    rows: list[Calibration] = []
    for name, statistic in statistics(truth.tz).items():
        for label, alt in alternatives.items():
            rows.append(
                calibrate(
                    name,
                    statistic,
                    lambda seed: streams_of(truth, seed, hours=HOURS),
                    lambda seed, alt=alt: streams_of(alt, seed, hours=HOURS),
                    perturbation=label,
                    hosts=HOSTS,
                    hours=HOURS,
                    seeds=SEEDS,
                    rng=rng,
                    rounds=ROUNDS,
                )
            )
    # Type I: with 16 seeds the Wilson band around 0.05 reaches 0.28; nothing above 0.3.
    assert all(r.type_i <= 0.3 for r in rows), markdown(rows)
    # The gross perturbation: a dwell times five is visible to both gap distances even at
    # this small sample; the finer ones are what scripts/calibrate.py measures at larger ones.
    gross = [r for r in rows if r.perturbation == "dwell x5" and r.test.startswith("gap_")]
    assert len(gross) == 2
    assert all(r.power >= 0.75 for r in gross), markdown(rows)
    assert load(dump(rows)) == rows
    table = markdown(rows)
    assert table.count("\n") == len(rows) + 2
    assert power_for(rows, "gap_ks", 5, 2.0) is not None
    assert power_for(rows, "no_such_test", 5, 2.0) is None


def test_a_report_prints_the_power_beside_the_verdict(truth: Harness) -> None:
    rng = np.random.default_rng(5)
    a = streams_of(truth, 10, hours=HOURS)
    b = streams_of(scale_dwell(truth, "web_get", 3.0), 11, hours=HOURS)
    wired = run_test("gap_ks", statistics(truth.tz)["gap_ks"], a, b, rng, rounds=ROUNDS)
    assert wired.hosts == (HOSTS, HOSTS)
    assert wired.splits == 70
    assert wired.can_reject(0.05)
    assert not wired.can_reject(0.01)
    assert 0 < wired.p_value <= 1
    results = [
        two_sample.TestResult("gap_ks", 0.4, 0.01, (HOSTS, HOSTS), (300, 280), 70),
        two_sample.TestResult("mix_js", 0.02, 0.6, (HOSTS, HOSTS), (300, 280), 70),
        two_sample.TestResult("rate_error", float("nan"), float("nan"), (4, 4), (300, 280), 70),
        two_sample.TestResult("transition_g", 9.0, 0.048, (3, 3), (200, 200), 20),
    ]
    cal = [
        Calibration(
            "gap_ks", "dwell x3", HOSTS, HOURS, SEEDS, 0.05, 0.05, wilson_(0.05), 0.9, wilson_(0.9)
        )
    ]
    rows = report(results, cal, HOSTS, HOURS)
    assert [r.metric for r in rows] == ["gap_ks", "mix_js", "rate_error", "transition_g"]
    ks, js, rate, few = rows
    assert few.verdict == "too few hosts (20 splits)"
    assert ks.verdict == "rejected"
    assert ks.power == 0.9
    assert ks.reference == "dwell x3 at 4 hosts x 2 h"
    assert (js.verdict, js.power, js.reference) == ("not rejected", None, "uncalibrated")
    assert rate.verdict == "not computed"
    text = render(rows, "conformance")
    assert text.startswith("# conformance\n")
    assert "| gap_ks |" in text
    assert "power column" in text


def wilson_(p: float) -> Interval:
    return Interval(p - 0.05, p + 0.05)


def _process(h: Harness) -> SemiMarkov:
    ws = next(k for k in h.scenario.kinds if k.name == WORKSTATION)
    return ws.behaviours[0].process
