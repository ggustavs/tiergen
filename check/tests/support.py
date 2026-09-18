"""A small well-formed scenario and the registries to check it against.

Each check's tests break one thing in it. Descriptors are built here rather than loaded
from entry points, so these tests do not depend on which packages are installed.
"""

from dataclasses import replace

from tiergen.check import Diagnostic, run_checks
from tiergen.core import dsl, ir
from tiergen.core.codec import JsonValue
from tiergen.core.resources import DictResources
from tiergen.impls._base import HostRequirements, ImplDescriptor, ServiceTable
from tiergen.interfaces import Capability, SensorDescriptor

IMPLS = {
    d.id: d
    for d in (
        ImplDescriptor(
            "http.cli",
            "1",
            "primitive",
            ("http.get",),
            HostRequirements(("linux", "windows")),
            variants=("a", "b"),
        ),
        ImplDescriptor(
            "scan.raw",
            "1",
            "primitive",
            ("scan.tcp_syn",),
            HostRequirements(("linux",), capabilities=("net_raw",)),
        ),
        ImplDescriptor(
            "http.srv",
            "1",
            "service",
            ("http.serve",),
            HostRequirements(("linux",)),
            service=ServiceTable(
                (ir.Endpoint("http", 80, "tcp"), ir.Endpoint("https", 443, "tcp"))
            ),
        ),
        ImplDescriptor(
            "http.srv80",
            "1",
            "service",
            ("http.serve",),
            HostRequirements(("linux",)),
            service=ServiceTable((ir.Endpoint("http", 80, "tcp"),)),
        ),
    )
}
SENSORS = {
    "rich": SensorDescriptor("rich", ("1.0",), ("offline", "live"), frozenset(Capability)),
    "poor": SensorDescriptor("poor", ("2.0",), ("offline",), frozenset({Capability.APP_EVENTS})),
}
RESOURCES: dict[str, JsonValue] = {
    "cli.transitions": [[0.5, 0.5], [1.0, 0.0]],
    "cli.rate": [1.0 for _ in range(24)],
    "lan.provenance": {
        "sensor": "rich",
        "capabilities_used": ["APP_EVENTS"],
        "coverage": {"APP_EVENTS": 0.9},
    },
}
OPAQUE = frozenset({"lan.topology", "lan.rich", "lan.poor"})


def surf(**changes: object) -> ir.Behaviour:
    parts: dict[str, object] = {
        "states": ["idle", "get"],
        "initial": [1.0, 0.0],
        "transitions": "cli.transitions",
        "dwell": [dsl.dist("exponential", [30.0]), dsl.dist("exponential", [2.0])],
        "rate": "cli.rate",
        "action_map": {"idle": None, "get": dsl.action("http.get", "web")},
    }
    parts.update(changes)
    return dsl.semi_markov("surf", **parts)  # pyright: ignore[reportArgumentType]


def good(behaviour: ir.Behaviour | None = None) -> ir.Scenario:
    srv = dsl.kind("srv", serves=[dsl.endpoint("https", 443, "tcp")], platforms=["linux"])
    cli = dsl.kind(
        "cli",
        ties=[dsl.tie("web", srv, "single")],
        behaviours=[behaviour or surf()],
        platforms=["linux", "windows"],
    )
    return dsl.scenario(
        "good",
        instances={cli: 3, srv: 1},
        bindings={
            cli: dsl.binding(
                dsl.host("windows", "container"),
                {"http.get": {"http.cli:a": 2.0, "http.cli:b": 1.0}},
            ),
            srv: dsl.binding(dsl.host("linux", "container"), {"http.serve": {"http.srv": 1.0}}),
        },
        topology="lan.topology",
        egress="none",
        schedule=[dsl.at(0, cli, "start", "surf"), dsl.at(60, "cli[2]", "set_rate", 0.5)],
        duration_s=3600,
        capture_points=["span0"],
        sensors=[
            dsl.sensor(
                "rich",
                "1.0",
                "lan.rich",
                "offline",
                caps=["APP_EVENTS", "SMB_DIALECT"],
                role="both",
            ),
            dsl.sensor("poor", "2.0", "lan.poor", "offline", caps=["APP_EVENTS"], role="label"),
        ],
        fit_provenance="lan.provenance",
        seed=1,
    )


def run(scenario: ir.Scenario, resources: dict[str, JsonValue] | None = None) -> list[Diagnostic]:
    store = DictResources(RESOURCES if resources is None else resources, OPAQUE)
    return run_checks(scenario, store, IMPLS, SENSORS)


def only(
    check: str, scenario: ir.Scenario, resources: dict[str, JsonValue] | None = None
) -> list[Diagnostic]:
    """The diagnostics of one check, after asserting no other check found an error."""
    found = run(scenario, resources)
    others = [d for d in found if d.check != check and d.severity == "error"]
    assert not others, others
    return [d for d in found if d.check == check]


def cli_kind(s: ir.Scenario) -> ir.ActorKind:
    return s.kinds[0]


def with_kind(s: ir.Scenario, index: int, **changes: object) -> ir.Scenario:
    kinds = list(s.kinds)
    kinds[index] = replace(kinds[index], **changes)  # pyright: ignore[reportArgumentType]
    return replace(s, kinds=tuple(kinds))


def with_binding(s: ir.Scenario, index: int, **changes: object) -> ir.Scenario:
    bindings = list(s.bindings)
    bindings[index] = replace(bindings[index], **changes)  # pyright: ignore[reportArgumentType]
    return replace(s, bindings=tuple(bindings))
