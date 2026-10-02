"""Three Linux hosts on one LAN, all in Docker: the first slice that will actually run.

A workstation browses an intranet web server while an attacker scans the LAN. Everything is
written inline, topology included, to show the builders; only the sensor configurations are
resources. It was not fitted from anything, so it has no fit provenance and both sensors
only label.
"""

from tiergen.core.dsl import (
    action,
    at,
    binding,
    capture_point,
    choice,
    dist,
    endpoint,
    group,
    host,
    kind,
    resource,
    scenario,
    segment,
    semi_markov,
    sensor,
    tie,
    topology,
)

Web = kind("web_server", serves=[endpoint("http", 80, "tcp")], platforms=["linux"])

Ws = kind(
    "workstation",
    ties=[tie("web", Web, "multiple")],
    behaviours=[
        semi_markov(
            "browse",
            states=["idle", "web_get"],
            initial=[1.0, 0.0],
            transitions=[[0.0, 1.0], [0.7, 0.3]],
            dwell=[dist("exponential", [20.0]), dist("exponential", [2.0])],
            action_map={
                "idle": None,
                "web_get": action("http.get", "web", {"path": choice(["/", "/news"], [0.8, 0.2])}),
            },
        )
    ],
    platforms=["linux"],
)

Atk = kind(
    "attacker",
    ties=[tie("targets", Web, "multiple")],
    behaviours=[
        semi_markov(
            "recon",
            states=["idle", "syn_scan"],
            initial=[1.0, 0.0],
            transitions=[[0.0, 1.0], [1.0, 0.0]],
            dwell=[dist("exponential", [300.0]), dist("exponential", [30.0])],
            action_map={
                "idle": None,
                "syn_scan": action("scan.tcp_syn", "targets", {"ports": "1-1024"}),
            },
        )
    ],
    platforms=["linux"],
)

Lan = segment("lan", "10.20.0.0/24")
Mgmt = segment("mgmt", "10.98.0.0/24", "management")

Lab = group(
    "lab", instances={Ws: 1, Web: 1, Atk: 1}, attachments={Ws: [Lan], Web: [Lan], Atk: [Lan]}
)

S = scenario(
    "linux_slice",
    groups=[Lab],
    bindings={
        Ws: binding(
            host("linux", "container", backend="docker"), {"http.get": {"http.httpx": 1.0}}
        ),
        Web: binding(
            host("linux", "container", backend="docker"), {"http.serve": {"http.nginx": 1.0}}
        ),
        # nmap's SYN scan opens raw sockets; Docker can grant a container net_raw.
        Atk: binding(
            host("linux", "container", backend="docker"), {"scan.tcp_syn": {"scan.nmap": 1.0}}
        ),
    },
    topology=topology(
        [Lan, Mgmt], [capture_point("lan-span", Lan)], {"lab/web_server[0]": "10.20.0.80"}
    ),
    egress="none",
    schedule=[at(0, Lab, "start", "browse", kind=Ws), at(600, Lab, "start", "recon", kind=Atk)],
    start="2026-10-05T08:00:00+02:00",
    duration_s=3600,
    capture_points=["lan-span"],
    sensors=[
        sensor(
            "zeek",
            "7.0",
            resource("linux_slice.zeek"),
            "offline",
            caps=["APP_EVENTS"],
            role="label",
        ),
        sensor(
            "suricata",
            "7.0.7",
            resource("linux_slice.suricata"),
            "offline",
            caps=["APP_EVENTS"],
            role="label",
        ),
    ],
    seed=1,
)
