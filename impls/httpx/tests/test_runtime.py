"""The httpx runtime against a server in this process: outcomes, never exceptions."""

import threading
from collections.abc import Iterator
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from random import Random

import pytest

from tiergen.core.ir import Endpoint
from tiergen.core.records import LabelKey, Peer
from tiergen.impls.httpx.runtime import HttpxRuntime


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        status = 200 if self.path in ("/", "/news") else 404
        self.send_response(status)
        self.end_headers()
        self.wfile.write(b"ok" if status == 200 else b"no")

    def do_POST(self) -> None:
        body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        self.send_response(200)
        self.end_headers()
        self.wfile.write(str(len(body)).encode())

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture(scope="module")
def server() -> Iterator[Peer]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_address[1]
    yield Peer("lab/web[0]", "127.0.0.1", (Endpoint("http", port, "tcp"),))
    httpd.shutdown()


@dataclass(frozen=True, slots=True)
class Ctx:
    label: LabelKey
    invocation: str
    targets: tuple[Peer, ...]
    ties: dict[str, tuple[Peer, ...]]
    variant: str | None
    rng: Random


def ctx(*targets: Peer) -> Ctx:
    label = LabelKey(
        "s",
        "lab/ws[0]",
        "browse",
        "web_get",
        "lab/ws[0]/browse#1",
        "http.httpx",
        None,
        tuple(t.instance for t in targets),
    )
    return Ctx(label, label.invocation, targets, {"web": targets}, None, Random(1))


def test_get_and_post_succeed_and_an_error_status_fails(server: Peer) -> None:
    runtime = HttpxRuntime()
    assert runtime.run(ctx(server), "http.get", path="/") == "succeeded"
    assert runtime.run(ctx(server), "http.get", path="/news") == "succeeded"
    assert runtime.run(ctx(server), "http.get", path="/missing") == "failed"
    assert runtime.run(ctx(server), "http.post_form", path="/", body_bytes=300) == "succeeded"


def test_nothing_listening_or_nothing_served_is_a_failed_outcome(server: Peer) -> None:
    runtime = HttpxRuntime()
    dark = Peer("lab/web[1]", "127.0.0.1", (Endpoint("http", 1, "tcp"),))
    assert runtime.run(ctx(dark), "http.get", path="/") == "failed"
    assert runtime.run(ctx(server, dark), "http.get", path="/") == "failed"
    smb_only = Peer("lab/fs[0]", "127.0.0.1", (Endpoint("smb", 445, "tcp"),))
    assert runtime.run(ctx(smb_only), "http.get", path="/") == "failed"
    assert runtime.run(ctx(server), "http.browse", start_path="/") == "failed"
