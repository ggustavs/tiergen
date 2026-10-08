"""From records, attribution and each sensor's connections to labels and flags.

Pure over data. A sensor connection is matched to the kernel's view of it by the instance
its originator address belongs to, the 5-tuple, and a start within the tolerance; that
record is matched to the invocation whose principal it was seen from and whose interval
contains it, within the same tolerance. Only the originator's records are consulted: the
originator accounts for the connection, and the responder's accept names a server
process, which is no invocation. Every timestamp is on the capture host's clock: the
collector and the sensors report it, and a record's ``ClockStamp`` moves its interval
onto it.
"""

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field

from tiergen.core.events import ConnEvent, FiveTuple
from tiergen.core.labels import Flag, Label
from tiergen.core.program import Program
from tiergen.core.records import InvocationRecord
from tiergen.interfaces import AttributionRecord

SignatureKey = tuple[str, str, str]
"""Instance, behaviour, state: what a record's key says, and what the IR maps to a signature."""


def signatures(programs: Iterable[Program]) -> dict[SignatureKey, str]:
    """The signature each acting state of each instance runs, from its program."""
    found: dict[SignatureKey, str] = {}
    for program in programs:
        for behaviour in program.behaviours:
            for state, action in behaviour.action_map.items():
                if action is not None:
                    found[(program.instance, behaviour.name, state)] = action.signature
    return found


@dataclass(frozen=True, slots=True)
class Joined:
    """Labels by sensor name, and the flags, in time order."""

    labels: dict[str, list[Label]] = field(default_factory=dict[str, list[Label]])
    flags: list[Flag] = field(default_factory=list[Flag])


def owns(invocation: InvocationRecord, record: AttributionRecord, tolerance_s: float) -> bool:
    """Whether ``record`` was seen from inside ``invocation``: same host, same principal (a
    ``pid`` principal matches the record's thread group), and a start within the interval
    widened by the tolerance."""
    if invocation.key.instance != record.instance:
        return False
    if invocation.principal != record.principal:
        kind, _, n = invocation.principal.principal.partition(":")
        if (
            invocation.principal.platform != record.principal.platform
            or kind != "pid"
            or record.tgid == 0
            or str(record.tgid) != n
        ):
            return False
    offset = invocation.clock.offset
    return (
        invocation.start + offset - tolerance_s
        <= record.start
        <= invocation.end + offset + tolerance_s
    )


def join(
    connections: Iterable[ConnEvent],
    attribution: Iterable[AttributionRecord],
    invocations: Iterable[InvocationRecord],
    signatures: Mapping[SignatureKey, str],
    instance_of: Mapping[str, str],
    tolerance_s: float,
) -> Joined:
    """``instance_of`` maps every planned address to its instance; an originator outside it
    is the substrate or the world, and its connections are unattributed."""
    records = list(attribution)
    by_flow: dict[tuple[str, FiveTuple], list[int]] = defaultdict(list)
    by_host: dict[str, list[int]] = defaultdict(list)
    for i, record in enumerate(records):
        by_flow[(record.instance, record.five_tuple)].append(i)
        by_host[record.instance].append(i)
    ran = list(invocations)
    by_instance: dict[str, list[InvocationRecord]] = defaultdict(list)
    for invocation in ran:
        by_instance[invocation.key.instance].append(invocation)
    owner: dict[int, InvocationRecord | None] = {}

    def owner_of(i: int) -> InvocationRecord | None:
        if i not in owner:
            record = records[i]
            owner[i] = next(
                (v for v in by_instance.get(record.instance, ()) if owns(v, record, tolerance_s)),
                None,
            )
        return owner[i]

    joined = Joined()
    seen: set[int] = set()
    for conn in connections:
        instance = instance_of.get(conn.five_tuple.orig_addr)
        near = (
            [
                i
                for i in by_flow.get((instance, conn.five_tuple), ())
                if abs(records[i].start - conn.start) <= tolerance_s
            ]
            if instance is not None
            else []
        )
        if not near:
            joined.flags.append(
                Flag(
                    "unattributed",
                    "no_attribution",
                    conn.start,
                    flow=conn.flow,
                    five_tuple=conn.five_tuple,
                )
            )
            continue
        i = min(near, key=lambda i: abs(records[i].start - conn.start))
        seen.add(i)
        invocation = owner_of(i)
        if invocation is None:
            joined.flags.append(
                Flag(
                    "unattributed",
                    "no_invocation",
                    conn.start,
                    flow=conn.flow,
                    five_tuple=conn.five_tuple,
                )
            )
            continue
        assert instance is not None
        key = invocation.key
        joined.labels.setdefault(conn.flow.sensor, []).append(
            Label(
                conn.flow,
                key,
                signatures[(instance, key.behaviour, key.action)],
                invocation.outcome,
                records[i].principal,
                records[i].start,
            )
        )
    for invocation in ran:
        mine = [
            i
            for i in by_host.get(invocation.key.instance, ())
            if owns(invocation, records[i], tolerance_s)
        ]
        at = invocation.start + invocation.clock.offset
        if not mine:
            joined.flags.append(
                Flag("failed", "no_attribution", at, invocation=invocation.key.invocation)
            )
        elif not any(i in seen for i in mine):
            joined.flags.append(
                Flag("failed", "no_connection", at, invocation=invocation.key.invocation)
            )
    joined.flags.sort(
        key=lambda f: (
            f.at,
            f.kind,
            f.reason,
            f.invocation or "",
            (f.flow.sensor, f.flow.capture_point, f.flow.native) if f.flow else ("", "", ""),
        )
    )
    return joined
