"""Build the guest templates the libvirt backend clones from.

    uv run python scripts/templates/build.py linux \\
        --image ~/.local/share/tiergen/media/debian-13-genericcloud-amd64.qcow2

A template is a volume in the ``tiergen`` pool, ``template-<name>.qcow2``, provisioned once
with internet through libvirt's ``default`` NAT network and then never booted again: every
run clones it. The Linux template is a Debian cloud image provisioned by cloud-init
(``linux/user-data`` and ``linux/network-config``); once the guest agent is up the build
waits for cloud-init through it, checks what was installed, reads cloud-init's log back
when something failed, removes what must not survive into a run (the build's network
configuration, cloud-init itself), and shuts the guest down. Windows templates follow
(``scripts/templates/README.md`` has the media).
"""

import argparse
import contextlib
import sys
import tempfile
import time
from pathlib import Path

from tiergen.backends.infra.libvirt._client import LibvirtClient
from tiergen.backends.infra.libvirt.backend import DISK_GIB, POOL, POOL_PATH, domain_xml
from tiergen.backends.infra.libvirt.iso import write_iso
from tiergen.interfaces import BackendError

HERE = Path(__file__).parent
NAT = "default"
AGENT_TIMEOUT_S = 900.0
PROVISION_TIMEOUT_S = 1800.0
REQUIRED = ("qemu-guest-agent", "python3", "python3-httpx", "nmap", "nginx", "ethtool", "libbpf1")
CLEANUP = (
    "rm -f /etc/netplan/50-cloud-init.yaml /run/systemd/network/10-netplan-* && "
    "touch /etc/cloud/cloud-init.disabled && cloud-init clean --logs && "
    "rm -rf /var/lib/cloud/instances /var/lib/cloud/instance && sync"
)
"""What a run must not inherit: a network configuration pinned to the build's MAC (a run's
bootstrap sets addresses itself), and a cloud-init that would look for a datasource."""


def _seed(client: LibvirtClient, domain: str, name: str) -> str:
    seed = f"{domain}-seed.iso"
    with tempfile.TemporaryDirectory(prefix="tiergen-seed-") as tmp:
        stage = Path(tmp) / "seed"
        stage.mkdir()
        for part in ("user-data", "network-config"):
            (stage / part).write_text((HERE / "linux" / part).read_text("utf-8"), "utf-8")
        (stage / "meta-data").write_text(
            f"instance-id: {domain}\nlocal-hostname: {name}\n", "utf-8"
        )
        iso = Path(tmp) / "seed.iso"
        write_iso(iso, stage, label="CIDATA")
        client.upload(POOL, seed, iso, "raw")
    return seed


def _fail(client: LibvirtClient, domain: str, seed: str, template: str, why: str) -> None:
    detail = ""
    try:
        done = client.guest_exec(
            domain,
            "/bin/sh",
            [
                "-c",
                "cloud-init status --long;"
                " grep -E 'WARNING|ERROR' /var/log/cloud-init.log | tail -20;"
                " tail -40 /var/log/cloud-init-output.log",
            ],
        )
        detail = "\n" + done.out
    except BackendError:
        pass
    with contextlib.suppress(BackendError):
        client.destroy_domain(domain)
    client.delete_volume(POOL, seed)
    client.delete_volume(POOL, template)
    raise BackendError(f"{domain}: {why}{detail}")


def linux(client: LibvirtClient, image: Path, name: str) -> None:
    base = f"base-{image.stem}.qcow2"
    template = f"template-{name}.qcow2"
    have = set(client.volumes(POOL))
    if template in have:
        print(f"{template} exists in pool {POOL}; delete it first to rebuild")
        return
    if base not in have:
        print(f"uploading {image} as {base}")
        client.upload(POOL, base, image, "qcow2")
    client.clone(POOL, template, base, DISK_GIB["linux"])
    domain = f"tiergen-build-{name}"
    seed = _seed(client, domain, name)
    client.ensure_network(NAT)
    xml = domain_xml(domain, "tiergen template build", "linux", template, seed, (), nat=NAT)
    client.create_domain(xml)
    began = time.monotonic()
    print(f"{domain} booting; cloud-init installs the packages, then the guest agent answers")
    if not client.agent_ready(domain, AGENT_TIMEOUT_S):
        _fail(client, domain, seed, template, f"no guest agent within {AGENT_TIMEOUT_S:g} s")
    print(f"guest agent up after {time.monotonic() - began:.0f} s; waiting for cloud-init")
    done = client.guest_exec(
        domain, "/usr/bin/cloud-init", ["status", "--wait"], timeout_s=PROVISION_TIMEOUT_S
    )
    if done.exit_code != 0:
        _fail(client, domain, seed, template, f"cloud-init ended with {done.exit_code}: {done.out}")
    check = client.guest_exec(
        domain,
        "/bin/sh",
        ["-c", "dpkg-query -W -f '${Package} ${Status}\\n' " + " ".join(REQUIRED)],
    )
    missing = [p for p in REQUIRED if f"{p} install ok installed" not in check.out]
    if missing:
        _fail(client, domain, seed, template, f"not installed: {', '.join(missing)}")
    cleaned = client.guest_exec(domain, "/bin/sh", ["-c", CLEANUP])
    if cleaned.exit_code != 0:
        _fail(client, domain, seed, template, f"cleanup failed: {cleaned.err}")
    client.guest_exec(
        domain, "/bin/sh", ["-c", "nohup sh -c 'sleep 1; poweroff' >/dev/null 2>&1 &"]
    )
    while domain in client.domains():
        if time.monotonic() - began > PROVISION_TIMEOUT_S:
            _fail(client, domain, seed, template, "did not power off")
        time.sleep(2)
    client.delete_volume(POOL, seed)
    print(f"{template} ready in pool {POOL} after {time.monotonic() - began:.0f} s")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the guest templates for the libvirt backend."
    )
    sub = parser.add_subparsers(dest="kind", required=True)
    lin = sub.add_parser("linux", help="the Linux agent template from a Debian cloud image")
    lin.add_argument("--image", type=Path, required=True, help="a genericcloud qcow2")
    lin.add_argument("--name", default="linux-agent")
    parser.add_argument("--pool-path", default=POOL_PATH)
    args = parser.parse_args(argv)
    try:
        client = LibvirtClient()
        client.ensure_pool(POOL, args.pool_path)
        if args.kind == "linux":
            linux(client, args.image, args.name)
    except BackendError as err:
        print(f"build: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
