"""A Linux virtual machine browsing a container's web server: the two substrates in one run.

The workstation is a libvirt guest running the same agent as a container would, reached
through the QEMU guest agent and attributed by the same eBPF collector running inside it;
the web server is a Docker container. Both sit on the one bridge the Docker backend makes,
where the capture point listens, so the labels tell a guest's connection from a
container's only by the instance. Written inline, like ``linux_slice``, which it mirrors
without the attacker.
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
                "web_get": action(
                    "http.get", "web", {"path": choice(["/", "/news"], [0.8, 0.2])}, select="one"
                ),
            },
        )
    ],
    platforms=["linux"],
)

Lan = segment("lan", "10.40.0.0/24")
Mgmt = segment("mgmt", "10.96.0.0/24", "management")

Lab = group("lab", instances={Ws: 1, Web: 1}, attachments={Ws: [Lan], Web: [Lan]})

S = scenario(
    "vm_slice",
    groups=[Lab],
    bindings={
        Ws: binding(
            host("linux", "vm", backend="libvirt"),
            {"http.get": {"http.httpx": 1.0}},
            mac_oui="52:54:00",
        ),
        Web: binding(
            host("linux", "container", backend="docker"),
            {"http.serve": {"http.nginx": 1.0}},
            mac_oui="3c:ec:ef",
        ),
    },
    topology=topology(
        [Lan, Mgmt], [capture_point("lan-span", Lan)], {"lab/web_server[0]": "10.40.0.80"}
    ),
    egress="none",
    schedule=[at(0, Lab, "start", "browse", kind=Ws)],
    start="2026-10-05T08:00:00+02:00",
    duration_s=3600,
    capture_points=["lan-span"],
    sensors=[
        sensor(
            "zeek",
            "7.0.11",
            resource("vm_slice.zeek"),
            "offline",
            caps=["APP_EVENTS"],
            role="label",
        ),
        sensor(
            "suricata",
            "7.0.7",
            resource("vm_slice.suricata"),
            "offline",
            caps=["APP_EVENTS"],
            role="label",
        ),
    ],
    seed=5,
)
