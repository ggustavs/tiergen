"""What links a Windows process's request to the traffic the system sends for it, measured
on the wire as well as on the host.

    uv run python scripts/measure/windows_links.py --out measure-links
    uv run python scripts/measure/windows_links.py --out measure-links --report-only

Brings up the joined pair (``scripts/templates/build.py join``) and a Samba container
(``samba/``) on one isolated bridge, captures the bridge with dumpcap, and runs
``windows_links.ps1`` on the workstation: processes alone and two at a time use the DC's
shares and Samba's, ask for tickets and resolve names, and a scheduled task does so as a
domain user, under an ETW session over the SMB client, DNS client, Kernel-Network and
Kernel-Process providers. The DC's Kerberos audit is exported, the guests' clock offsets are
measured before and after, and the pinned Zeek and Suricata read the capture with
``examples/hq_lan``'s configuration.

``report.md`` computes the joins rather than listing events:
- each SMB request the client logged in a process (30406) against the SMB2 headers on the
  wire, by session and message id, and which processes' requests share each connection;
- each Kerberos exchange on the wire, the requests that present the ticket it handed out,
  down to the SMB sessions and the processes whose requests used them, against the DC's
  audit by client port;
- each name a process resolved (DNS client 3006) against the queries on the wire;
- each sensor record of SMB, Kerberos and DNS against the packets of its connection: does
  its timestamp name one, and which.
"""

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from etw import NS, Event, images, parse_time, read_trace, sysmon
from wire import KRB_TYPES, SMB2_COMMANDS, Krb, Smb2, Wire, read

from tiergen.backends.infra.docker._client import DaemonClient
from tiergen.backends.infra.docker.backend import DockerBackend
from tiergen.backends.infra.libvirt._client import LibvirtClient
from tiergen.backends.infra.libvirt.backend import LibvirtBackend, domain_name
from tiergen.backends.sensor._base.runner import run_image
from tiergen.backends.sensor._base.zeeklog import read_zeek_log
from tiergen.backends.sensor.suricata.runtime import Suricata
from tiergen.backends.sensor.zeek.runtime import Zeek
from tiergen.core.ir import SensorSpec
from tiergen.interfaces import Attachment, HostSpec, NetworkSpec, RunManifest

HERE = Path(__file__).parent
MODELS = HERE.parents[1] / "examples" / "hq_lan" / "models"
RUN = "measure-links"
SAMBA_IMAGE = "tiergen/measure-samba"
DOMAIN = "hq.tiergen.test"
DC_SHORT = "TIERGEN-DC"
DC_FQDN = f"{DC_SHORT}.{DOMAIN}"
DC_ADDRESS = "10.10.0.10"
WS_ADDRESS = "10.10.0.21"
SERVER = "10.10.0.53"
SERVER_USER = "tiergen"
USER = "Administrator"
POWERSHELL = "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"
WEVTUTIL = "C:\\Windows\\System32\\wevtutil.exe"
SENSORS = (
    Zeek(SensorSpec("zeek", "zeek", "7.0.11", "hq_lan.zeek", "offline", (), "label"), "lan"),
    Suricata(
        SensorSpec("suricata", "suricata", "7.0.7", "hq_lan.suricata", "offline", (), "label"),
        "lan",
    ),
)
# What the SMB client's events call each command, against the protocol's numbers.
ETW_COMMANDS = {
    "NEGOTIATE": 0,
    "SESSION": 1,
    "LOGOFF": 2,
    "TRE_CONN": 3,
    "TRE_DCON": 4,
    "CREATE": 5,
    "CLOSE": 6,
    "FLUSH": 7,
    "READ": 8,
    "WRITE": 9,
    "LOCK": 10,
    "IOCTL": 11,
    "CANCEL": 12,
    "ECHO": 13,
    "QRY_DIR": 14,
    "CHG_NOTIFY": 15,
    "QRY_INFO": 16,
    "SET_INFO": 17,
}

