from support import good, run


def test_the_baseline_scenario_is_clean() -> None:
    assert run(good()) == []
