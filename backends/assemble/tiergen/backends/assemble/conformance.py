"""``conformance.md``: a run against its own model.

The run's connections, per sensor, are compared with a simulation of the same IR over the
same length through the calibrated tests of ``tiergen.stats``, host by host, with the run's
timestamps moved onto the scenario's clock so the hours line up; each verdict is printed
beside the power measured at the nearest sample size. Then exactness: for every labelled
invocation whose signature promises a fixed number of connections, whether the sensor
reported that many. A conformance gap is an implementation or infrastructure bug (section
9); the fit, when it runs on the same run, is what says whether the model was recovered.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime

import numpy as np

from tiergen.core.addressing import AddressPlan
from tiergen.core.events import ConnEvent
from tiergen.core.ir import Scenario
from tiergen.core.labels import Label
from tiergen.core.program import Program
from tiergen.core.resolve import Resolver
from tiergen.core.resources import Resources
from tiergen.protocols import SIGNATURES
from tiergen.sim import simulate
from tiergen.stats import Stream, render, report, run_test, service, statistics, streams
from tiergen.stats.calibrate import shipped
from tiergen.stats.streams import local_tz

ROUNDS = 300


@dataclass(frozen=True, slots=True)
class Exactness:
    """Labelled invocations whose signature fixes a connection count, and how many of
    them the sensor reported with exactly that count."""

    checked: int
    exact: int
    off: dict[str, int]
    """Invocation ids with the wrong count, with what the sensor reported."""


def shifted(conns: Iterable[ConnEvent], by: float) -> list[ConnEvent]:
    from dataclasses import replace

    return [replace(c, start=c.start + by) for c in conns]


def agent_addresses(
    programs: Mapping[str, Program], plan: AddressPlan, data: set[str]
) -> list[str]:
    """The data-plane addresses of every instance that runs a behaviour."""
    return sorted(
        a
        for instance, p in programs.items()
        if p.behaviours
        for seg, a in plan.addresses.get(instance, {}).items()
        if seg in data
    )


def exactness(labels: Sequence[Label], signatures: Mapping[tuple[str, str, str], str]) -> Exactness:
    counts = Counter[str]()
    signature_of: dict[str, str] = {}
    for lb in labels:
        counts[lb.key.invocation] += 1
        signature_of[lb.key.invocation] = signatures.get(
            (lb.key.instance, lb.key.behaviour, lb.key.action), lb.signature
        )
    checked = exact = 0
    off: dict[str, int] = {}
    for invocation, n in counts.items():
        promised = SIGNATURES[signature_of[invocation]].shape.connections
        if not isinstance(promised, int):
            continue
        checked += 1
        if n == promised:
            exact += 1
        else:
            off[invocation] = n
    return Exactness(checked, exact, off)


def conformance(
    scenario: Scenario,
    resources: Resources,
    programs: Mapping[str, Program],
    plan: AddressPlan,
    started: float,
    ran_s: float,
    by_sensor: Mapping[str, Sequence[ConnEvent]],
    labels_by_sensor: Mapping[str, Sequence[Label]],
    signatures: Mapping[tuple[str, str, str], str],
    seed: int = 0,
) -> str:
    """The report, as markdown."""
    epoch = datetime.fromisoformat(scenario.start).timestamp()
    hours = ran_s / 3600
    topology = Resolver(resources).topology(scenario)
    data: set[str] = {s.name for s in topology.segments if s.plane == "data"} if topology else set()
    hosts = agent_addresses(programs, plan, data)
    window = (epoch, epoch + ran_s)
    sim = simulate(scenario, resources, seed=scenario.seed + 1 + seed, duration_s=ran_s)
    model: list[Stream] = streams(
        [e for e in sim.events if isinstance(e, ConnEvent)], window, service, hosts=hosts
    )
    tz = local_tz(scenario.start)
    rng = np.random.default_rng(seed)
    calibrations = shipped()
    sections: list[str] = []
    for sensor, conns in sorted(by_sensor.items()):
        observed = streams(shifted(conns, epoch - started), window, service, hosts=hosts)
        results = [
            run_test(name, stat, observed, model, rng, ROUNDS)
            for name, stat in statistics(tz).items()
        ]
        rows = report(results, calibrations, len(hosts), hours)
        text = render(rows, f"{sensor} against the model")
        ex = exactness(labels_by_sensor.get(sensor, ()), signatures)
        text += (
            f"\nExactness: {ex.exact} of {ex.checked} labelled invocation(s) with a fixed "
            "connection count were reported with exactly that count."
        )
        if ex.off:
            text += " Off: " + ", ".join(f"{k} ({v})" for k, v in list(ex.off.items())[:10])
        sections.append(text + "\n")
    head = (
        f"# Conformance of {scenario.name}\n\n"
        f"The run's {ran_s:.0f} s against one simulation of its own IR over the same length, "
        f"{len(hosts)} agent host(s), per sensor. Tests are those of tiergen.stats, "
        f"p-values by host permutation ({ROUNDS} rounds), verdicts at 0.05 beside the power "
        "measured on the simulator at the nearest sample size.\n\n"
    )
    return head + "\n".join(sections)
