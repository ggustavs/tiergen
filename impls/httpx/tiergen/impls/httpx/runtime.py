"""``http.get`` and ``http.post_form`` with httpx: one client per invocation.

Each invocation opens its own client and closes it, so a connection never outlives the
invocation that opened it and the signature's shape, one connection, holds. The user agent
is httpx's own, which is what the manifest's fingerprint says. A served ``https`` endpoint
is used without verifying its certificate: the lab has no CA yet.
"""

import httpx
from tiergen.core.codec import JsonValue
from tiergen.core.records import Outcome, Peer
from tiergen.impls._base import Context

TIMEOUT = 10.0
SCHEMES = ("http", "https")


def _url(peer: Peer, path: str) -> str | None:
    """The first served endpoint the signature fits, as a URL; None if the peer serves none."""
    for endpoint in peer.served:
        if endpoint.protocol in SCHEMES:
            return f"{endpoint.protocol}://{peer.address}:{endpoint.port}{path}"
    return None


class HttpxRuntime:
    def run(self, ctx: Context, signature: str, **params: JsonValue) -> Outcome:
        path = str(params.get("path", "/"))
        outcome: Outcome = "succeeded"
        for peer in ctx.targets:
            url = _url(peer, path)
            if url is None:
                return "failed"
            try:
                with httpx.Client(timeout=TIMEOUT, verify=False) as client:
                    if signature == "http.get":
                        response = client.get(url)
                    elif signature == "http.post_form":
                        size = int(str(params.get("body_bytes", 0)))
                        response = client.post(url, data={"payload": "x" * max(size - 8, 0)})
                    else:
                        return "failed"
            except httpx.HTTPError:
                return "failed"
            if response.is_error:
                outcome = "failed"
        return outcome
