from pathlib import Path

import pytest

from tiergen.core.resources import DictResources, DirResources, Resources


@pytest.fixture
def models(tmp_path: Path) -> DirResources:
    (tmp_path / "ws.states.json").write_text('["idle", "web_get"]')
    (tmp_path / "lan.zeek").write_text("# opaque sensor config\n")
    (tmp_path / "lan.rules").mkdir()
    return DirResources(tmp_path)


def test_json_resource_is_the_dot_json_file(models: DirResources) -> None:
    assert models.exists("ws.states")
    assert models.get("ws.states") == ["idle", "web_get"]


def test_opaque_resources_exist_but_have_no_value(models: DirResources) -> None:
    assert models.exists("lan.zeek")
    assert models.exists("lan.rules")
    with pytest.raises(KeyError):
        models.get("lan.zeek")


def test_missing_resource(models: DirResources) -> None:
    assert not models.exists("ws.transitions")
    with pytest.raises(KeyError):
        models.get("ws.transitions")


@pytest.mark.parametrize("name", ["../ws.states", "sub/ws.states", "", ".hidden", "a b"])
def test_a_name_that_is_not_a_plain_name_is_not_a_resource(models: DirResources, name: str) -> None:
    assert not models.exists(name)
    with pytest.raises(KeyError):
        models.get(name)


def test_dict_resources() -> None:
    store: Resources = DictResources({"a": [1, 2], "null": None}, opaque=frozenset({"cfg"}))
    assert store.get("a") == [1, 2]
    assert store.exists("null")
    assert store.get("null") is None
    assert store.exists("cfg")
    assert not store.exists("b")
    with pytest.raises(KeyError):
        store.get("cfg")