LAN = NetworkSpec("lan", "10.10.0.0/24", "10.10.0.1", "data", True, "tg-measure-lnk")
SAMBA = HostSpec(
    "m/samba[0]", "samba", "linux", "samba", SAMBA_IMAGE, (), (), (Attachment("lan", SERVER),)
)
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
    (Attachment("lan", WS_ADDRESS, "52:54:00:4b:00:15"),),
)
DOCKER = RunManifest(RUN, "docker", (LAN,), (SAMBA,))
LIBVIRT = RunManifest(RUN, "libvirt", (LAN,), (DC, WS))

type ActionOf = Callable[[int], str]
"""The action a process id belongs to, or its image where it belongs to none."""
type OnWire = Callable[[datetime], float]
"""A guest's timestamp on the capture's clock."""


def offsets(guests: LibvirtClient) -> dict[str, float]:
    """Each guest's clock against the host's, seconds to add to its stamps, by the midpoint
    of one guest agent round trip."""
    found: dict[str, float] = {}
    for host in (DC, WS):
        before = time.time()
        guest = guests.guest_time(domain_name(RUN, host.instance))
        found[host.instance] = (before + time.time()) / 2 - guest
    return found


def measure(out: Path, password: str) -> None:
    daemon = DaemonClient()
    if daemon.image_id(SAMBA_IMAGE) is None:
        print(f"building {SAMBA_IMAGE}")
        daemon.build_image(SAMBA_IMAGE, HERE / "samba")
    run_dir = out / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    docker, libvirt = DockerBackend(), LibvirtBackend(agent_timeout_s=600)
    dumpcap: subprocess.Popen[bytes] | None = None
    try:
        docker.up(DOCKER, run_dir)
        libvirt.up(LIBVIRT, run_dir, start=False)
        guests = LibvirtClient()
        ws, dc = domain_name(RUN, WS.instance), domain_name(RUN, DC.instance)
        clocks = {"before": offsets(guests)}
        with (out / "dumpcap.log").open("wb") as log:
            dumpcap = subprocess.Popen(
                ["dumpcap", "-q", "-i", LAN.bridge, "-w", str(out / "capture.pcapng")],
                stdout=subprocess.DEVNULL,
                stderr=log,
                start_new_session=True,
            )
        time.sleep(2)
        if dumpcap.poll() is not None:
            raise SystemExit(f"dumpcap exited {dumpcap.returncode}; see {out / 'dumpcap.log'}")
        guests.guest_exec(ws, "C:\\Windows\\System32\\cmd.exe", ["/c", "mkdir", "C:\\m"])
        guests.guest_write(ws, "C:\\m\\measure.ps1", (HERE / "windows_links.ps1").read_bytes())
        began = time.monotonic()
        done = guests.guest_exec(
            ws,
            POWERSHELL,
            [
                "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "C:\\m\\measure.ps1",
                "-DcShort", DC_SHORT, "-DcFqdn", DC_FQDN, "-Domain", DOMAIN,
                "-Server", SERVER, "-ServerUser", SERVER_USER, "-User", USER,
                "-Password", password,
            ],
            timeout_s=1200,
        )  # fmt: skip
        (out / "guest.out").write_text(done.out + "\n--- stderr\n" + done.err, "utf-8")
        if done.exit_code != 0:
            log_text = guests.guest_read(ws, "C:\\m\\measure.log").decode("utf-8", "replace")
            raise SystemExit(f"the guest script exited {done.exit_code}:\n{log_text[-3000:]}")
        print(f"measured in {time.monotonic() - began:.0f} s", flush=True)
        clocks["after"] = offsets(guests)
        (out / "offsets.json").write_text(json.dumps(clocks, indent=2) + "\n", "utf-8")
        (out / "result.zip").write_bytes(guests.guest_read(ws, "C:\\m\\result.zip"))
        audit = guests.guest_exec(
            dc,
            WEVTUTIL,
            [
                "qe",
                "Security",
                "/q:*[System[(EventID=4768 or EventID=4769 or EventID=4770)]]",
                "/f:xml",
                "/e:Events",
            ],
        )
        (out / "dc-security.xml").write_text(audit.out, "utf-8")
    finally:
        if dumpcap is not None and dumpcap.poll() is None:
            os.kill(dumpcap.pid, signal.SIGINT)
            dumpcap.wait(timeout=30)
        libvirt.down(LIBVIRT)
        docker.down(DOCKER)
    with zipfile.ZipFile(out / "result.zip") as z:
        z.extractall(out / "result")


