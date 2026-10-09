"""Five workstations, two web servers and an attacker on one LAN, all in Docker: the
scenario the fit is checked against on a real run.

Each workstation runs one behaviour over three acting states that differ by request path,
so a sensor with ``APP_EVENTS`` tells them apart, with every dwell family once and a daily
rate curve from ``models/``. Five workstations against five simulated ones give the
conformance report enough hosts to relabel (252 ways) for its verdicts to mean something,
which ``linux_slice``'s two could not. The round trip is: run it for two hours, assemble,
fit from Zeek, and compare the fitted resources with these numbers through the projection
(the idle state is silent, so the fit sees the chain over the three acting states).
"""

from tiergen.core.dsl import (
    action,
    at,
    binding,
    capture_point,
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
            "office",
            states=["idle", "web_get", "news", "files"],
            initial=[1.0, 0.0, 0.0, 0.0],
            transitions=[
                [0.0, 0.5, 0.3, 0.2],
                [0.4, 0.2, 0.3, 0.1],
                [0.5, 0.2, 0.1, 0.2],
                [0.6, 0.1, 0.2, 0.1],
            ],
            dwell=[
                dist("exponential", [45.0]),
                dist("exponential", [8.0]),
                dist("lognormal", [2.0, 0.5]),
                dist("weibull", [1.5, 12.0]),
            ],
            rate=resource("office.rate_day"),
            action_map={
                "idle": None,
                "web_get": action("http.get", "web", {"path": "/"}, select="one"),
                "news": action("http.get", "web", {"path": "/news"}, select="one"),
                "files": action("http.get", "web", {"path": "/files"}, select="one"),
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
            initial=[0.0, 1.0],
            transitions=[[0.0, 1.0], [1.0, 0.0]],
            dwell=[dist("exponential", [1800.0]), dist("exponential", [30.0])],
            action_map={
                "idle": None,
                "syn_scan": action("scan.tcp_syn", "targets", {"ports": "1-1024"}, select="all"),
            },
        )
    ],
    platforms=["linux"],
)

Lan = segment("lan", "10.30.0.0/24")
Mgmt = segment("mgmt", "10.97.0.0/24", "management")

Office = group(
    "office",
    instances={Ws: 5, Web: 2, Atk: 1},
    attachments={Ws: [Lan], Web: [Lan], Atk: [Lan]},
)

linux = host("linux", "container", backend="docker")

S = scenario(
    "office_slice",
    groups=[Office],
    bindings={
        Ws: binding(linux, {"http.get": {"http.httpx": 1.0}}, mac_oui="3c:ec:ef"),
        Web: binding(linux, {"http.serve": {"http.nginx": 1.0}}, mac_oui="3c:ec:ef"),
        Atk: binding(linux, {"scan.tcp_syn": {"scan.nmap": 1.0}}, mac_oui="3c:ec:ef"),
    },
    topology=topology([Lan, Mgmt], [capture_point("lan-span", Lan)]),
    egress="none",
    schedule=[
        at(0, Office, "start", "office", kind=Ws),
        at(600, Office, "start", "recon", kind=Atk),
    ],
    start="2026-10-05T08:00:00+02:00",
    duration_s=7200,
    capture_points=["lan-span"],
    sensors=[
        sensor(
            "zeek",
            "7.0.11",
            resource("office_slice.zeek"),
            "offline",
            caps=["APP_EVENTS"],
            role="label",
        ),
        sensor(
            "suricata",
            "7.0.7",
            resource("office_slice.suricata"),
            "offline",
            caps=["APP_EVENTS"],
            role="label",
        ),
    ],
    seed=3,
)
