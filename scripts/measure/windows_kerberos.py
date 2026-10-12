"""What Windows reports of a Kerberos exchange, and what ties it to the process that caused it.

    uv run python scripts/measure/windows_kerberos.py --out measure-krb
    uv run python scripts/measure/windows_kerberos.py --out measure-krb --report-only

Brings up the joined pair (``scripts/templates/build.py join``) on an isolated bridge
through the libvirt backend. On the workstation, ``windows_kerberos.ps1`` records an ETW
session over the Kerberos, LSA, SMB client, DNS client, Kernel-Network and Kernel-Process
providers while fresh processes purge the tickets, ask for one, reach the DC's SYSVOL share
with no ticket cached, resolve the DC's name, and while a scheduled task logs a domain user
on and lists NETLOGON. The DC's Kerberos audit events (4768, 4769) are exported beside it.
``report.md`` lists the connections to the DC and the process each was logged in, which
Kerberos, LSA and DNS events name which processes and what, and each action's events.

The question: the KDC exchanges go out from ``lsass.exe``; does anything name the process
that caused one, together with the exchange?
"""

import argparse
import json
import sys
import time
import zipfile
from collections import defaultdict
from pathlib import Path

from etw import Event, images, parse_time, read_trace, sysmon

from tiergen.backends.infra.libvirt._client import LibvirtClient
from tiergen.backends.infra.libvirt.backend import LibvirtBackend, domain_name
from tiergen.interfaces import Attachment, HostSpec, NetworkSpec, RunManifest

HERE = Path(__file__).parent
RUN = "measure-krb"
DOMAIN = "hq.tiergen.test"
DC_NAME = f"TIERGEN-DC.{DOMAIN}"
DC_ADDRESS = "10.10.0.10"
USER = "Administrator"
PASSWORD = "Tiergen-2026!"
POWERSHELL = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
WEVTUTIL = "C:\\Windows\\System32\\wevtutil.exe"

LAN = NetworkSpec("lan", "10.10.0.0/24", "10.10.0.1", "data", True, "tg-measure-krb")
DC = HostSpec(
    "m/dc[0]",
    "dc",
    "windows",
    "dc",
    "hq-dc",
    (),
    (),
    (Attachment("lan", DC_ADDRESS, "52:54:00:4b:00:0a"),),
)
WS = HostSpec(
    "m/ws[0]",
    "ws",
    "windows",
    "ws",
    "hq-ws",
    (),
    (),
    (Attachment("lan", "10.10.0.21", "52:54:00:4b:00:15"),),
)
MANIFEST = RunManifest(RUN, "libvirt", (LAN,), (DC, WS))


def measure(out: Path) -> None:
    run_dir = out / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    backend = LibvirtBackend(agent_timeout_s=600)
    try:
        backend.up(MANIFEST, run_dir, start=False)
        guests = LibvirtClient()
        ws, dc = domain_name(RUN, WS.instance), domain_name(RUN, DC.instance)
        guests.guest_exec(ws, "C:\\Windows\\System32\\cmd.exe", ["/c", "mkdir", "C:\\m"])
        guests.guest_write(ws, "C:\\m\\measure.ps1", (HERE / "windows_kerberos.ps1").read_bytes())
        began = time.monotonic()
        done = guests.guest_exec(
            ws,
            POWERSHELL,
            [
                "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "C:\\m\\measure.ps1",
                "-Dc", DC_NAME, "-Domain", DOMAIN, "-User", USER, "-Password", PASSWORD,
            ],
            timeout_s=900,
        )  # fmt: skip
        (out / "guest.out").write_text(done.out + "\n--- stderr\n" + done.err, "utf-8")
        if done.exit_code != 0:
            log = guests.guest_read(ws, "C:\\m\\measure.log").decode("utf-8", "replace")
            raise SystemExit(f"the guest script exited {done.exit_code}:\n{log[-3000:]}")
        print(f"measured in {time.monotonic() - began:.0f} s")
        (out / "result.zip").write_bytes(guests.guest_read(ws, "C:\\m\\result.zip"))
        audit = guests.guest_exec(
            dc,
            WEVTUTIL,
            [
                "qe",
                "Security",
                "/q:*[System[(EventID=4768 or EventID=4769)]]",
                "/f:xml",
                "/e:Events",
            ],
        )
        (out / "dc-security.xml").write_text(audit.out, "utf-8")
    finally:
        backend.down(MANIFEST)
    with zipfile.ZipFile(out / "result.zip") as z:
        z.extractall(out / "result")