def sense(out: Path) -> None:
    """The pinned sensors over the capture, as ``assemble`` runs them, except that Suricata
    skips checksum validation: the Windows guests' virtio NICs offload it, nothing turns
    that off in a Windows guest yet, and with validation on Suricata tracked none of the SMB
    connections and half of the Kerberos ones (Zeek runs with -C anyway). What is measured
    here is which packet a record is stamped with, not the checksums."""
    pcap = out / "capture.pcapng"
    for sensor in SENSORS:
        config = MODELS / sensor.spec.config
        if isinstance(sensor, Suricata):
            run_image(
                DaemonClient(),
                sensor.image,
                [*sensor.command(pcap.name, config.name), "-k", "none"],
                pcap,
                config,
                out / "sensors" / sensor.name,
            )
        else:
            sensor.run(pcap, config, out / "sensors" / sensor.name)


@dataclass(frozen=True)
class Record:
    """One sensor record: which log, its connection's endpoints and its timestamp."""

    sensor: str
    kind: str
    ends: frozenset[tuple[str, int]]
    ts: float
    detail: str


def records(out: Path) -> list[Record]:
    found: list[Record] = []
    zeek = out / "sensors" / "zeek"
    for log in ("smb_mapping", "smb_files", "kerberos", "dns", "dce_rpc", "ntlm"):
        path = zeek / f"{log}.log"
        if not path.is_file():
            continue
        for r in read_zeek_log(path):
            ends = frozenset(
                {
                    (str(r["id.orig_h"]), int(str(r["id.orig_p"]))),
                    (str(r["id.resp_h"]), int(str(r["id.resp_p"]))),
                }
            )
            detail = {
                "kerberos": f"{r.get('request_type')} {r.get('client')} {r.get('service')}",
                "dns": f"{r.get('query')} id {r.get('trans_id')}",
                "smb_mapping": f"{r.get('path')}",
                "smb_files": f"{r.get('action')} {r.get('name')}",
                "dce_rpc": f"{r.get('endpoint')} {r.get('operation')}",
                "ntlm": f"{r.get('username')}",
            }[log]
            found.append(Record("zeek", log, ends, float(str(r["ts"])), detail))
    eve = out / "sensors" / "suricata" / "eve.json"
    if eve.is_file():
        for line in eve.read_text("utf-8").splitlines():
            e = json.loads(line)
            kind = e.get("event_type")
            if kind not in ("smb", "krb5", "dns", "dcerpc"):
                continue
            ends = frozenset(
                {
                    (e["src_ip"], int(e.get("src_port", 0))),
                    (e["dest_ip"], int(e.get("dest_port", 0))),
                }
            )
            body = e.get(kind, {})
            detail = {
                "smb": f"tx {body.get('id')} {body.get('command')} session {body.get('session_id')}"
                f" tree {body.get('tree_id')}",
                "krb5": f"{body.get('msg_type')} {body.get('cname')} {body.get('sname')}",
                "dns": f"{body.get('type')} {body.get('rrname')} id {body.get('id')}",
                "dcerpc": f"{body.get('request')} {body.get('response')}",
            }[kind]
            ts = datetime.fromisoformat(e["timestamp"]).timestamp()
            found.append(Record("suricata", kind, ends, ts, detail))
    return found


def frames(pcap: Path) -> dict[frozenset[tuple[str, int]], list[tuple[float, int]]]:
    """Every TCP and UDP frame's time and number, by its connection's two endpoints."""
    args = [
        "tshark", "-r", str(pcap), "-Y", "tcp || udp", "-T", "fields", "-E", "separator=/t",
        "-E", "occurrence=f",
        "-e", "frame.number", "-e", "frame.time_epoch", "-e", "ip.src", "-e", "ip.dst",
        "-e", "tcp.srcport", "-e", "tcp.dstport", "-e", "udp.srcport", "-e", "udp.dstport",
    ]  # fmt: skip
    found: dict[frozenset[tuple[str, int]], list[tuple[float, int]]] = defaultdict(list)
    lines = subprocess.run(args, check=True, capture_output=True, text=True).stdout
    for line in lines.splitlines():
        n, t, src, dst, ts_, td, us, ud = (line.split("\t") + [""] * 8)[:8]
        sport, dport = (ts_, td) if ts_ else (us, ud)
        if src and sport:
            found[frozenset({(src, int(sport)), (dst, int(dport))})].append((float(t), int(n)))
    return found


