"""The agent image's build context and tag, without a daemon."""

from pathlib import Path

from tiergen.backends.infra.docker import image


def test_the_context_holds_the_members_without_their_tests_and_the_tag_follows_it(
    tmp_path: Path,
) -> None:
    ctx = image.context(tmp_path / "ctx")
    assert (ctx / "Dockerfile").read_text() == image.dockerfile()
    for where, _ in image.PACKAGES:
        assert (ctx / where / "pyproject.toml").is_file(), where
    assert (ctx / "runtime/agent_linux/tiergen/runtime/agent_linux/main.py").is_file()
    assert not (ctx / "core/tests").exists()
    assert not list(ctx.rglob("__pycache__"))
    tag = image.tag(ctx)
    assert tag == f"{image.NAME}:{image.digest(ctx)}"
    assert len(image.digest(ctx)) == 12
    again = image.context(tmp_path / "again")
    assert image.tag(again) == tag
    (again / "core" / "pyproject.toml").write_text("changed")
    assert image.tag(again) != tag
