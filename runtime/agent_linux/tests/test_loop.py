from collections import Counter

from agent_support import EPOCH, FakeAttribution, FakeClock, FakeImpl, program

from tiergen.core.ir import ScheduleEvent
from tiergen.core.program import Program
from tiergen.core.records import InvocationRecord
from tiergen.impls._base import PrimitiveImpl
from tiergen.runtime.agent_linux.loop import BehaviourLoop


def run(p: Program, impl: FakeImpl | None = None) -> tuple[list[InvocationRecord], FakeImpl]:
    impl = impl or FakeImpl()
    records: list[InvocationRecord] = []

    def primitive(impl_id: str) -> PrimitiveImpl:
        assert impl_id == "http.fake"
        return impl

    BehaviourLoop(
        p,
        p.behaviours[0],
        clock=FakeClock(),
        primitive=primitive,
        attribution=FakeAttribution(),
        sink=records.append,
    ).run()
    return records, impl


def test_a_run_is_a_function_of_the_program_and_the_seed() -> None:
    a, _ = run(program())
    b, _ = run(program())
    c, _ = run(program(seed=2))
    assert a
    assert a == b
    assert [r.start for r in a] != [r.start for r in c]
    assert [r.key.invocation for r in a[:3]] == [f"lab/ws[0]/browse#{n}" for n in (1, 2, 3)]
    assert all(r.key.impl == "http.fake" and r.key.variant is None for r in a)
    assert all(r.principal.principal == f"fake:{r.key.invocation}" for r in a)
    assert all(r.outcome == "succeeded" and r.end >= r.start >= EPOCH for r in a)
    assert all(r.key.action == "web_get" and r.key.behaviour == "browse" for r in a)


def test_an_implementation_drawing_from_its_stream_shifts_nothing_else() -> None:
    quiet, _ = run(program(), FakeImpl(draws=0))
    noisy, _ = run(program(), FakeImpl(draws=100))
    assert quiet == noisy


def test_a_raising_implementation_is_a_failed_outcome_and_the_loop_goes_on() -> None:
    records, impl = run(program(), FakeImpl(raise_at=2))
    assert [r.outcome for r in records[:3]] == ["succeeded", "failed", "succeeded"]
    assert len(impl.calls) == len(records) > 3


def test_targets_follow_select_and_parameters_follow_their_choice() -> None:
    one, impl = run(program(duration=36_000, select="one"))
    assert {len(r.key.targets) for r in one} == {1}
    assert {t for r in one for t in r.key.targets} == {"lab/web[0]", "lab/web[1]"}
    assert all(c.targets == r.key.targets for c, r in zip(impl.calls, one, strict=True))
    paths = Counter(str(c.params["path"]) for c in impl.calls)
    assert 0.7 < paths["/"] / len(impl.calls) < 0.9
    every, _ = run(program(select="all"))
    assert {r.key.targets for r in every} == {("lab/web[0]", "lab/web[1]")}


def test_a_weighted_implementation_choice_carries_its_variant() -> None:
    records, _ = run(program(duration=36_000, impls={"http.fake:a": 1.0, "http.fake:b": 1.0}))
    variants = Counter(r.key.variant for r in records)
    assert set(variants) == {"a", "b"}
    assert 0.35 < variants["a"] / len(records) < 0.65


def test_the_schedule_starts_stops_and_rescales() -> None:
    late, _ = run(program(schedule=(ScheduleEvent(100.0, "lab/ws", "start", "browse"),)))
    assert late
    assert min(r.start for r in late) >= EPOCH + 100
    stopped, _ = run(
        program(
            schedule=(
                ScheduleEvent(0.0, "lab/ws", "start", "browse"),
                ScheduleEvent(300.0, "lab/ws", "stop", "browse"),
            )
        )
    )
    assert stopped
    assert max(r.start for r in stopped) < EPOCH + 300
    frozen, _ = run(
        program(
            schedule=(
                ScheduleEvent(0.0, "lab/ws", "start", "browse"),
                ScheduleEvent(200.0, "lab/ws", "set_rate", 0.0),
            )
        )
    )
    assert frozen
    assert max(r.start for r in frozen) < EPOCH + 200
    never, _ = run(program(schedule=()))
    assert never == []
    plain, _ = run(program(duration=36_000))
    doubled, _ = run(
        program(
            duration=36_000,
            schedule=(
                ScheduleEvent(0.0, "lab/ws", "start", "browse"),
                ScheduleEvent(0.0, "lab/ws", "set_rate", 2.0),
            ),
        )
    )
    assert 1.8 < len(doubled) / len(plain) < 2.2


def test_the_rate_curve_is_read_in_local_time() -> None:
    # The scenario starts at 08:00 local on a Monday; the curve is zero until 10:00.
    day = tuple(0.0 if h < 10 else 1.0 for h in range(24))
    records, _ = run(program(duration=4 * 3600, rate=day))
    assert records
    assert min(r.start for r in records) >= EPOCH + 2 * 3600
    week = tuple(0.0 if i < 8 + 2 else 1.0 for i in range(168))  # Monday 10:00 onward
    weekly, _ = run(program(duration=4 * 3600, rate=week))
    assert weekly
    assert min(r.start for r in weekly) >= EPOCH + 2 * 3600
