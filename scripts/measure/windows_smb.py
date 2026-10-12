"""What Windows reports of an SMB connection, and what ties it to the process that asked.

    uv run python scripts/measure/windows_smb.py --out measure-smb
    uv run python scripts/measure/windows_smb.py --out measure-smb --report-only

Brings up a Samba container (``samba/``) and a clone of the Windows workstation template on
one isolated bridge, through the Docker and libvirt backends as a run would. In the guest,
``windows_smb.ps1`` records an ETW session over the SMB client, Kernel-Network,
Kernel-Process, Kernel-File, Kerberos and LSA providers while fresh processes map the
share, list it, read a file, unmap it and list it unmapped, each process id noted; Sysmon's
and the SMB client's channels are exported beside the trace. Everything comes back under
``--out``, and ``report.md`` says, per provider and event, which processes the events were
logged in and which fields name the server, and walks each action's events in time order.

The question it answers: is there an event that names the requesting process together with
something that identifies the connection the System process then opens?
"""

import argparse
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from tiergen.backends.infra.docker._client import DaemonClient
from tiergen.backends.infra.docker.backend import DockerBackend
from tiergen.backends.infra.libvirt._client import LibvirtClient
from tiergen.backends.infra.libvirt.backend import LibvirtBackend, domain_name
from tiergen.interfaces import Attachment, HostSpec, NetworkSpec, RunManifest

HERE = Path(__file__).parent
RUN = "measure-smb"
SAMBA_IMAGE = "tiergen/measure-samba"
SERVER = "10.77.0.53"
GUEST = "10.77.0.21"
MAC = "52:54:00:4d:00:15"
USER = "tiergen"
PASSWORD = "Tiergen-2026!"
POWERSHELL = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
NS = "{http://schemas.microsoft.com/win/2004/08/events/event}"

LAN = NetworkSpec("lan", "10.77.0.0/24", "10.77.0.1", "data", True, "tg-measure-smb")
SAMBA = HostSpec(
    "m/samba[0]", "samba", "linux", "samba", SAMBA_IMAGE, (), (), (Attachment("lan", SERVER),)
)
WS = HostSpec(
    "m/ws[0]",
    "workstation",
    "windows",
    "ws",
    "windows-agent",
    (),
    (),
    (Attachment("lan", GUEST, MAC),),
)
DOCKER = RunManifest(RUN, "docker", (LAN,), (SAMBA,))
LIBVIRT = RunManifest(RUN, "libvirt", (LAN,), (WS,))


def measure(out: Path) -> None:
    daemon = DaemonClient()
    if daemon.image_id(SAMBA_IMAGE) is None:
        print(f"building {SAMBA_IMAGE}")
        daemon.build_image(SAMBA_IMAGE, HERE / "samba")
    run_dir = out / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    docker, libvirt = DockerBackend(), LibvirtBackend(agent_timeout_s=600)
    try:
        docker.up(DOCKER, run_dir)
        libvirt.up(LIBVIRT, run_dir, start=False)
        guests = LibvirtClient()
        domain = domain_name(RUN, WS.instance)
        guests.guest_exec(domain, "C:\\Windows\\System32\\cmd.exe", ["/c", "mkdir", "C:\\m"])
        guests.guest_write(domain, "C:\\m\\measure.ps1", (HERE / "windows_smb.ps1").read_bytes())
        began = time.monotonic()
        done = guests.guest_exec(
            domain,
            POWERSHELL,
            [
                "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "C:\\m\\measure.ps1",
                "-Mac", MAC, "-Address", GUEST, "-Prefix", "24", "-Server", SERVER,
                "-User", USER, "-Password", PASSWORD,
            ],
            timeout_s=900,
        )  # fmt: skip
        (out / "guest.out").write_text(done.out + "\n--- stderr\n" + done.err, "utf-8")
        if done.exit_code != 0:
            log = guests.guest_read(domain, "C:\\m\\measure.log").decode("utf-8", "replace")
            raise SystemExit(f"the guest script exited {done.exit_code}:\n{log[-3000:]}")
        print(f"measured in {time.monotonic() - began:.0f} s")
        (out / "result.zip").write_bytes(guests.guest_read(domain, "C:\\m\\result.zip"))
    finally:
        libvirt.down(LIBVIRT)
        docker.down(DOCKER)
    with zipfile.ZipFile(out / "result.zip") as z:
        z.extractall(out / "result")