def report(out: Path) -> str:
    result = out / "result"
    events = read_trace(result / "trace.xml")
    actions = json.loads((result / "actions.json").read_text("utf-8-sig"))
    logged = sysmon(result / "sysmon.xml")
    image, parent = images(events, logged)
    clocks = json.loads((out / "offsets.json").read_text("utf-8"))
    ws_offset = clocks["before"][WS.instance]
    wire = read(out / "capture.pcapng")
    for a in actions:
        if a.get("marker"):
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

    def action_of(pid: int) -> str:
        """The action whose process is ``pid`` or an ancestor of it, else the image."""
        for a in actions:
            if a["pid"] and descends(pid, a["pid"]):
                return str(a["action"])
        return f"{image.get(pid, '?')}({pid})"

    def on_wire(t: datetime) -> float:
        return t.timestamp() + ws_offset

    lines = ["# What links a request to its traffic", ""]
    lines += [
        f"Clock offsets (s to add to a guest's stamps): before {clocks['before']}, "
        f"after {clocks['after']}.",
        "",
        "| action | pid | exit | start | end |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {a['action']} | {a['pid']} | {a['exit']} | {a['start']} | {a['end']} |" for a in actions
    ]
    lines += smb_join(events, wire, action_of)
    lines += krb_chain(out, events, wire, action_of, clocks["before"][DC.instance])
    lines += dns_join(events, wire, action_of, on_wire)
    lines += sensor_check(out, wire)
    return "\n".join(lines) + "\n"


def smb_join(events: list[Event], wire: Wire, action_of: ActionOf) -> list[str]:
    requests = [w for w in wire.smb2 if not w.response]
    by_key: dict[tuple[int, int], list[Smb2]] = defaultdict(list)
    for w in requests:
        by_key[(w.session_id, w.message_id)].append(w)
    sent = [e for e in events if e.provider.endswith("SMBClient") and e.id == 30406]
    tally: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    riders: dict[str, set[str]] = defaultdict(set)
    explained: set[tuple[int, int, int]] = set()
    for e in sent:
        who = action_of(e.pid)
        key = (int(e.data["SessionId"]), int(e.data["MessageId"]))
        hits = by_key.get(key, [])
        if len(hits) != 1:
            tally[who]["none" if not hits else "several"] += 1
            continue
        hit = hits[0]
        command = ETW_COMMANDS.get(e.data.get("Command", "").strip(), -1)
        tally[who]["matched" if command == hit.command else "command differs"] += 1
        riders[hit.frame.stream].add(who)
        explained.add((hit.frame.number, hit.session_id, hit.message_id))
    lines = ["", "## SMB: requests logged in a process against the wire", ""]
    lines += [
        "Key: (SessionId, MessageId) of SMBClient 30406 against the SMB2 header.",
        "",
        "| logged in | " + " | ".join(("matched", "command differs", "none", "several")) + " |",
        "|---|---|---|---|---|",
    ]
    for who, counts in sorted(tally.items()):
        lines.append(
            f"| {who} | "
            + " | ".join(str(counts[k]) for k in ("matched", "command differs", "none", "several"))
            + " |"
        )
    lines += ["", "Connections and whose requests they carried:", ""]
    for stream, who in sorted(riders.items()):
        first = next(w.frame for w in wire.smb2 if w.frame.stream == stream)
        lines.append(
            f"- {stream} {first.src}:{first.sport} -> {first.dst}:{first.dport}: "
            + ", ".join(sorted(who))
        )
    unexplained: dict[str, int] = defaultdict(int)
    for w in requests:
        if (w.frame.number, w.session_id, w.message_id) not in explained:
            unexplained[SMB2_COMMANDS.get(w.command, str(w.command))] += 1
    lines.append(
        "- requests on the wire no 30406 explains: "
        + (", ".join(f"{c} {n}" for c, n in sorted(unexplained.items())) or "none")
    )
    return lines