def report(out: Path) -> str:
    result = out / "result"
    events = read_trace(result / "trace.xml")
    actions = json.loads((result / "actions.json").read_text("utf-8-sig"))
    logged = sysmon(result / "sysmon.xml")
    image, parent = images(events, logged)
    for a in actions:
        if a.get("marker"):
            # The scheduled task's process, by its command line.
            a["pid"] = next(
                (
                    int(d["ProcessId"])
                    for eid, d in logged
                    if eid == 1 and a["marker"] in d.get("CommandLine", "")
                ),
                0,
            )

    def descends(pid: int, root: int) -> bool:
        seen: set[int] = set()
        while pid and pid not in seen:
            if pid == root:
                return True
            seen.add(pid)
            pid = parent.get(pid, 0)
        return False

    requesters = {a["pid"] for a in actions if a["pid"]}

    def who(pid: int) -> str:
        mark = "*" if any(descends(pid, r) for r in requesters) else ""
        return f"{image.get(pid, '?')}({pid}){mark}"

    def naming(e: Event) -> list[str]:
        return [
            k
            for k, v in e.data.items()
            if DC_ADDRESS in v or "cifs/" in v.lower() or "tiergen-dc" in v.lower()
        ]

    lines = [
        "# What Windows reports of Kerberos",
        "",
        "Processes marked * are an action's process or its descendants.",
        "",
        "| action | pid | exit | start | end |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {a['action']} | {a['pid']} | {a['exit']} | {a['start']} | {a['end']} |" for a in actions
    ]
    lines += ["", "## Connections to the DC", ""]
    for e in events:
        if (
            e.provider.endswith("Kernel-Network")
            and e.id in (12, 42)
            and e.data.get("daddr") == DC_ADDRESS
        ):
            kind = "TCP connect" if e.id == 12 else "UDP send"
            # Kernel-Network's header context is whatever ran the stack; its PID field is
            # the socket's owner.
            owner = int(e.data.get("PID", "0").strip() or 0)
            lines.append(
                f"- {e.time.time()} {kind} {e.data.get('saddr')}:{e.data.get('sport', '').strip()}"
                f" -> {DC_ADDRESS}:{e.data.get('dport', '').strip()} owned by {who(owner)}"
            )
    lines += [
        f"- Sysmon network connection: {d.get('Image', '').rsplit(chr(92), 1)[-1]} "
        f"({d.get('ProcessId')}) -> {DC_ADDRESS}:{d.get('DestinationPort')}"
        for eid, d in logged
        if eid == 3 and d.get("DestinationIp") == DC_ADDRESS
    ]
    lines += [
        "",
        "## Authentication and DNS client events",
        "",
        "| provider | id | task | n | logged in | fields naming the DC or a service |",
        "|---|---|---|---|---|---|",
    ]
    groups: dict[tuple[str, int, str], list[Event]] = defaultdict(list)
    for e in events:
        if not any(k in e.provider for k in ("Kernel-", "SMBClient")):
            groups[(e.provider, e.id, e.task)].append(e)
    for (provider, eid, task), group in sorted(groups.items()):
        pids = sorted({e.pid for e in group})
        shown = ", ".join(who(p) for p in pids[:6]) + (" …" if len(pids) > 6 else "")
        fields = sorted({k for e in group for k in naming(e)})
        lines.append(
            f"| {provider.removeprefix('Microsoft-Windows-')} | {eid} | {task} | {len(group)} "
            f"| {shown} | {', '.join(fields)} |"
        )
    lines += ["", "## The DC's Kerberos audit", ""]
    for eid, d in sysmon(out / "dc-security.xml"):
        lines.append(
            f"- {eid} {d.get('TargetUserName')} {d.get('ServiceName')} from "
            f"{d.get('IpAddress')}:{d.get('IpPort')} status {d.get('Status')}"
        )
    lines += ["", "## Each action's events", ""]
    for a in actions:
        start, end = parse_time(a["start"]), parse_time(a["end"])
        lines += [f"### {a['action']} (pid {a['pid']}, exit {a['exit']})", ""]
        for e in events:
            if not (start <= e.time <= end):
                continue
            relevant = (
                not any(k in e.provider for k in ("Kernel-", "SMBClient"))
                or (e.provider.endswith("SMBClient") and e.id in (30203, 30406))
                or (e.provider.endswith("Kernel-Network") and e.data.get("daddr") == DC_ADDRESS)
                or (e.provider.endswith("Kernel-Process") and e.pid in requesters)
            )
            if not relevant:
                continue
            fields = "; ".join(f"{k}={v}" for k, v in e.data.items() if v)[:260]
            lines.append(
                f"- {e.time.time()} {e.provider.removeprefix('Microsoft-Windows-')} {e.id} "
                f"{e.task} in {who(e.pid)}: {fields}"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="What Windows reports of a Kerberos exchange.")
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