@dataclass
class Event:
    provider: str
    id: int
    task: str
    time: datetime
    pid: int
    activity: str
    data: dict[str, str] = field(default_factory=dict[str, str])


def _time(text: str) -> datetime:
    """Windows' timestamps: seven fractional digits, which fromisoformat cuts to six, and
    either a ``Z`` or an offset."""
    text = re.sub(r"(\.\d{6})\d+", r"\1", text.strip())
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def read_trace(path: Path) -> list[Event]:
    """tracerpt's XML: the header's process id is the context the event was logged in."""
    events: list[Event] = []
    for ev in ET.parse(path).getroot().iter(f"{NS}Event"):
        system = ev.find(f"{NS}System")
        if system is None:
            continue
        provider = system.find(f"{NS}Provider")
        execution = system.find(f"{NS}Execution")
        created = system.find(f"{NS}TimeCreated")
        correlation = system.find(f"{NS}Correlation")
        if provider is None or execution is None or created is None:
            continue
        info = ev.find(f"{NS}RenderingInfo")
        task = info.findtext(f"{NS}Task", "") if info is not None else ""
        data = {d.get("Name", f"#{i}"): (d.text or "") for i, d in enumerate(ev.iter(f"{NS}Data"))}
        events.append(
            Event(
                provider.get("Name", ""),
                int(system.findtext(f"{NS}EventID", "0")),
                task or "",
                _time(created.get("SystemTime", "")),
                int(execution.get("ProcessID", "0")),
                correlation.get("ActivityID", "") if correlation is not None else "",
                data,
            )
        )
    return sorted(events, key=lambda e: e.time)


def processes(events: list[Event]) -> tuple[dict[int, str], dict[int, int]]:
    """Image and parent by process id, from Kernel-Process's starts."""
    image: dict[int, str] = {4: "System"}
    parent: dict[int, int] = {}
    for e in events:
        if e.provider == "Microsoft-Windows-Kernel-Process" and e.id == 1:
            pid = int(e.data.get("ProcessID", "0"))
            image[pid] = e.data.get("ImageName", "?").rsplit("\\", 1)[-1]
            parent[pid] = int(e.data.get("ParentProcessID", "0"))
    return image, parent


def sysmon(path: Path) -> list[tuple[int, dict[str, str]]]:
    """Sysmon's events from ``wevtutil qe /f:xml``: (event id, data)."""
    if not path.is_file() or path.stat().st_size < 64:
        return []
    found: list[tuple[int, dict[str, str]]] = []
    for ev in ET.parse(path).getroot().iter(f"{NS}Event"):
        data = {d.get("Name", ""): (d.text or "") for d in ev.iter(f"{NS}Data")}
        found.append((int(ev.findtext(f"{NS}System/{NS}EventID", "0")), data))
    return found


