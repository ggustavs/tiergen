"""Build the guest templates the libvirt backend clones from.

    uv run python scripts/templates/build.py linux \\
        --image ~/.local/share/tiergen/media/debian-13-genericcloud-amd64.qcow2
    uv run python scripts/templates/build.py windows \\
        --iso ~/.local/share/tiergen/media/win10-ltsc2021-eval.iso

A template is a volume in the ``tiergen`` pool, ``template-<name>.qcow2``, provisioned once
on libvirt's ``default`` NAT network and then never booted again: every run clones it. The
Linux template is a Debian cloud image provisioned by cloud-init (``linux/user-data`` and
``linux/network-config``); once the guest agent is up the build waits for cloud-init
through it, checks what was installed, reads cloud-init's log back when something failed,
removes what must not survive into a run (the build's network configuration, cloud-init
itself), and shuts the guest down. A Windows template is an unattended install onto an
empty disk (``windows/autounattend.xml`` on a build CD, the virtio drivers from the
virtio-win CD); at first logon ``windows/setup.ps1`` installs the guest agent, and the build
then runs ``windows/provision.ps1`` through it: Python, the agent's third-party wheels and
Sysmon, all from the build CD, so the guest needs no network. ``scripts/templates/README.md``
has the media.
"""

import argparse
import contextlib
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from tiergen.backends.infra._base.members import MEMBERS, workspace_root
from tiergen.backends.infra.libvirt._client import Exec, LibvirtClient
from tiergen.backends.infra.libvirt.backend import DISK_GIB, POOL, POOL_PATH, domain_xml
from tiergen.backends.infra.libvirt.iso import write_iso
from tiergen.interfaces import BackendError

HERE = Path(__file__).parent
MEDIA = Path.home() / ".local" / "share" / "tiergen" / "media"
NAT = "default"
AGENT_TIMEOUT_S = 900.0
PROVISION_TIMEOUT_S = 1800.0
INSTALL_TIMEOUT_S = 5400.0
"""From the domain's start to the guest agent's first answer: Setup, its reboots, the first
logon and the guest agent's install."""
BOOT_KEYS_S = 60.0
"""How long to keep pressing Enter so the install CD boots: its boot loader waits a few
seconds for a key and otherwise falls through to the empty disk, and the Server ISO then
shows a boot menu that waits for Enter with no timeout."""
KEY_ENTER = 28
BUILD_LABEL = "TGBUILD"
PASSWORD = "Tiergen-2026!"
"""The build account's password, also the built-in Administrator's. A template never leaves
the host, and every run is on isolated bridges."""
POWERSHELL = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
CMD = "C:\\Windows\\System32\\cmd.exe"
SHUTDOWN = "C:\\Windows\\System32\\shutdown.exe"
GUEST_BUILD = "C:\\tiergen-build"
DOMAIN = "hq.tiergen.test"
"""The forest a DC template serves: under ``.test``, which never resolves outside."""
NETBIOS = "HQ"
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
    xml = domain_xml(domain, "tiergen template build", "linux", template, (seed,), (), nat=NAT)
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


def _media_volume(client: LibvirtClient, path: Path) -> str:
    """An installation medium as a raw volume in the pool, uploaded once and kept for the
    next build."""
    name = f"media-{path.name}"
    if name not in client.volumes(POOL):
        print(f"uploading {path} as {name}")
        client.upload(POOL, name, path, "raw")
    return name


def windows_wheels(into: Path) -> None:
    """The agent members' third-party dependencies, pinned by ``uv.lock``, as wheels for
    CPython 3.12 on Windows, with the ``requirements.txt`` that installs them."""
    root = workspace_root()
    pins: set[str] = set()
    for dist, _ in MEMBERS:
        exported = subprocess.run(
            [
                "uv", "export", "--frozen", "--package", dist, "--no-emit-workspace",
                "--no-hashes", "--no-header", "--no-annotate", "--format", "requirements-txt",
            ],
            cwd=root, capture_output=True, text=True,
        )  # fmt: skip
        if exported.returncode != 0:
            raise BackendError(f"cannot export the pins of {dist}: {exported.stderr.strip()}")
        pins.update(line for line in exported.stdout.splitlines() if line.strip())
    requirements = into / "requirements.txt"
    requirements.write_text("".join(f"{p}\n" for p in sorted(pins)), "utf-8")
    downloaded = subprocess.run(
        [
            "uv", "run", "--no-project", "--with", "pip", "python", "-m", "pip", "download",
            "--quiet", "--only-binary=:all:", "--platform", "win_amd64", "--python-version",
            "3.12", "--implementation", "cp", "--abi", "cp312", "-r", str(requirements),
            "-d", str(into),
        ],
        cwd=root, capture_output=True, text=True,
    )  # fmt: skip
    if downloaded.returncode != 0:
        raise BackendError(f"cannot download the Windows wheels: {downloaded.stderr.strip()}")