def krb_chain(
    out: Path, events: list[Event], wire: Wire, action_of: ActionOf, dc_offset: float
) -> list[str]:
    lines = ["", "## Kerberos: exchanges, the tickets they handed out, and who used them", ""]
    sessions: dict[tuple[str, int], int] = {}
    for w in wire.smb2:
        # A session setup's request carries session 0; its response names the session.
        if w.command == 1 and w.response and w.session_id:
            sessions[(w.frame.stream, w.message_id)] = w.session_id
    setups = {
        w.frame.number: (w.frame.stream, w.message_id)
        for w in wire.smb2
        if w.command == 1 and not w.response
    }
    users: dict[int, set[str]] = defaultdict(set)
    for e in events:
        if e.provider.endswith("SMBClient") and e.id == 30406:
            users[int(e.data["SessionId"])].add(action_of(e.pid))
    first, last = wire.krb[0].frame.time - 5, wire.krb[-1].frame.time + 5
    audited = [
        (t + dc_offset, eid, d)
        for t, eid, d in audit(out / "dc-security.xml")
        if first <= t + dc_offset <= last
    ]

    def reply_to(k: Krb) -> Krb | None:
        return next(
            (
                r
                for r in wire.krb
                if r.msg_type == k.msg_type + 1
                and r.frame.stream == k.frame.stream
                and r.frame.time >= k.frame.time
            ),
            None,
        )

    def uses(reply: Krb, depth: int) -> list[str]:
        """Where the ticket ``reply`` handed out was presented, and, for a TGT, where the
        tickets bought with it were."""
        found: list[str] = []
        pad = "  " * depth
        for u in wire.krb:
            if u.frame.time <= reply.frame.time or not (u.tickets & reply.tickets):
                continue
            if u.frame.number in setups:
                stream, mid = setups[u.frame.number]
                session = sessions.get((stream, mid))
                used = ", ".join(sorted(users.get(session or -1, set()))) or "no logged request"
                found.append(f"{pad}- presented in an SMB session setup on {stream}: {used}")
            elif u.msg_type == 12:
                found.append(f"{pad}- presented in the TGS-REQ for {'/'.join(u.sname[-2:])}")
                bought = reply_to(u)
                if bought is not None:
                    found += uses(bought, depth + 1)
            else:
                found.append(
                    f"{pad}- presented in {KRB_TYPES.get(u.msg_type, u.msg_type)} to "
                    f"{u.frame.dst}:{u.frame.dport}"
                )
        return found or [f"{pad}- presented nowhere in the capture"]

    for k in wire.krb:
        if k.msg_type not in (10, 12):
            continue
        reply = reply_to(k)
        seen = [
            f"{eid} {d.get('TargetUserName')} {d.get('ServiceName')}"
            for t, eid, d in audited
            if int(d.get("IpPort", "0") or 0) == k.frame.sport and abs(t - k.frame.time) < 2
        ]
        lines.append(
            f"- {k.frame.time:.6f} {KRB_TYPES[k.msg_type]} from :{k.frame.sport} "
            f"cname {'/'.join(k.cname)} sname {'/'.join(k.sname)}; "
            f"reply {KRB_TYPES.get(reply.msg_type) if reply else 'none or an error'}; "
            f"DC audit {', '.join(seen) or 'none'}"
        )
        if reply is not None:
            lines += uses(reply, 1)
    return lines


def audit(path: Path) -> list[tuple[float, int, dict[str, str]]]:
    """The DC's Security events, each with its time on the DC's clock."""
    if not path.is_file() or path.stat().st_size < 64:
        return []
    found: list[tuple[float, int, dict[str, str]]] = []
    for ev in ET.parse(path).getroot().iter(f"{NS}Event"):
        created = ev.find(f"{NS}System/{NS}TimeCreated")
        if created is None:
            continue
        data = {d.get("Name", ""): (d.text or "") for d in ev.iter(f"{NS}Data")}
        found.append(
            (
                parse_time(created.get("SystemTime", "")).timestamp(),
                int(ev.findtext(f"{NS}System/{NS}EventID", "0")),
                data,
            )
        )
    return found


