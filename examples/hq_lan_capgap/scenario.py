"""hq_lan with a fit-versus-label capability gap: check 14 warns, nothing errors.

`fit` ran on Zeek and relied on SMB_DIALECT (see models/hq_lan.fit_provenance.json), which
the Suricata label sensor does not declare. A detector trained on SMB-dialect features
would not see them in a Suricata deployment."""

from tiergen.core.dsl import (
    action,
    at,
    binding,
    dist,
    endpoint,
    host,
    hours,
    kind,
    resource,
    scenario,
    semi_markov,
    sensor,
    tie,
)

Dc = kind(
    "domain_controller",
    serves=[
        endpoint("kerberos", 88, "tcp"),
        endpoint("ldap", 389, "tcp"),
        endpoint("smb", 445, "tcp"),
        endpoint("dns", 53, "udp"),
    ],
    platforms=["windows"],
)
Fs = kind("file_server", serves=[endpoint("smb", 445, "tcp")], platforms=["windows", "linux"])
Web = kind("intranet_web", serves=[endpoint("https", 443, "tcp")], platforms=["linux"])

# The workstation's behaviour is what `fit` would emit: every part is a resource under models/.
Ws = kind(
    "workstation",
    ties=[tie("dc", Dc, "single"), tie("fs", Fs, "multiple"), tie("web", Web, "multiple")],
    behaviours=[
        semi_markov(
            "office",
            states=resource("ws_office.states"),
            initial=resource("ws_office.initial"),
            transitions=resource("ws_office.transitions"),
            dwell=resource("ws_office.dwell"),
            rate=resource("ws_office.rate_week"),
            action_map=resource("ws_office.action_map"),
        )
    ],
    platforms=["windows", "linux"],
)

# The attacker's behaviour is written inline, as an engineer adding it by hand would.
Atk = kind(
    "attacker",
    ties=[tie("dc", Dc, "single"), tie("victim", Ws, "multiple")],
    behaviours=[
        semi_markov(
            "recon",
            states=["idle", "syn_scan"],
            initial=[1.0, 0.0],
            transitions=[[0.0, 1.0], [1.0, 0.0]],
            dwell=[dist("exponential", [600.0]), dist("exponential", [45.0])],
            action_map={"idle": None, "syn_scan": action("scan.tcp_syn", "victim")},
        )
    ],
    platforms=["linux"],
)

S = scenario(
    "hq_lan_capgap",
    instances={Ws: 60, Dc: 1, Fs: 2, Web: 1, Atk: 1},
    bindings={
        # A VM from a template is a custom host: its manifest says what it serves.
        Dc: binding(
            host("windows", "vm", "template:win2022-dc", manifest=resource("hq_lan.dc_manifest"))
        ),
        Ws: binding(
            host("windows", "container"),
            {
                "http.get": {"http.httpx": 1.0},
                "smb.read": {"smb.windows_native": 1.0},
                "kerberos.tgs": {"smb.windows_native": 1.0},
            },
        ),
        # Default hosts serve through the service implementations selected here.
        Fs: binding(host("linux", "container"), {"smb.serve": {"smb.samba": 1.0}}),
        Web: binding(host("linux", "container"), {"http.serve": {"http.nginx": 1.0}}),
        Atk: binding(host("linux", "container"), {"scan.tcp_syn": {"scan.nmap": 1.0}}),
    },
    topology=resource("hq_lan.topology"),
    egress="none",
    schedule=[at(0, Ws, "start", "office"), at(hours(30), Atk, "start", "recon")],
    duration_s=7 * 24 * 3600,
    capture_points=["core-switch-span"],
    sensors=[
        sensor(
            "zeek",
            "7.0",
            resource("hq_lan.zeek"),
            "offline",
            caps=["APP_EVENTS", "TLS_JA4", "HTTP_USER_AGENT", "SSH_STRINGS", "SMB_DIALECT", "X509"],
            role="both",
        ),
        sensor(
            "suricata",
            "7.0.7",
            resource("hq_lan.suricata"),
            "offline",
            caps=["APP_EVENTS", "TLS_JA4", "HTTP_USER_AGENT"],
            role="label",
        ),
    ],
    fit_provenance=resource("hq_lan.fit_provenance"),
    seed=1,
)