def answer_file(index: int, drivers: str, computer: str) -> str:
    """``windows/autounattend.xml`` with its fields filled."""
    text = (HERE / "windows" / "autounattend.xml").read_text("utf-8")
    for field, value in (
        ("@INDEX@", str(index)),
        ("@DRIVERS@", drivers),
        ("@COMPUTER@", computer),
        ("@PASSWORD@", PASSWORD),
    ):
        text = text.replace(field, value)
    return text


@dataclass(frozen=True, slots=True)
class Forest:
    """What a DC build promotes its guest to: the address its NIC keeps, the forest's DNS
    and NetBIOS names. ``hq_lan`` pins its DC at 10.10.0.10."""

    address: str
    prefix: int
    domain: str
    netbios: str


def _fail_windows(client: LibvirtClient, domain: str, volumes: Sequence[str], why: str) -> None:
    detail = ""
    for log in ("setup.log", "provision.log", "promote.log", "join.log"):
        with contextlib.suppress(BackendError):
            text = client.guest_read(domain, f"{GUEST_BUILD}\\{log}").decode("utf-8", "replace")
            detail += f"\n--- {log}\n" + "\n".join(text.splitlines()[-40:])
    with contextlib.suppress(BackendError):
        client.destroy_domain(domain)
    for volume in volumes:
        with contextlib.suppress(BackendError):
            client.delete_volume(POOL, volume)
    raise BackendError(f"{domain}: {why}{detail}")


def run_script(
    client: LibvirtClient,
    domain: str,
    script: str,
    args: Sequence[str] = (),
    timeout_s: float = PROVISION_TIMEOUT_S,
) -> Exec:
    """``windows/<script>`` written into the guest's build directory through the agent and
    run there by PowerShell as SYSTEM with ``args``."""
    target = f"{GUEST_BUILD}\\{script}"
    client.guest_exec(domain, CMD, ["/c", "mkdir", GUEST_BUILD])
    client.guest_write(domain, target, (HERE / "windows" / script).read_bytes())
    return client.guest_exec(
        domain,
        POWERSHELL,
        ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", target, *args],
        timeout_s=timeout_s,
    )


def reboot(client: LibvirtClient, domain: str, timeout_s: float = 900.0) -> bool:
    """Restart the guest and wait until its agent answers again."""
    client.guest_exec(domain, SHUTDOWN, ["/r", "/t", "3", "/f"])
    deadline = time.monotonic() + timeout_s
    while client.agent_ready(domain, 1.0):
        if time.monotonic() > deadline:
            return False
        time.sleep(1.0)
    return client.agent_ready(domain, max(deadline - time.monotonic(), 1.0))


def power_off(client: LibvirtClient, domain: str, timeout_s: float = 600.0) -> bool:
    client.guest_exec(domain, SHUTDOWN, ["/s", "/t", "3", "/f"])
    deadline = time.monotonic() + timeout_s
    while domain in client.domains():
        if time.monotonic() > deadline:
            return False
        time.sleep(2)
    return True