def dns_join(events: list[Event], wire: Wire, action_of: ActionOf, on_wire: OnWire) -> list[str]:
    lines = ["", "## DNS: names a process resolved against the queries on the wire", ""]
    lines += [
        "Each ask (DNS client 3006, in the asking process) against the nearest query of the "
        "same name within 0.5 s on the capture's clock; then each query with every ask it "
        "was the nearest for.",
        "",
    ]
    queries = [d for d in wire.dns if not d.response]
    askers: dict[int, list[str]] = defaultdict(list)
    for e in events:
        if not (e.provider.endswith("DNS-Client") and e.id == 3006):
            continue
        name = e.data.get("QueryName", "").rstrip(".").lower()
        at = on_wire(e.time)
        near = sorted(
            (
                q
                for q in queries
                if any(n.rstrip(".").lower() == name for n in q.names)
                and abs(q.frame.time - at) <= 0.5
            ),
            key=lambda q: abs(q.frame.time - at),
        )
        who = action_of(e.pid)
        if near:
            q = near[0]
            askers[q.frame.number].append(f"{who} ({q.frame.time - at:+.3f} s)")
        lines.append(
            f"- {who} asked {name or '(empty)'} type {e.data.get('QueryType', '').strip()}: "
            + (f"query id {near[0].id}" if near else "no query of that name within 0.5 s")
        )
    lines += ["", "Queries on the wire and who asked:", ""]
    for q in queries:
        lines.append(
            f"- {q.frame.time:.3f} id {q.id} {'/'.join(q.names)} from {q.frame.src}:"
            f"{q.frame.sport}: {', '.join(askers.get(q.frame.number, [])) or 'no ask'}"
        )
    return lines


def sensor_check(out: Path, wire: Wire) -> list[str]:
    lines = ["", "## Sensor records against the packets of their connection", ""]
    if not (out / "sensors").is_dir():
        return [*lines, "Sensors not run."]
    by_ends = frames(out / "capture.pcapng")
    kinds: dict[int, str] = {}
    for w in wire.smb2:
        kinds[w.frame.number] = f"SMB2 {SMB2_COMMANDS.get(w.command, w.command)} " + (
            "response" if w.response else "request"
        )
    for k in wire.krb:
        kinds[k.frame.number] = f"Kerberos {KRB_TYPES.get(k.msg_type, k.msg_type)}"
    for d in wire.dns:
        kinds[d.frame.number] = "DNS " + ("response" if d.response else "query")
    tally: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
    examples: dict[tuple[str, str], list[str]] = defaultdict(list)
    for r in records(out):
        match = [n for t, n in by_ends.get(r.ends, []) if abs(t - r.ts) < 1e-6]
        what = kinds.get(match[0], "other packet") if match else "no packet"
        tally[(r.sensor, r.kind)][what] += 1
        if len(examples[(r.sensor, r.kind)]) < 3:
            examples[(r.sensor, r.kind)].append(f"{r.detail} -> {what}")
    for (sensor, kind), counts in sorted(tally.items()):
        lines.append(
            f"- {sensor} {kind}: " + ", ".join(f"{what} {n}" for what, n in sorted(counts.items()))
        )
        lines += [f"  - e.g. {x}" for x in examples[(sensor, kind)]]
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="What links a request to its traffic.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--report-only", action="store_true", help="re-read what --out holds")
    parser.add_argument(
        "--password",
        default=os.environ.get("TIERGEN_LAB_PASSWORD", "Tiergen-2026!"),
        help="the lab password the templates were built with (scripts/templates/README.md)",
    )
    args = parser.parse_args(argv)
    if not args.report_only:
        if (args.out / "result").exists():
            print(f"{args.out} holds a measurement; --report-only re-reads it", file=sys.stderr)
            return 1
        measure(args.out, args.password)
    if not (args.out / "sensors").is_dir():
        sense(args.out)
    (args.out / "report.md").write_text(report(args.out), "utf-8")
    print(f"report: {args.out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
