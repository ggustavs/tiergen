from collections import Counter

from hypothesis import given, settings
from hypothesis import strategies as st

from tiergen.core.records import invocation_id
from tiergen.core.sampling import instance_seed, rng, weighted


def test_streams_are_deterministic_and_independent() -> None:
    a = rng(7, "lab/ws[0]", "behaviour")
    b = rng(7, "lab/ws[0]", "behaviour")
    assert [a.random() for _ in range(5)] == [b.random() for _ in range(5)]
    assert instance_seed(7, "lab/ws[0]", "behaviour") != instance_seed(7, "lab/ws[0]", "impl")
    assert instance_seed(7, "lab/ws[0]", "impl") != instance_seed(7, "lab/ws[1]", "impl")
    assert instance_seed(7, "lab/ws[0]", "impl") != instance_seed(8, "lab/ws[0]", "impl")
    # Drawing from one stream leaves another untouched: an impl cannot shift the dwell times.
    impl = rng(7, "lab/ws[0]", "impl")
    for _ in range(100):
        impl.random()
    assert (
        rng(7, "lab/ws[0]", "behaviour").random()
        == b.__class__(instance_seed(7, "lab/ws[0]", "behaviour")).random()
    )


def test_weighted_ignores_insertion_order_and_follows_the_weights() -> None:
    forward = {"a": 1.0, "b": 3.0}
    backward = {"b": 3.0, "a": 1.0}
    assert [weighted(rng(1, "x", "selection"), forward) for _ in range(20)] == [
        weighted(rng(1, "x", "selection"), backward) for _ in range(20)
    ]
    r = rng(2, "x", "selection")
    counts = Counter(weighted(r, forward) for _ in range(4000))
    assert 0.65 < counts["b"] / 4000 < 0.85


def test_invocation_ids() -> None:
    assert (
        invocation_id("corp/eng/workstation[3]", "office", 17)
        == "corp/eng/workstation[3]/office#17"
    )


@given(seed=st.integers(), instance=st.text(max_size=20), n=st.integers(0, 50))
@settings(max_examples=50, deadline=None)
def test_seeds_are_64_bit_and_stable(seed: int, instance: str, n: int) -> None:
    s = instance_seed(seed, instance, "behaviour")
    assert 0 <= s < 2**64
    assert s == instance_seed(seed, instance, "behaviour")
    assert invocation_id(instance, "b", n).endswith(f"/b#{n}")