def windows(
    client: LibvirtClient,
    iso: Path,
    name: str,
    index: int,
    drivers: str,
    computer: str,
    virtio: Path,
    python: Path,
    sysmon: Path,
    forest: Forest | None = None,
) -> None:
    """A Windows template by unattended install and provisioning; with ``forest``, a DC:
    the guest is promoted to a new forest's first domain controller before it shuts down."""
    template = f"template-{name}.qcow2"
    if template in client.volumes(POOL):
        print(f"{template} exists in pool {POOL}; delete it first to rebuild")
        return
    for medium in (iso, virtio, python, sysmon):
        if not medium.is_file():
            raise BackendError(f"{medium} is missing; scripts/templates/README.md says where from")
    install = _media_volume(client, iso)
    virtio_cd = _media_volume(client, virtio)
    domain = f"tiergen-build-{name}"
    build = f"{domain}-build.iso"
    with tempfile.TemporaryDirectory(prefix="tiergen-build-") as tmp:
        stage = Path(tmp) / "stage"
        stage.mkdir()
        (stage / "autounattend.xml").write_text(answer_file(index, drivers, computer), "utf-8")
        for part in ("setup.ps1", "provision.ps1", "sysmon.xml"):
            shutil.copyfile(HERE / "windows" / part, stage / part)
        shutil.copyfile(python, stage / "python-installer.exe")
        shutil.copyfile(sysmon, stage / "Sysmon.zip")
        (stage / "wheels").mkdir()
        windows_wheels(stage / "wheels")
        out = Path(tmp) / "build.iso"
        write_iso(out, stage, label=BUILD_LABEL)
        client.upload(POOL, build, out, "raw")
    client.create_volume(POOL, template, DISK_GIB["windows"])
    client.ensure_network(NAT)
    xml = domain_xml(
        domain,
        "tiergen template build",
        "windows",
        template,
        (install, virtio_cd, build),
        (),
        nat=NAT,
        display=True,
    )
    client.create_domain(xml)
    began = time.monotonic()
    volumes = (build, template)
    while time.monotonic() - began < BOOT_KEYS_S:
        client.send_key(domain, KEY_ENTER)
        time.sleep(0.5)
    print(f"{domain} installing (VNC on 127.0.0.1); the guest agent answers after first logon")
    if not client.agent_ready(domain, INSTALL_TIMEOUT_S):
        _fail_windows(client, domain, volumes, f"no guest agent within {INSTALL_TIMEOUT_S:g} s")
    print(f"guest agent up after {time.monotonic() - began:.0f} s; provisioning")
    done = client.guest_exec(
        domain,
        POWERSHELL,
        [
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"& ((Get-Volume -FileSystemLabel {BUILD_LABEL}).DriveLetter + ':\\provision.ps1')",
        ],
        timeout_s=PROVISION_TIMEOUT_S,
    )
    if done.exit_code != 0:
        _fail_windows(
            client, domain, volumes, f"provisioning ended with {done.exit_code}: {done.err}"
        )
    print(done.out.strip())
    if forest is not None:
        done = run_script(
            client,
            domain,
            "promote.ps1",
            [
                "-Address", forest.address, "-Prefix", str(forest.prefix),
                "-Domain", forest.domain, "-NetBios", forest.netbios, "-Password", PASSWORD,
            ],
        )  # fmt: skip
        if done.exit_code != 0:
            _fail_windows(client, domain, volumes, f"promotion ended with {done.exit_code}")
        print(done.out.strip())
        if not reboot(client, domain):
            _fail_windows(client, domain, volumes, "no guest agent after the promotion's reboot")
        done = run_script(client, domain, "dc-ready.ps1", ["-Domain", forest.domain])
        if done.exit_code != 0:
            _fail_windows(client, domain, volumes, f"the DC is not ready: {done.err.strip()}")
        print(f"{forest.domain} served by {computer}")
    if not power_off(client, domain):
        _fail_windows(client, domain, volumes, "did not power off")
    client.delete_volume(POOL, build)
    print(f"{template} ready in pool {POOL} after {time.monotonic() - began:.0f} s")


def join(
    client: LibvirtClient,
    dc: str,
    workstation: str,
    name: str,
    forest: Forest,
    address: str,
) -> None:
    """The workstation template joined to the DC template's forest, kept as a pair:
    ``template-<name>-dc`` and ``template-<name>-ws``, overlays on the two templates, both
    disks as they were when the join was done. A run clones the pair together; the
    workstation's machine account lives in the DC's directory, so neither works without
    the other."""
    pair = {"dc": f"template-{name}-dc.qcow2", "ws": f"template-{name}-ws.qcow2"}
    have = set(client.volumes(POOL))
    if set(pair.values()) & have:
        print(f"{' or '.join(pair.values())} exists in pool {POOL}; delete both to rebuild")
        return
    bases = {"dc": f"template-{dc}.qcow2", "ws": f"template-{workstation}.qcow2"}
    for base in bases.values():
        if base not in have:
            raise BackendError(f"{base} is missing; build it first")
    network, bridge = f"tiergen-build-{name}", f"tg-build-{name}"[:15]
    domains = {role: f"tiergen-build-{name}-{role}" for role in pair}
    for role, volume in pair.items():
        client.clone(POOL, volume, bases[role], DISK_GIB["windows"])
    client.create_network(network, bridge)
    began = time.monotonic()
    try:
        for i, (role, domain) in enumerate(domains.items()):
            mac = f"52:54:00:7e:00:{i + 1:02x}"
            client.create_domain(
                domain_xml(
                    domain, "tiergen template build", "windows", pair[role], (), [(bridge, mac)]
                )
            )
        for domain in domains.values():
            if not client.agent_ready(domain, 600):
                raise BackendError(f"{domain}: no guest agent")
        done = run_script(
            client,
            domains["dc"],
            "dc-ready.ps1",
            ["-Domain", forest.domain, "-Address", forest.address],
        )
        if done.exit_code != 0:
            raise BackendError(f"the DC is not ready: {done.err.strip()}")
        done = run_script(
            client,
            domains["ws"],
            "join.ps1",
            [
                "-Address", address.split("/")[0], "-Prefix", address.split("/")[1],
                "-Dns", forest.address, "-Domain", forest.domain,
                "-User", "Administrator", "-Password", PASSWORD,
            ],
        )  # fmt: skip
        if done.exit_code != 0:
            log = client.guest_read(domains["ws"], f"{GUEST_BUILD}\\join.log")
            raise BackendError(f"the join failed:\n{log.decode('utf-8', 'replace')[-3000:]}")
        print(done.out.strip())
        if not reboot(client, domains["ws"]):
            raise BackendError("no guest agent after the join's reboot")
        done = run_script(client, domains["ws"], "joined.ps1", ["-Domain", forest.domain])
        if done.exit_code != 0:
            raise BackendError(f"the workstation is not in {forest.domain}: {done.err.strip()}")
        print(done.out.strip())
        for role in ("ws", "dc"):
            if not power_off(client, domains[role]):
                raise BackendError(f"{domains[role]} did not power off")
    except BackendError:
        for domain in domains.values():
            with contextlib.suppress(BackendError):
                client.destroy_domain(domain)
        for volume in pair.values():
            with contextlib.suppress(BackendError):
                client.delete_volume(POOL, volume)
        raise
    finally:
        with contextlib.suppress(BackendError):
            client.destroy_network(network)
    print(f"{pair['dc']} and {pair['ws']} ready after {time.monotonic() - began:.0f} s")


