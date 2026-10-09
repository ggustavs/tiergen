"""The scenarios the statistics are validated on, and the perturbations that define power.

``office`` is a workstation kind with three acting states, each reaching a server of its
own on a port of its own, so a service mark is an action; with ``idle`` it has a silent
state too. Every dwell family appears once. The perturbations move one transition
probability, scale one dwell, or scale one hour of the rate curve: the effect sizes the
calibration tables are stated at. ``streams_of`` simulates and reduces to streams with
every workstation present, active or not.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass, replace
from datetime import datetime, tzinfo

from tiergen.core.codec import JsonValue
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
    tie,
    topology,
)
from tiergen.core.events import ConnEvent
from tiergen.core.ir import Action, ActorKind, Behaviour, Distribution, Scenario, SemiMarkov
from tiergen.core.resources import DictResources
from tiergen.sim import simulate
from tiergen.stats.streams import Stream, local_tz, streams

START = "2026-10-05T08:00:00+02:00"
RATE = "ws.rate"
STATES = ("web_get", "wiki_get", "api_get")
PORTS = {"web_get": 80, "wiki_get": 8080, "api_get": 9090}
MARKS = {s: f"tcp/{p}" for s, p in PORTS.items()}
WORKSTATION = "workstation"
BEHAVIOUR = "office"


@dataclass(frozen=True, slots=True)
class Harness:
    scenario: Scenario
    resources: dict[str, JsonValue]

    @property
    def tz(self) -> tzinfo:
        return local_tz(self.scenario.start)


def office(
    hosts: int,
    *,
    idle: bool = True,
    rate: Sequence[float] | None = None,
    duration_s: float = 8 * 3600,
    seed: int = 1,
) -> Harness:
    web = kind("web", serves=[endpoint("http", 80, "tcp")], platforms=["linux"])
    wiki = kind("wiki", serves=[endpoint("http", 8080, "tcp")], platforms=["linux"])
    api = kind("api", serves=[endpoint("http", 9090, "tcp")], platforms=["linux"])
    acting = {
        "web_get": action("http.get", "web", {"path": "/"}),
        "wiki_get": action("http.get", "wiki", {"path": "/wiki"}),
        "api_get": action("http.get", "api", {"path": "/api"}),
    }
    dwell = [
        dist("exponential", [10.0]),
        dist("lognormal", [2.0, 0.5]),
        dist("weibull", [1.5, 15.0]),
    ]
    if idle:
        states = ["idle", *STATES]
        initial = [1.0, 0.0, 0.0, 0.0]
        transitions = [
            [0.0, 0.5, 0.3, 0.2],
            [0.4, 0.2, 0.3, 0.1],
            [0.5, 0.2, 0.1, 0.2],
            [0.6, 0.1, 0.2, 0.1],
        ]
        dwell = [dist("exponential", [60.0]), *dwell]
        action_map: dict[str, Action | None] = {"idle": None, **acting}
    else:
        states = list(STATES)
        initial = [1.0, 0.0, 0.0]
        transitions = [[0.2, 0.5, 0.3], [0.4, 0.2, 0.4], [0.5, 0.3, 0.2]]
        action_map = dict(acting)
    ws = kind(
        WORKSTATION,
        ties=[tie("web", web, "single"), tie("wiki", wiki, "single"), tie("api", api, "single")],
        behaviours=[
            semi_markov(
                BEHAVIOUR,
                states=states,
                initial=initial,
                transitions=transitions,
                dwell=dwell,
                action_map=action_map,
                rate=resource(RATE) if rate is not None else None,
            )
        ],
        platforms=["linux"],
    )
    lan = segment("lan", "10.50.0.0/16")
    lab = group(
        "lab",
        instances={ws: hosts, web: 1, wiki: 1, api: 1},
        attachments={ws: [lan], web: [lan], wiki: [lan], api: [lan]},
    )
    linux = host("linux", "container", backend="docker")
    served = {"http.serve": {"http.nginx": 1.0}}
    s = scenario(
        "office",
        groups=[lab],
        bindings={
            ws: binding(linux, {"http.get": {"http.httpx": 1.0}}),
            web: binding(linux, served),
            wiki: binding(linux, served),
            api: binding(linux, served),
        },
        topology=topology([lan], [capture_point("span", lan)]),
        egress="none",
        start=START,
        duration_s=duration_s,
        capture_points=["span"],
        sensors=[],
        schedule=[at(0, lab, "start", BEHAVIOUR, kind=ws)],
        seed=seed,
    )
    resources: dict[str, JsonValue] = {RATE: list(rate)} if rate is not None else {}
    return Harness(s, resources)


def _process(h: Harness) -> tuple[int, int, SemiMarkov]:
    for i, k in enumerate(h.scenario.kinds):
        if k.name == WORKSTATION:
            for j, b in enumerate(k.behaviours):
                if b.name == BEHAVIOUR:
                    return i, j, b.process
    raise KeyError(BEHAVIOUR)


def _with_process(h: Harness, process: SemiMarkov) -> Harness:
    i, j, _ = _process(h)
    k: ActorKind = h.scenario.kinds[i]
    b: Behaviour = replace(k.behaviours[j], process=process)
    k = replace(k, behaviours=(*k.behaviours[:j], b, *k.behaviours[j + 1 :]))
    kinds = (*h.scenario.kinds[:i], k, *h.scenario.kinds[i + 1 :])
    return Harness(replace(h.scenario, kinds=kinds), h.resources)


def perturb_transition(h: Harness, origin: str, target: str, delta: float) -> Harness:
    """Move ``delta`` of probability onto ``origin -> target`` from the row's largest other
    entry, so the row stays stochastic."""
    _, _, p = _process(h)
    assert not isinstance(p.states, str)
    assert not isinstance(p.transitions, str)
    i, j = p.states.index(origin), p.states.index(target)
    row = list(p.transitions[i])
    k = max((c for c in range(len(row)) if c != j), key=lambda c: row[c])
    if row[k] < delta:
        raise ValueError(f"row {origin!r} has no {delta} to move from {p.states[k]!r}")
    row[j] += delta
    row[k] -= delta
    rows = (*p.transitions[:i], tuple(row), *p.transitions[i + 1 :])
    return _with_process(h, replace(p, transitions=rows))


def scale_dwell(h: Harness, state: str, factor: float) -> Harness:
    """Scale the state's dwell: the mean for exponential, the scale for Weibull, ``mu``
    by ``log(factor)`` for lognormal, so the mean scales by ``factor`` in every family."""
    _, _, p = _process(h)
    assert not isinstance(p.states, str)
    assert not isinstance(p.dwell, str)
    i = p.states.index(state)
    d = p.dwell[i]
    assert not isinstance(d.params, str)
    if d.family == "exponential":
        scaled = Distribution(d.family, (d.params[0] * factor,))
    elif d.family == "lognormal":
        scaled = Distribution(d.family, (d.params[0] + math.log(factor), d.params[1]))
    elif d.family == "weibull":
        scaled = Distribution(d.family, (d.params[0], d.params[1] * factor))
    else:
        scaled = Distribution(d.family, tuple(v * factor for v in d.params))
    return _with_process(h, replace(p, dwell=(*p.dwell[:i], scaled, *p.dwell[i + 1 :])))


def scale_rate(h: Harness, hour: int, factor: float) -> Harness:
    """Scale one local hour of the rate curve; the harness needs a curve to begin with."""
    curve = h.resources.get(RATE)
    if not isinstance(curve, list):
        raise ValueError("the harness has no rate curve to scale")
    scaled: list[JsonValue] = [
        float(str(v)) * (factor if i % 24 == hour else 1.0) for i, v in enumerate(curve)
    ]
    return Harness(h.scenario, {**h.resources, RATE: scaled})


def streams_of(h: Harness, seed: int, *, hours: float) -> list[Stream]:
    """The harness simulated for ``hours`` under ``seed``, as one stream per workstation,
    marks by service."""
    sim = simulate(h.scenario, DictResources(h.resources), seed=seed, duration_s=hours * 3600)
    epoch = datetime.fromisoformat(h.scenario.start).timestamp()
    hosts = [
        by_segment["lan"]
        for instance, by_segment in sim.plan.addresses.items()
        if f"/{WORKSTATION}[" in instance
    ]
    conns = [e for e in sim.events if isinstance(e, ConnEvent)]
    return streams(conns, (epoch, epoch + hours * 3600), hosts=hosts)
