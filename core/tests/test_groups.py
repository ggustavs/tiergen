import pytest

from tiergen.core.dsl import group, kind, scenario, tie
from tiergen.core.groups import descendants, instance_ids, parse_target, paths, select, targets

Dc = kind("dc", platforms=["windows"])
Fs = kind("fs", platforms=["linux"])
Ws = kind("ws", ties=[tie("fs", Fs, "multiple"), tie("dc", Dc, "single")], platforms=["linux"])
Atk = kind("atk", ties=[tie("victim", Ws, "multiple")], platforms=["linux"])

CORP = group("corp", instances={Dc: 1, Atk: 1}, attachments={})
ENG = group("eng", instances={Fs: 1, Ws: 2}, attachments={}, parent=CORP, wiring={"ws.dc": CORP})
SALES = group(
    "sales", instances={Fs: 2, Ws: 1}, attachments={}, parent=CORP, wiring={"ws.dc": CORP}
)
ATK_WIRED = group(
    "corp", instances={Dc: 1, Atk: 1}, attachments={}, wiring={"atk.victim": [ENG, SALES]}
)
S = scenario(
    "org",
    groups=[ATK_WIRED, ENG, SALES],
    bindings={},
    topology="t",
    egress="none",
    duration_s=1,
    capture_points=[],
    sensors=[],
    seed=0,
)


def test_paths_and_instance_ids_follow_group_then_kind_then_index() -> None:
    assert paths(S) == ["corp", "corp/eng", "corp/sales"]
    assert [i for _, _, i in instance_ids(S)] == [
        "corp/dc[0]",
        "corp/atk[0]",
        "corp/eng/fs[0]",
        "corp/eng/ws[0]",
        "corp/eng/ws[1]",
        "corp/sales/fs[0]",
        "corp/sales/fs[1]",
        "corp/sales/ws[0]",
    ]
    assert descendants(S, "corp") == ["corp", "corp/eng", "corp/sales"]
    assert descendants(S, "corp/eng") == ["corp/eng"]


def test_a_tie_reaches_exactly_the_wired_groups_instances_of_its_target_kind() -> None:
    assert targets(S, "corp/eng", "ws", "fs") == ["corp/eng/fs[0]"]
    assert targets(S, "corp/sales", "ws", "fs") == ["corp/sales/fs[0]", "corp/sales/fs[1]"]
    assert targets(S, "corp/eng", "ws", "dc") == ["corp/dc[0]"]
    assert targets(S, "corp", "atk", "victim") == [
        "corp/eng/ws[0]",
        "corp/eng/ws[1]",
        "corp/sales/ws[0]",
    ]


def test_an_unwired_or_unknown_tie_has_no_targets_rather_than_a_guess() -> None:
    unwired = group("eng", instances={Ws: 1}, attachments={}, parent=CORP)
    s = scenario(
        "u",
        groups=[CORP, unwired],
        bindings={},
        topology="t",
        egress="none",
        duration_s=1,
        capture_points=[],
        sensors=[],
        seed=0,
    )
    assert "ws.dc" not in unwired.ir.wiring
    assert targets(s, "corp/eng", "ws", "dc") is None
    assert targets(s, "corp/eng", "ws", "nope") is None
    assert targets(s, "corp/nowhere", "ws", "dc") is None


def test_a_wired_group_without_the_target_kind_contributes_nothing() -> None:
    odd = group("eng", instances={Ws: 1}, attachments={}, parent=CORP, wiring={"ws.fs": CORP})
    s = scenario(
        "o",
        groups=[CORP, odd],
        bindings={},
        topology="t",
        egress="none",
        duration_s=1,
        capture_points=[],
        sensors=[],
        seed=0,
    )
    assert targets(s, "corp/eng", "ws", "fs") == []


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "corp",
            [
                "corp/dc[0]",
                "corp/atk[0]",
                "corp/eng/fs[0]",
                "corp/eng/ws[0]",
                "corp/eng/ws[1]",
                "corp/sales/fs[0]",
                "corp/sales/fs[1]",
                "corp/sales/ws[0]",
            ],
        ),
        ("corp/eng", ["corp/eng/fs[0]", "corp/eng/ws[0]", "corp/eng/ws[1]"]),
        ("corp/ws", ["corp/eng/ws[0]", "corp/eng/ws[1]", "corp/sales/ws[0]"]),
        ("corp/eng/ws", ["corp/eng/ws[0]", "corp/eng/ws[1]"]),
        ("corp/eng/ws[1]", ["corp/eng/ws[1]"]),
        ("corp/dc[0]", ["corp/dc[0]"]),
        ("corp/eng/ws[2]", None),
        ("corp/eng/fs[0]x", None),
        ("corp/hr", None),
        ("corp/hr/ws", None),
        ("ws", None),
        ("ws[0]", None),
        ("/corp", None),
        ("corp/", None),
        ("corp//eng", None),
        ("", None),
    ],
)
def test_schedule_targets_select_instances(text: str, expected: list[str] | None) -> None:
    assert select(S, text) == expected


def test_parse_target_shape() -> None:
    parsed = parse_target("a/b[3]")
    assert parsed is not None
    assert (parsed.head, parsed.index) == ("a/b", 3)
    assert parse_target("a[3]") is None