def _forest(text: str, domain: str, netbios: str) -> Forest:
    address, _, prefix = text.partition("/")
    return Forest(address, int(prefix or 24), domain, netbios)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the guest templates for the libvirt backend."
    )
    sub = parser.add_subparsers(dest="kind", required=True)
    lin = sub.add_parser("linux", help="the Linux agent template from a Debian cloud image")
    lin.add_argument("--image", type=Path, required=True, help="a genericcloud qcow2")
    lin.add_argument("--name", default="linux-agent")
    for kind, help_, name, index, drivers, computer in (
        ("windows", "the Windows workstation", "windows-agent", 1, "w10", "TIERGEN-WS"),
        ("dc", "a Windows domain controller", "win2022-dc", 1, "2k22", "TIERGEN-DC"),
    ):
        win = sub.add_parser(kind, help=f"{help_} template by unattended install")
        win.add_argument("--iso", type=Path, required=True, help="the Windows installation ISO")
        win.add_argument("--name", default=name)
        win.add_argument("--index", type=int, default=index, help="the image in install.wim")
        win.add_argument("--drivers", default=drivers, help="virtio-win's directory for the OS")
        win.add_argument("--computer", default=computer, help="the computer name")
        win.add_argument(
            "--virtio", type=Path, default=MEDIA / "virtio-win" / "virtio-win-0.1.302.iso"
        )
        win.add_argument(
            "--python", type=Path, default=MEDIA / "windows" / "python-3.12.10-amd64.exe"
        )
        win.add_argument("--sysmon", type=Path, default=MEDIA / "windows" / "Sysmon.zip")
        if kind == "dc":
            win.add_argument("--address", default="10.10.0.10/24", help="the DC's, kept")
            win.add_argument("--domain", default=DOMAIN)
            win.add_argument("--netbios", default=NETBIOS)
    pair = sub.add_parser("join", help="the workstation joined to the DC, kept as a pair")
    pair.add_argument("--dc", default="win2022-dc")
    pair.add_argument("--workstation", default="windows-agent")
    pair.add_argument("--name", default="hq")
    pair.add_argument("--dc-address", default="10.10.0.10/24")
    pair.add_argument("--address", default="10.10.0.21/24", help="the workstation's, for the join")
    pair.add_argument("--domain", default=DOMAIN)
    pair.add_argument("--netbios", default=NETBIOS)
    parser.add_argument("--pool-path", default=POOL_PATH)
    args = parser.parse_args(argv)
    try:
        client = LibvirtClient()
        client.ensure_pool(POOL, args.pool_path)
        if args.kind == "linux":
            linux(client, args.image, args.name)
        elif args.kind == "join":
            forest = _forest(args.dc_address, args.domain, args.netbios)
            join(client, args.dc, args.workstation, args.name, forest, args.address)
        else:
            windows(
                client,
                args.iso,
                args.name,
                args.index,
                args.drivers,
                args.computer,
                args.virtio,
                args.python,
                args.sysmon,
                _forest(args.address, args.domain, args.netbios) if args.kind == "dc" else None,
            )
    except BackendError as err:
        print(f"build: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
