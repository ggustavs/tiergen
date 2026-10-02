"""nginx in the foreground as a child of the agent, serving a generated site.

Everything it writes goes under the service's output directory: the configuration, the
site, its temporary files, ``access.log`` and ``error.log``, so the access log comes back
with the run. The site answers every path with its index page, which is enough for the
paths a fitted ``Choice`` asks for; the ``https`` endpoint uses a self-signed certificate
made at start, until the lab CA exists.
"""

import socket
import subprocess
from pathlib import Path

from tiergen.core.ir import Endpoint
from tiergen.impls._base import ServiceContext

SERVED = (Endpoint("http", 80, "tcp"), Endpoint("https", 443, "tcp"))
INDEX = "<!doctype html><title>{instance}</title><h1>{instance}</h1><p>intranet</p>\n"


def _listen(endpoint: Endpoint, out: Path) -> str:
    if endpoint.protocol == "https":
        return (
            f"listen {endpoint.port} ssl;\n"
            f"        ssl_certificate {out / 'cert.pem'};\n"
            f"        ssl_certificate_key {out / 'key.pem'};"
        )
    return f"listen {endpoint.port};"


def config(out: Path, instance: str, served: tuple[Endpoint, ...]) -> str:
    listens = "\n        ".join(_listen(e, out) for e in served)
    return f"""pid {out / "nginx.pid"};
error_log {out / "error.log"};
worker_processes 1;
events {{ worker_connections 64; }}
http {{
    access_log {out / "access.log"};
    client_body_temp_path {out / "tmp"};
    proxy_temp_path {out / "tmp"};
    fastcgi_temp_path {out / "tmp"};
    uwsgi_temp_path {out / "tmp"};
    scgi_temp_path {out / "tmp"};
    server_tokens on;
    server {{
        {listens}
        server_name {instance.replace("/", "-")};
        root {out / "site"};
        location / {{ try_files $uri $uri/ /index.html; }}
    }}
}}
"""


class NginxRuntime:
    def __init__(self) -> None:
        self._process: subprocess.Popen[bytes] | None = None

    def served(self) -> tuple[Endpoint, ...]:
        return SERVED

    def start(self, ctx: ServiceContext) -> None:
        out = ctx.out
        (out / "site").mkdir(parents=True, exist_ok=True)
        (out / "tmp").mkdir(exist_ok=True)
        (out / "site" / "index.html").write_text(INDEX.format(instance=ctx.instance))
        if any(e.protocol == "https" for e in ctx.served):
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-days",
                    "30",
                    "-subj",
                    f"/CN={ctx.instance.replace('/', '-')}",
                    "-keyout",
                    str(out / "key.pem"),
                    "-out",
                    str(out / "cert.pem"),
                ],
                check=True,
                capture_output=True,
            )
        (out / "nginx.conf").write_text(config(out, ctx.instance, ctx.served))
        self._process = subprocess.Popen(
            [
                "nginx",
                "-c",
                str(out / "nginx.conf"),
                "-p",
                str(out),
                "-e",
                str(out / "error.log"),
                "-g",
                "daemon off;",
            ],
        )

    def healthcheck(self, ctx: ServiceContext) -> bool:
        if self._process is None or self._process.poll() is not None:
            return False
        for endpoint in ctx.served:
            try:
                with socket.create_connection(("127.0.0.1", endpoint.port), timeout=1.0):
                    pass
            except OSError:
                return False
        return True

    def stop(self, ctx: ServiceContext) -> None:
        if self._process is None:
            return
        self._process.terminate()
        try:
            self._process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self._process.kill()
            self._process.wait()
        self._process = None
