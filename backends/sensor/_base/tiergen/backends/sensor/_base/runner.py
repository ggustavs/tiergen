"""Running a sensor image over a pcap through the daemon.

The container sees the pcap at ``/pcap/<file>``, the configuration at ``/config/<name>`` (a
file or a directory, as the scenario's resource is) and writes under ``/out``. It runs
under the daemon's user-namespace remap like any other container, so the remapped root is
let into those three paths with ACLs first: dumpcap writes the pcap readable by its owner
only, and the output directory is the user's.
"""

from collections.abc import Callable, Sequence
from pathlib import Path

from tiergen.backends.infra.docker._client import Client, setfacl
from tiergen.interfaces import BackendError

PCAP_MOUNT = "/pcap"
CONFIG_MOUNT = "/config"
OUT_MOUNT = "/out"


class SensorError(RuntimeError):
    """A sensor did not produce what its adapter reads; the message names the file."""


def run_image(
    client: Client,
    image: str,
    command: Sequence[str],
    pcap: Path,
    config: Path,
    out: Path,
    acl: Callable[[Sequence[str]], None] = setfacl,
) -> str:
    """Pull ``image`` if the daemon lacks it, run ``command`` in it over ``pcap`` with
    ``config`` into ``out``, and return the image's digest, which is what identifies the
    instrument that ran."""
    ids = client.userns()
    if ids is None:
        raise BackendError("the daemon runs without a user-namespace remap (design decision 4.19)")
    uid = ids[0]
    out.mkdir(parents=True, exist_ok=True)
    acl(["-m", f"u:{uid}:rwx", str(out)])
    acl(["-m", f"u:{uid}:r", str(pcap)])
    acl(["-m", f"u:{uid}:rx", str(pcap.parent)])
    acl(["-R", "-m", f"u:{uid}:rX", str(config)])
    client.ensure_image(image)
    client.run_helper(
        image,
        command,
        "none",
        (),
        [
            (pcap.resolve(), f"{PCAP_MOUNT}/{pcap.name}", True),
            (config.resolve(), f"{CONFIG_MOUNT}/{config.name}", True),
            (out.resolve(), OUT_MOUNT, False),
        ],
        userns_host=False,
    )
    return client.image_digest(image)