def report(out: Path) -> str:
    result = out / "result"
    events = read_trace(result / "trace.xml")
    actions = json.loads((result / "actions.json").read_text("utf-8-sig"))
    image, parent = processes(events)
    logged = sysmon(result / "sysmon.xml")
    for eid, data in logged:
        # Processes that started before the trace are named from Sysmon's creations.
        if eid == 1 and int(data.get("ProcessId", "0")) not in image:
            image[int(data["ProcessId"])] = data.get("Image", "?").rsplit("\\", 1)[-1]

    def descends(pid: int, root: int) -> bool:
        seen: set[int] = set()
        while pid and pid not in seen:
            if pid == root:
                return True
            seen.add(pid)
            pid = parent.get(pid, 0)
        return False

    requesters = {a["pid"] for a in actions}

    def who(pid: int) -> str:
        mark = "*" if any(descends(pid, r) for r in requesters) else ""
        return f"{image.get(pid, '?')}({pid}){mark}"

    lines = [
        "# What Windows reports of SMB",
        "",
        "Processes marked * are an action's process or its descendants.",
        "",
        "| action | pid | exit | start | end |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {a['action']} | {a['pid']} | {a['exit']} | {a['start']} | {a['end']} |" for a in actions
    ]
    connects = [
        e
        for e in events
        if e.provider.endswith("Kernel-Network") and e.id == 12 and e.data.get("daddr") == SERVER
    ]
    lines += ["", "## Connections and requests", ""]
    lines += [
        f"- TCP connect {e.data['saddr']}:{e.data['sport'].strip()} -> {SERVER}:"
        f"{e.data['dport'].strip()} at {e.time.time()}, logged in {who(e.pid)}"
        for e in connects
    ]
    closes = sum(1 for e in events if e.provider.endswith("Kernel-Network") and e.id == 13)
    lines.append(f"- TCP disconnects in the trace: {closes}")
    lines += [
        f"- Sysmon network connection: {d.get('Image')} ({d.get('ProcessId')}) "
        f"{d.get('SourceIp')}:{d.get('SourcePort')} -> {d.get('DestinationIp')}:"
        f"{d.get('DestinationPort')}"
        for eid, d in logged
        if eid == 3 and d.get("DestinationIp") == SERVER
    ]
    handles = {e.data["VcEndpoint"] for e in events if e.data.get("VcEndpoint")}
    lines.append(f"- SMB connection handles (VcEndpoint): {len(handles)}")
    requests: dict[int, list[Event]] = defaultdict(list)
    for e in events:
        if e.provider.endswith("SMBClient") and e.id == 30406:
            requests[e.pid].append(e)
    for pid, sent in sorted(requests.items()):
        commands: dict[str, int] = defaultdict(int)
        for e in sent:
            commands[e.data.get("Command", "").strip()] += 1
        sessions = sorted({e.data.get("SessionId", "") for e in sent})
        lines.append(
            f"- requests sent (SMBClient 30406) in {who(pid)}: "
            + ", ".join(f"{c} {n}" for c, n in sorted(commands.items()))
            + f"; sessions {', '.join(sessions)}"
        )
    lines += [
        "",
        "## Per provider and event",
        "",
        "| provider | id | task | n | logged in | fields naming the server |",
        "|---|---|---|---|---|---|",
    ]
    groups: dict[tuple[str, int, str], list[Event]] = defaultdict(list)
    for e in events:
        groups[(e.provider, e.id, e.task)].append(e)
    for (provider, eid, task), group in sorted(groups.items()):
        pids = sorted({e.pid for e in group})
        shown = ", ".join(who(p) for p in pids[:6]) + (" …" if len(pids) > 6 else "")
        naming = sorted(
            {k for e in group for k, v in e.data.items() if SERVER in v or "share" in v}
        )
        lines.append(
            f"| {provider.removeprefix('Microsoft-Windows-')} | {eid} | {task} | {len(group)} "
            f"| {shown} | {', '.join(naming)} |"
        )
    lines += ["", "## Each action's events", ""]
    for a in actions:
        start, end = _time(a["start"]), _time(a["end"])
        lines += [f"### {a['action']} (pid {a['pid']}, exit {a['exit']})", ""]
        for e in events:
            if not (start <= e.time <= end) or e.provider.endswith("Kernel-File"):
                continue
            if e.provider.endswith("Kernel-Process") and not any(
                descends(e.pid, r) for r in requesters
            ):
                continue
            fields = "; ".join(f"{k}={v}" for k, v in e.data.items() if v)[:240]
            lines.append(
                f"- {e.time.time()} {e.provider.removeprefix('Microsoft-Windows-')} {e.id} "
                f"{e.task} in {who(e.pid)} act {e.activity[:9]}: {fields}"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="What Windows reports of an SMB connection.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report-only", action="store_true", help="re-read what --out holds")
    args = parser.parse_args(argv)
    if not args.report_only:
        if (args.out / "result").exists():
            print(f"{args.out} holds a measurement; --report-only re-reads it", file=sys.stderr)
            return 1
        measure(args.out)
    (args.out / "report.md").write_text(report(args.out), "utf-8")
    print(f"report: {args.out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
