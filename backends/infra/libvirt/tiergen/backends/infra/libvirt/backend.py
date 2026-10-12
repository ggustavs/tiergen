"""The libvirt backend: a run manifest's guests under KVM, on the run's bridges.

A host is a transient domain cloned from a template volume in the ``tiergen`` pool, UEFI
and virtio throughout, with one tap per attachment on the segment's Linux bridge (the
bridge the Docker backend made, or an isolated libvirt network made here when no
container shares the segment) and the planned MAC, so the capture sees the guest as the
plan says. The guest gets the run on a CD-ROM (``iso.py``) and is driven through the QEMU
guest agent: the bootstrap on the ISO sets addresses by MAC, installs the agent's wheels
and starts the agent held at its gate; ``start`` writes the gate; ``collect`` pulls what
the agent wrote; the guest's clock against the host's at ``up`` is its offset. Every
domain carries the run in its description, so ``down`` finds everything without state.
"""

import hashlib
import io
import ipaddress
import json
import subprocess
import tarfile
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from tiergen.backends.infra._base.manifest import AGENT_IMAGE
from tiergen.backends.infra._base.members import AGENT_MEMBERS, MEMBERS, workspace_root
from tiergen.backends.infra.libvirt._client import Client, LibvirtClient
from tiergen.backends.infra.libvirt.iso import stage_run, write_iso
from tiergen.core.program import flat_id
from tiergen.interfaces import BackendError, HostSpec, HostState, RunManifest, RunState

POOL = "tiergen"
POOL_PATH = "/var/lib/libvirt/images/tiergen"
RUN_LABEL = "tiergen.run"
INSTANCE_LABEL = "tiergen.instance"
MEMORY_MIB = {"linux": 2048, "windows": 4096}
DISK_GIB = {"linux": 20, "windows": 64}
VCPUS = 2
GUEST_OUT = "/tiergen/out"
GUEST_MOUNT = "/mnt/tiergen"
AGENT_TIMEOUT_S = 180.0
BOOTSTRAP = (
    f"mkdir -p {GUEST_MOUNT} && (mountpoint -q {GUEST_MOUNT} || mount -o ro LABEL=TIERGEN "
    f"{GUEST_MOUNT}) && sh {GUEST_MOUNT}/bootstrap.sh"
)
QUIESCE = (
    "for d in /sys/class/net/e*; do ethtool -K $(basename $d) tso off gso off tx off "
    ">/dev/null 2>&1 || true; done"
)

Wheels = Callable[[Path], None]
IsoWriter = Callable[[Path, Path], None]


def domain_name(run: str, instance: str) -> str:
    return f"tiergen-{run}-{flat_id(instance)}"


def network_name(run: str, segment: str) -> str:
    return f"tiergen-{run}-{segment}"


def template_volume(image: str, platform: str) -> str:
    """The pool volume a host's image names: the platform's agent template for a default
    host, else the template the binding named."""
    if image == AGENT_IMAGE.get(platform):
        return f"template-{platform}-agent.qcow2"
    return f"template-{image}.qcow2"


def derived_mac(run: str, instance: str, network: str) -> str:
    """A locally administered MAC for an attachment the plan gave none: QEMU's prefix and
    three bytes of a hash, stable across runs of the same scenario."""
    digest = hashlib.blake2b(f"{run}|{instance}|{network}".encode(), digest_size=3).digest()
    return "52:54:00:" + ":".join(f"{b:02x}" for b in digest)


