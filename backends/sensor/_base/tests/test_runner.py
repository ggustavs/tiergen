from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pytest

from tiergen.backends.infra.docker._client import Client
from tiergen.backends.sensor._base import run_image
from tiergen.interfaces import BackendError


class FakeDaemon:
    def __init__(self, userns: tuple[int, int] | None = (100000, 100000)) -> None:
        self.calls: list[tuple[object, ...]] = []
        self._userns = userns

    def userns(self) -> tuple[int, int] | None:
        return self._userns

    def ensure_image(self, image: str) -> None:
        self.calls.append(("pull", image))

    def run_helper(
        self,
        image: str,
        command: Sequence[str],
        network: str,
        cap_add: Sequence[str],
        mounts: Sequence[tuple[Path, str, bool]] = (),
        userns_host: bool = True,
    ) -> str:
        binds = tuple((str(s), t, ro) for s, t, ro in mounts)
        self.calls.append(("run", image, tuple(command), network, binds, userns_host))
        return ""

    def image_digest(self, tag: str) -> str:
        return "zeek/zeek@sha256:0123"


def test_the_image_runs_over_the_pcap_with_the_remapped_root_let_in(tmp_path: Path) -> None:
    fake = FakeDaemon()
    acls: list[list[str]] = []
    pcap = tmp_path / "capture" / "lan-span.pcapng"
    pcap.parent.mkdir()
    pcap.write_bytes(b"")
    config = tmp_path / "models" / "linux_slice.zeek"
    config.parent.mkdir()
    config.write_text("@load base/protocols/conn\n")
    out = tmp_path / "sensors" / "zeek" / "lan-span"
    command = ["zeek", "-r", "/pcap/lan-span.pcapng"]
    digest = run_image(
        cast(Client, fake),
        "zeek/zeek:7.0.11",
        command,
        pcap,
        config,
        out,
        acl=lambda a: acls.append(list(a)),
    )
    assert digest == "zeek/zeek@sha256:0123"
    assert out.is_dir()
    assert acls == [
        ["-m", "u:100000:rwx", str(out)],
        ["-m", "u:100000:r", str(pcap)],
        ["-m", "u:100000:rx", str(pcap.parent)],
        ["-R", "-m", "u:100000:rX", str(config)],
    ]
    assert fake.calls == [
        ("pull", "zeek/zeek:7.0.11"),
        (
            "run",
            "zeek/zeek:7.0.11",
            tuple(command),
            "none",
            (
                (str(pcap.resolve()), "/pcap/lan-span.pcapng", True),
                (str(config.resolve()), "/config/linux_slice.zeek", True),
                (str(out.resolve()), "/out", False),
            ),
            False,
        ),
    ]


def test_without_the_remap_nothing_runs(tmp_path: Path) -> None:
    fake = FakeDaemon(userns=None)
    with pytest.raises(BackendError, match=r"4\.19"):
        run_image(
            cast(Client, fake),
            "img",
            ["x"],
            tmp_path / "p",
            tmp_path / "c",
            tmp_path / "o",
            acl=lambda a: None,
        )
    assert fake.calls == []
