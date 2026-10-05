from importlib.metadata import EntryPoint

import pytest

from tiergen.interfaces import Capability, SensorDescriptor, registry

GOOD = SensorDescriptor("good", ("1.0",), ("offline",), frozenset({Capability.APP_EVENTS}))
MISNAMED = SensorDescriptor("other", ("1.0",), ("offline",), frozenset())
NOT_A_DESCRIPTOR = object()


def _use(monkeypatch: pytest.MonkeyPatch, name: str, attr: str) -> None:
    eps = [EntryPoint(name, f"{__name__}:{attr}", registry.GROUP)]

    def fake_entry_points(group: str) -> list[EntryPoint]:
        assert group == registry.GROUP
        return eps

    monkeypatch.setattr(registry, "entry_points", fake_entry_points)


def test_loads_descriptors_by_id(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, "good", "GOOD")
    assert registry.load_sensors() == {"good": GOOD}


def test_entry_point_name_must_equal_descriptor_id(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, "good", "MISNAMED")
    with pytest.raises(ValueError, match="'other'"):
        registry.load_sensors()


def test_entry_point_must_be_a_descriptor(monkeypatch: pytest.MonkeyPatch) -> None:
    _use(monkeypatch, "good", "NOT_A_DESCRIPTOR")
    with pytest.raises(TypeError, match="not a SensorDescriptor"):
        registry.load_sensors()


class FakeBackend:
    id = "fake"

    def up(self, manifest: object) -> None: ...

    def down(self, manifest: object) -> None: ...

    def quiesce(self, manifest: object, state: object) -> None: ...


def test_backends_are_constructed_only_when_asked_for(monkeypatch: pytest.MonkeyPatch) -> None:
    eps = [
        EntryPoint("fake", f"{__name__}:FakeBackend", registry.INFRA_BACKEND_GROUP),
        EntryPoint("other", f"{__name__}:FakeBackend", registry.INFRA_BACKEND_GROUP),
    ]

    def fake_entry_points(group: str) -> list[EntryPoint]:
        assert group == registry.INFRA_BACKEND_GROUP
        return eps

    monkeypatch.setattr(registry, "entry_points", fake_entry_points)
    found = registry.load_infra_backends(only={"fake"})
    assert list(found) == ["fake"]
    assert isinstance(found["fake"], FakeBackend)
    with pytest.raises(ValueError, match="'other'"):
        registry.load_infra_backends()
