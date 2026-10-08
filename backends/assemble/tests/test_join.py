from tiergen.backends.assemble.join import join, owns
from tiergen.core.events import ConnEvent, ConnState, FiveTuple, SensorFlowId
from tiergen.core.records import AttributionKey, ClockStamp, InvocationRecord, LabelKey
from tiergen.interfaces import AttributionRecord

WS, WEB, ATK, HOST = "10.20.0.2", "10.20.0.80", "10.20.0.3", "10.20.0.1"
INSTANCE_OF = {WS: "lab/workstation[0]", WEB: "lab/web_server[0]", ATK: "lab/attacker[0]"}
SIGNATURES = {
    ("lab/workstation[0]", "browse", "web_get"): "http.get",
    ("lab/attacker[0]", "recon", "syn_scan"): "scan.tcp_syn",
}
BROWSE = FiveTuple(WS, 40112, WEB, 80, "tcp")
PROBE = FiveTuple(ATK, 50000, WEB, 22, "tcp")
MDNS = FiveTuple(HOST, 5353, "224.0.0.251", 5353, "udp")
PHONE_HOME = FiveTuple(WEB, 51000, WS, 9, "tcp")


def conn(
    sensor: str, native: str, five: FiveTuple, start: float, state: ConnState = "closed"
) -> ConnEvent:
    return ConnEvent(
        SensorFlowId(sensor, "lan-span", native),
        five,
        start,
        None,
        None,
        None,
        None,
        None,
        state,
        {},  # type: ignore[arg-type]
    )


def invocation(
    instance: str, behaviour: str, action: str, n: int, principal: str, start: float, end: float
) -> InvocationRecord:
    key = LabelKey(
        "linux_slice", instance, behaviour, action, f"{instance}/{behaviour}#{n}", "x", None, ()
    )
    return InvocationRecord(
        key,
        AttributionKey("linux", principal),
        start,
        end,
        "succeeded",
        ClockStamp(start, 0.0, 0.0),
    )


def seen(
    instance: str, principal: str, five: FiveTuple, start: float, tgid: int = 0
) -> AttributionRecord:
    return AttributionRecord(instance, AttributionKey("linux", principal), five, start, start, tgid)


INVOCATIONS = [
    invocation("lab/workstation[0]", "browse", "web_get", 1, "cgroup:4242", 99.9, 101.0),
    invocation("lab/workstation[0]", "browse", "web_get", 2, "cgroup:4243", 150.0, 151.0),
    invocation("lab/attacker[0]", "recon", "syn_scan", 1, "cgroup:7", 199.0, 230.0),
    invocation("lab/attacker[0]", "recon", "syn_scan", 2, "cgroup:8", 299.0, 330.0),
]
ATTRIBUTION = [
    seen("lab/workstation[0]", "cgroup:4242", BROWSE, 100.0, tgid=31),
    seen("lab/web_server[0]", "cgroup:9", BROWSE, 100.0, tgid=12),  # nginx's accept
    seen("lab/web_server[0]", "cgroup:9", PHONE_HOME, 120.0, tgid=12),  # the service's own
    seen("lab/attacker[0]", "cgroup:7", PROBE, 200.0),  # a raw packet: no process
    seen("lab/attacker[0]", "cgroup:8", FiveTuple(ATK, 50001, WEB, 23, "tcp"), 300.0),
]
CONNECTIONS = [
    conn("zeek", "C1", BROWSE, 100.2),
    conn("zeek", "C2", MDNS, 110.0, "other"),
    conn("zeek", "C3", PHONE_HOME, 120.1, "rejected"),
    conn("zeek", "C4", PROBE, 200.01, "rejected"),
    conn("suricata", "1", BROWSE, 100.2),
    conn("suricata", "2", PROBE, 200.01, "rejected"),
]


def test_connections_are_labelled_through_the_originator_and_the_rest_is_flagged() -> None:
    joined = join(CONNECTIONS, ATTRIBUTION, INVOCATIONS, SIGNATURES, INSTANCE_OF, 1.0)
    assert {
        s: [(lb.flow.native, lb.key.action, lb.signature) for lb in ls]
        for s, ls in joined.labels.items()
    } == {
        "zeek": [("C1", "web_get", "http.get"), ("C4", "syn_scan", "scan.tcp_syn")],
        "suricata": [("1", "web_get", "http.get"), ("2", "syn_scan", "scan.tcp_syn")],
    }
    browse = joined.labels["zeek"][0]
    assert browse.key.invocation == "lab/workstation[0]/browse#1"
    assert browse.outcome == "succeeded"
    assert (browse.principal.principal, browse.observed) == ("cgroup:4242", 100.0)
    assert [
        (f.kind, f.reason, f.at, f.invocation, f.flow.native if f.flow else None)
        for f in joined.flags
    ] == [
        ("unattributed", "no_attribution", 110.0, None, "C2"),
        ("unattributed", "no_invocation", 120.1, None, "C3"),
        ("failed", "no_attribution", 150.0, "lab/workstation[0]/browse#2", None),
        ("failed", "no_connection", 299.0, "lab/attacker[0]/recon#2", None),
    ]
    assert joined.flags[1].five_tuple == PHONE_HOME


def test_the_tolerance_bounds_both_matches() -> None:
    late = [conn("zeek", "C1", BROWSE, 101.5)]
    assert join(late, ATTRIBUTION, INVOCATIONS, SIGNATURES, INSTANCE_OF, 1.0).labels == {}
    assert join(late, ATTRIBUTION, INVOCATIONS, SIGNATURES, INSTANCE_OF, 2.0).labels["zeek"]
    early = seen("lab/workstation[0]", "cgroup:4242", BROWSE, 98.0)
    assert not owns(INVOCATIONS[0], early, 1.0)
    assert owns(INVOCATIONS[0], early, 2.0)


def test_a_pid_principal_matches_the_thread_group_and_nothing_without_one() -> None:
    by_pid = invocation("lab/workstation[0]", "browse", "web_get", 1, "pid:31", 99.9, 101.0)
    assert owns(by_pid, ATTRIBUTION[0], 1.0)
    assert not owns(by_pid, ATTRIBUTION[3], 1.0)  # a raw packet has no thread group
    assert not owns(
        invocation("lab/workstation[0]", "browse", "web_get", 1, "pid:32", 99.9, 101.0),
        ATTRIBUTION[0],
        1.0,
    )


def test_a_record_s_offset_moves_its_interval_onto_the_capture_host() -> None:
    shifted = InvocationRecord(
        INVOCATIONS[0].key,
        INVOCATIONS[0].principal,
        89.9,
        91.0,
        "succeeded",
        ClockStamp(89.9, 0.0, 10.0),
    )
    assert owns(shifted, ATTRIBUTION[0], 1.0)
