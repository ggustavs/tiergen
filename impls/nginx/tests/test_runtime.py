"""The nginx runtime as a child process; skipped without the binary or the ports."""

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from random import Random

import httpx
import pytest

from tiergen.core.ir import Endpoint
from tiergen.impls.nginx.runtime import NginxRuntime, config

needs_nginx = pytest.mark.skipif(
    shutil.which("nginx") is None or shutil.which("openssl") is None or os.geteuid() != 0,
    reason="needs nginx, openssl and the privilege to bind ports 80 and 443",
)


@dataclass(frozen=True, slots=True)
class Ctx:
    instance: str
    served: tuple[Endpoint, ...]
    out: Path
    rng: Random


def test_the_configuration_keeps_everything_under_out(tmp_path: Path) -> None:
    text = config(tmp_path, "lab/web[0]", NginxRuntime().served())
    assert f"access_log {tmp_path / 'access.log'};" in text
    assert "listen 80;" in text
    assert "listen 443 ssl;" in text
    assert f"ssl_certificate {tmp_path / 'cert.pem'};" in text
    assert "/var/" not in text


@needs_nginx
def test_nginx_serves_every_path_from_the_generated_site(tmp_path: Path) -> None:
    runtime = NginxRuntime()
    ctx = Ctx("lab/web[0]", runtime.served(), tmp_path, Random(1))
    assert runtime.healthcheck(ctx) is False
    runtime.start(ctx)
    try:
        for _ in range(50):
            if runtime.healthcheck(ctx):
                break
            __import__("time").sleep(0.1)
        assert runtime.healthcheck(ctx)
        assert httpx.get("http://127.0.0.1/news").status_code == 200
        assert httpx.get("https://127.0.0.1/", verify=False).text.startswith("<!doctype html>")
    finally:
        runtime.stop(ctx)
    assert runtime.healthcheck(ctx) is False
    assert "/news" in (tmp_path / "access.log").read_text()
