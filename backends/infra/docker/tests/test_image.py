"""The agent image's build context and tag, without a daemon."""

from pathlib import Path

from tiergen.backends.infra.docker import image


def test_the_context_holds_the_members_without_their_tests_and_the_tag_follows_it(
    tmp_path: Path,
) -> None:
    spec = image.agent()
    ctx = image.context(tmp_path / "ctx", spec)
    assert (ctx / "Dockerfile").read_text() == image.dockerfile()
    for where, _ in image.PACKAGES:
        assert (ctx / where / "pyproject.toml").is_file(), where
    assert (ctx / "runtime/agent_linux/tiergen/runtime/agent_linux/main.py").is_file()
    assert not (ctx / "core/tests").exists()
    assert not list(ctx.rglob("__pycache__"))
    tag = image.tag(ctx, spec)
    assert tag == f"{image.NAME}:{image.digest(ctx)}"
    assert len(image.digest(ctx)) == 12
    again = image.context(tmp_path / "again", spec)
    assert image.tag(again, spec) == tag
    (again / "core" / "pyproject.toml").write_text("changed")
    assert image.tag(again, spec) != tag
    # Another image: its own Dockerfile and loose files, no members.
    (tmp_path / "a.c").write_text("int main(void) { return 0; }\n")
    other = image.Spec("tiergen/other", "FROM scratch\n", (), (("src/a.c", tmp_path / "a.c"),))
    ctx2 = image.context(tmp_path / "other", other)
    assert sorted(p.relative_to(ctx2).as_posix() for p in ctx2.rglob("*") if p.is_file()) == [
        "Dockerfile",
        "src/a.c",
    ]
    assert image.tag(ctx2, other).startswith("tiergen/other:")
