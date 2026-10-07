"""One organisation, two teams, built by a function: repeated structure without repeated kinds.

Every workstation is the same kind. Each team's workstations reach their own team's file
server over the ``fs`` tie and the organisation's domain controller over ``dc``, because
each team's group wires them so; the packets cross ``core_router``, the one host that
forwards, which is attached to all three LANs. Nothing is looked up by walking the tree;
``team()`` passes the site in, the way a Terraform module takes its dependencies as inputs.

The sensor sits on a SPAN of the core switch's trunk, so it sees all three VLANs, tagged,
and a routed flow twice: once on each VLAN it crosses.
"""

from tiergen.core.dsl import (
    GroupHandle,
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
from tiergen.core.ir import Segment

Dc = kind(
    "domain_controller",
    serves=[endpoint("kerberos", 88, "tcp"), endpoint("smb", 445, "tcp")],
    platforms=["windows"],
)
Fs = kind("file_server", serves=[endpoint("smb", 445, "tcp")], platforms=["linux"])
# The L3 switch between the team LANs and the core: a host that forwards, nothing more.
Rt = kind("core_router", platforms=["linux"], forwards=True)
Ws = kind(
    "workstation",
    ties=[tie("dc", Dc, "single"), tie("fs", Fs, "single")],
    behaviours=[
        semi_markov(
            "office",
            states=["idle", "ticket", "read"],
            initial=[1.0, 0.0, 0.0],
            transitions=[[0.0, 0.5, 0.5], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]],
            dwell=[
                dist("exponential", [120.0]),
                dist("exponential", [1.0]),
                dist("exponential", [20.0]),
            ],
            action_map={
                "idle": None,
                "ticket": action("kerberos.tgs", "dc", {"spn": "cifs/fs"}),
                "read": action(
                    "smb.read",
                    "fs",
                    {"share": "team", "path": choice(["plan.docx", "notes.txt"], [0.6, 0.4])},
                ),
            },
        )
    ],
    platforms=["windows"],
)
Atk = kind(
    "attacker",
    ties=[tie("victims", Ws, "multiple")],
    behaviours=[
        semi_markov(
            "recon",
            states=["idle", "scan"],
            initial=[1.0, 0.0],
            transitions=[[0.0, 1.0], [1.0, 0.0]],
            dwell=[dist("exponential", [600.0]), dist("exponential", [45.0])],
            action_map={
                "idle": None,
                "scan": action("scan.tcp_syn", "victims", {"ports": "445"}, select="all"),
            },
        )
    ],
    platforms=["linux"],
)

Core = segment("core", "10.30.0.0/24", vlan=10)
Mgmt = segment("mgmt", "10.97.0.0/24", "management")


def team(name: str, site: str, lan: Segment, workstations: int) -> GroupHandle:
    """A team: its own LAN, one file server, some workstations. ``fs`` is wired to the team
    itself by default, since the team holds a file server; ``dc`` has to be said."""
    return group(
        name,
        instances={Fs: 1, Ws: workstations},
        attachments={Fs: [lan], Ws: [lan]},
        wiring={"workstation.dc": site},
        parent=site,
    )


EngNet = segment("eng", "10.31.0.0/24", vlan=20)
SalesNet = segment("sales", "10.32.0.0/24", vlan=30)
Eng = team("eng", "corp", EngNet, workstations=12)
Sales = team("sales", "corp", SalesNet, workstations=8)
Corp = group(
    "corp",
    instances={Dc: 1, Atk: 1, Rt: 1},
    attachments={Dc: [Core], Atk: [Core], Rt: [Core, EngNet, SalesNet]},
    wiring={"attacker.victims": [Eng, Sales]},
)

S = scenario(
    "two_teams",
    groups=[Corp, Eng, Sales],
    bindings={
        Dc: binding(
            host(
                "windows",
                "vm",
                "template:win2022-dc",
                backend="libvirt",
                manifest=resource("two_teams.dc_manifest"),
            ),
            mac_oui="00:15:5d",
        ),
        Fs: binding(
            host("linux", "container", backend="docker"),
            {"smb.serve": {"smb.samba": 1.0}},
            mac_oui="3c:ec:ef",
        ),
        Ws: binding(
            host("windows", "vm", "template:win11-workstation", backend="libvirt"),
            {
                "smb.read": {"smb.windows_native": 1.0},
                "kerberos.tgs": {"smb.windows_native": 1.0},
            },
            mac_oui="00:15:5d",
        ),
        Atk: binding(
            host("linux", "container", backend="docker"),
            {"scan.tcp_syn": {"scan.nmap": 1.0}},
            mac_oui="3c:ec:ef",
        ),
        Rt: binding(host("linux", "container", backend="docker"), mac_oui="3c:ec:ef"),
    },
    topology=topology(
        [Core, EngNet, SalesNet, Mgmt],
        [capture_point("core-span", [Core, EngNet, SalesNet], tagged=True)],
    ),
    egress="none",
    schedule=[at(0, Corp, "start", "office", kind=Ws), at(3600, Corp, "start", "recon", kind=Atk)],
    start="2026-10-05T08:00:00+02:00",
    duration_s=8 * 3600,
    capture_points=["core-span"],
    sensors=[
        sensor(
            "zeek",
            "7.0.11",
            resource("two_teams.zeek"),
            "offline",
            caps=["APP_EVENTS"],
            role="label",
        )
    ],
    seed=3,
)
