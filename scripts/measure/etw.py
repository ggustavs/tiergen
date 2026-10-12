"""What the measurement scripts share: Windows' event XML, as tracerpt and wevtutil write it.

An ETW event's header names the process it was logged in, which is the whole point of the
measurements: whether the process that asked for a connection appears beside it.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

NS = "{http://schemas.microsoft.com/win/2004/08/events/event}"


@dataclass
class Event:
    provider: str
    id: int
    task: str
    time: datetime
    pid: int
    activity: str
    data: dict[str, str] = field(default_factory=dict[str, str])


def parse_time(text: str) -> datetime:
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
                parse_time(created.get("SystemTime", "")),
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


def images(
    events: list[Event], logged: list[tuple[int, dict[str, str]]]
) -> tuple[dict[int, str], dict[int, int]]:
    """Image and parent by process id: Kernel-Process's starts within the trace, then, for
    processes that started before it, Sysmon's latest creation before the trace ended. The
    Sysmon log spans the template's earlier boots, whose process ids recur."""
    image, parent = processes(events)
    end = events[-1].time if events else None
    latest: dict[int, str] = {}
    for eid, data in logged:
        if eid != 1 or "ProcessId" not in data:
            continue
        created = parse_time(data["UtcTime"].replace(" ", "T") + "Z") if "UtcTime" in data else None
        if end is not None and created is not None and created > end:
            continue
        latest[int(data["ProcessId"])] = data.get("Image", "?").rsplit("\\", 1)[-1]
    for pid, name in latest.items():
        image.setdefault(pid, name)
    return image, parent
