"""``scan.tcp_syn``, ``scan.tcp_connect`` and ``scan.udp`` as one nmap run over the targets.

The scan is nmap's own in every respect that reaches the wire, host discovery included;
only name resolution is off (``-n``), since a lab has no resolver and the signature's shape
has no lookups. A non-zero exit, such as a SYN scan without ``net_raw``, is a failed
outcome, not an exception.
"""

import subprocess

from tiergen.core.codec import JsonValue
from tiergen.core.records import Outcome
from tiergen.impls._base import Context

FLAGS = {"scan.tcp_syn": "-sS", "scan.tcp_connect": "-sT", "scan.udp": "-sU"}
TIMEOUT = 600.0


def command(signature: str, ports: str, addresses: tuple[str, ...]) -> list[str]:
    return ["nmap", FLAGS[signature], "-n", "-p", ports, "--host-timeout", "300s", *addresses]


class NmapRuntime:
    def run(self, ctx: Context, signature: str, **params: JsonValue) -> Outcome:
        if signature not in FLAGS or not ctx.targets:
            return "failed"
        addresses = tuple(peer.address for peer in ctx.targets)
        try:
            result = subprocess.run(
                command(signature, str(params.get("ports", "1-1024")), addresses),
                capture_output=True,
                timeout=TIMEOUT,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return "failed"
        return "succeeded" if result.returncode == 0 else "failed"