def build_wheels(into: Path) -> None:
    """Every member an agent imports, as wheels under ``into``, built from the workspace."""
    root = workspace_root()
    for dist, _ in (*MEMBERS, *AGENT_MEMBERS.values()):
        done = subprocess.run(
            ["uv", "build", "--wheel", "--package", dist, "--out-dir", str(into), "--quiet"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if done.returncode != 0:
            raise BackendError(f"cannot build the wheel of {dist}: {done.stderr.strip()}")


@dataclass(frozen=True, slots=True)
class GuestAttachment:
    network: str
    address: str
    prefix: int
    mac: str


@dataclass(frozen=True, slots=True)
class GuestHost:
    """``host.json`` on the run ISO: what the bootstrap needs to know about this host."""

    instance: str
    hostname: str
    program: str
    attachments: tuple[GuestAttachment, ...]
    routes: tuple[tuple[str, str], ...]
    forwards: bool
    gate: str | None
    out: str

    def json(self) -> str:
        return json.dumps(
            {
                "instance": self.instance,
                "hostname": self.hostname,
                "program": self.program,
                "attachments": [
                    {"network": a.network, "address": a.address, "prefix": a.prefix, "mac": a.mac}
                    for a in self.attachments
                ],
                "routes": [{"cidr": c, "via": v} for c, v in self.routes],
                "forwards": self.forwards,
                "gate": self.gate,
                "out": self.out,
            },
            indent=2,
        )


def domain_xml(
    name: str,
    description: str,
    platform: str,
    disk: str,
    isos: Sequence[str],
    attachments: Sequence[tuple[str, str]],
    nat: str | None = None,
    display: bool = False,
) -> str:
    """A q35 UEFI guest with virtio devices: its clone as ``disk``, each of ``isos`` as a
    SATA CD-ROM in order (a run has one, the run ISO), one virtio NIC per (bridge, mac), and
    the guest agent channel. The disk boots first and the first CD-ROM after it, so an
    empty disk installs from that CD and the next boot is the installed system. With
    ``nat``, a libvirt network name, one NIC on that network instead: how a template is
    built. With ``display``, a VNC display on the host's loopback, to watch a build. A
    Windows guest gets the Hyper-V enlightenments and clock it runs best with."""
    nics = (
        f"<interface type='network'><source network='{nat}'/><model type='virtio'/></interface>"
        if nat is not None
        else "".join(
            f"<interface type='bridge'><source bridge='{bridge}'/><mac address='{mac}'/>"
            "<model type='virtio'/></interface>"
            for bridge, mac in attachments
        )
    )
    after_disk = "<boot order='2'/>"
    cdroms = "".join(
        "<disk type='volume' device='cdrom'><driver name='qemu' type='raw'/>"
        f"<source pool='{POOL}' volume='{iso}'/><target dev='sd{'abcdef'[i]}' bus='sata'/>"
        f"<readonly/>{after_disk if i == 0 else ''}</disk>"
        for i, iso in enumerate(isos)
    )
    windows = platform == "windows"
    hyperv = (
        "<hyperv mode='custom'><relaxed state='on'/><vapic state='on'/>"
        "<spinlocks state='on' retries='8191'/><vpindex state='on'/><synic state='on'/>"
        "<stimer state='on'/></hyperv>"
        if windows
        else ""
    )
    clock = (
        "<clock offset='utc'><timer name='hypervclock' present='yes'/></clock>"
        if windows
        else "<clock offset='utc'/>"
    )
    # The video device gets a slot of its own: placed by libvirt it takes the first one and
    # moves every root port, so a guest built with a display would meet its NIC behind a
    # different bridge in a run, as a new adapter without the template's configuration.
    screen = (
        "<graphics type='vnc' autoport='yes' listen='127.0.0.1'/><video><model type='vga'/>"
        "<address type='pci' domain='0x0000' bus='0x00' slot='0x0a' function='0x0'/></video>"
        if display
        else ""
    )
    return (
        f"<domain type='kvm'><name>{name}</name><description>{description}</description>"
        f"<memory unit='MiB'>{MEMORY_MIB[platform]}</memory><vcpu>{VCPUS}</vcpu>"
        "<os firmware='efi'><type arch='x86_64' machine='q35'>hvm</type>"
        "<firmware><feature enabled='no' name='secure-boot'/></firmware></os>"
        f"<features><acpi/><apic/>{hyperv}</features><cpu mode='host-passthrough'/>"
        f"{clock}<on_poweroff>destroy</on_poweroff><on_crash>destroy</on_crash>"
        "<devices><emulator>/usr/bin/qemu-system-x86_64</emulator>"
        f"<disk type='volume' device='disk'><driver name='qemu' type='qcow2'/>"
        f"<source pool='{POOL}' volume='{disk}'/><target dev='vda' bus='virtio'/>"
        "<boot order='1'/></disk>"
        f"{cdroms}{nics}{screen}"
        "<channel type='unix'><target type='virtio' name='org.qemu.guest_agent.0'/></channel>"
        "<serial type='pty'/><console type='pty'/>"
        "<rng model='virtio'><backend model='random'>/dev/urandom</backend></rng>"
        "</devices></domain>"
    )


class LibvirtBackend:
    id = "libvirt"

    def __init__(
        self,
        client: Callable[[], Client] = LibvirtClient,
        wheels: Wheels = build_wheels,
        iso: IsoWriter = write_iso,
        pool_path: str = POOL_PATH,
        agent_timeout_s: float = AGENT_TIMEOUT_S,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._connect = client
        self._wheels = wheels
        self._iso = iso
        self._pool_path = pool_path
        self._agent_timeout_s = agent_timeout_s
        self._clock = clock

    def up(self, manifest: RunManifest, run_dir: Path, start: bool = True) -> RunState:
        client = self._connect()
        client.ensure_pool(POOL, self._pool_path)
        state = RunState(manifest.run, self.id)
        have = set(client.volumes(POOL))
        for host in manifest.hosts:
            template = template_volume(host.image, host.platform)
            if template not in have:
                raise BackendError(
                    f"template {template!r} is missing from pool {POOL!r}; build it with "
                    "scripts/templates/build.py"
                )
        prefixes = {n.name: ipaddress.ip_network(n.cidr).prefixlen for n in manifest.networks}
        bridges = {n.name: n.bridge for n in manifest.networks}
        try:
            for net in manifest.networks:
                if not client.bridge_exists(net.bridge):
                    client.create_network(network_name(manifest.run, net.name), net.bridge)
                state.bridges[net.name] = net.bridge
            with tempfile.TemporaryDirectory(prefix="tiergen-libvirt-") as tmp:
                wheels = Path(tmp) / "wheels"
                wheels.mkdir()
                if any(h.agent for h in manifest.hosts):
                    self._wheels(wheels)
                for host in manifest.hosts:
                    name = domain_name(manifest.run, host.instance)
                    attachments = [
                        GuestAttachment(
                            a.network,
                            a.address,
                            prefixes[a.network],
                            a.mac or derived_mac(manifest.run, host.instance, a.network),
                        )
                        for a in host.attachments
                    ]
                    iso = self._run_iso(Path(tmp), run_dir, wheels, host, attachments)
                    client.clone(
                        POOL,
                        f"{name}.qcow2",
                        template_volume(host.image, host.platform),
                        DISK_GIB[host.platform],
                    )
                    client.upload(POOL, f"{name}-run.iso", iso, "raw")
                    description = json.dumps(
                        {RUN_LABEL: manifest.run, INSTANCE_LABEL: host.instance}
                    )
                    uuid = client.create_domain(
                        domain_xml(
                            name,
                            description,
                            host.platform,
                            f"{name}.qcow2",
                            (f"{name}-run.iso",),
                            [(bridges[a.network], a.mac) for a in attachments],
                        )
                    )
                    state.hosts[host.instance] = HostState(name, uuid)
            for host in manifest.hosts:
                name = state.hosts[host.instance].name
                if not client.agent_ready(name, self._agent_timeout_s):
                    raise BackendError(
                        f"{name}: the guest agent did not answer within "
                        f"{self._agent_timeout_s:g} s; does the template run qemu-guest-agent?"
                    )
                before = self._clock()
                guest = client.guest_time(name)
                offset = (before + self._clock()) / 2 - guest
                state.hosts[host.instance] = HostState(name, state.hosts[host.instance].id, offset)
                if host.agent:
                    done = client.guest_exec(name, "/bin/sh", ["-c", BOOTSTRAP])
                    if done.exit_code != 0:
                        raise BackendError(
                            f"{name}: the bootstrap failed ({done.exit_code}): "
                            f"{done.err.strip() or done.out.strip()}"
                        )
            if start:
                self.start(manifest, state)
        except Exception:
            self._remove(client, manifest.run)
            raise
        return state

    def _run_iso(
        self,
        tmp: Path,
        run_dir: Path,
        wheels: Path,
        host: HostSpec,
        attachments: Sequence[GuestAttachment],
    ) -> Path:
        stage = tmp / f"stage-{flat_id(host.instance)}"
        stage.mkdir()
        stage_run(run_dir, stage)
        guest = GuestHost(
            host.instance,
            host.hostname,
            f"program.{flat_id(host.instance)}.json",
            tuple(attachments),
            tuple((r.cidr, r.via) for r in host.routes),
            host.forwards,
            host.gate,
            GUEST_OUT,
        )
        (stage / "host.json").write_text(guest.json() + "\n", encoding="utf-8")
        (stage / "bootstrap.sh").write_text(
            (files(__package__) / "bootstrap.sh").read_text(encoding="utf-8"), encoding="utf-8"
        )
        (stage / "wheels").mkdir()
        for wheel in wheels.iterdir():
            (stage / "wheels" / wheel.name).write_bytes(wheel.read_bytes())
        iso = tmp / f"{flat_id(host.instance)}.iso"
        self._iso(iso, stage)
        return iso

    def start(self, manifest: RunManifest, state: RunState) -> None:
        client = self._connect()
        for host in manifest.hosts:
            if host.gate is not None:
                client.guest_write(state.hosts[host.instance].name, host.gate, b"go\n")

    def quiesce(self, manifest: RunManifest, state: RunState) -> None:
        """Segmentation and checksum offloads off inside every Linux guest, through the
        agent; a Windows guest's come with its agent (phase B)."""
        client = self._connect()
        for host in manifest.hosts:
            if host.platform == "linux":
                client.guest_exec(state.hosts[host.instance].name, "/bin/sh", ["-c", QUIESCE])

    def collect(self, manifest: RunManifest, state: RunState, run_dir: Path) -> None:
        """What the agent wrote under ``/tiergen/out``, as a tarball through the agent,
        into ``run_dir/out/<instance>``; the bootstrap's log beside it."""
        client = self._connect()
        for host in manifest.hosts:
            if not host.agent:
                continue
            name = state.hosts[host.instance].name
            out = run_dir / "out" / flat_id(host.instance)
            out.mkdir(parents=True, exist_ok=True)
            done = client.guest_exec(
                name, "/bin/sh", ["-c", f"tar -czf /tiergen/out.tgz -C {GUEST_OUT} ."]
            )
            if done.exit_code != 0:
                raise BackendError(f"{name}: cannot pack its outputs: {done.err.strip()}")
            with tarfile.open(
                fileobj=io.BytesIO(client.guest_read(name, "/tiergen/out.tgz"))
            ) as tar:
                tar.extractall(out, filter="data")
            log = client.guest_read(name, "/tiergen/bootstrap.log")
            (out / "bootstrap.log").write_bytes(log)

    def down(self, manifest: RunManifest) -> None:
        self._remove(self._connect(), manifest.run)

    @staticmethod
    def _remove(client: Client, run: str) -> None:
        for name, description in client.domains().items():
            try:
                labels: Mapping[str, object] = json.loads(description or "{}")
            except json.JSONDecodeError:
                continue
            if labels.get(RUN_LABEL) == run:
                client.destroy_domain(name)
        prefix = f"tiergen-{run}-"
        for volume in client.volumes(POOL):
            if volume.startswith(prefix):
                client.delete_volume(POOL, volume)
        for network in client.networks():
            if network.startswith(prefix):
                client.destroy_network(network)
