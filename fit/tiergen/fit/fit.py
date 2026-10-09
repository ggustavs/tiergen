"""``tiergen fit RUN_DIR --sensor NAME --out DIR``, as a function."""

import json
from dataclasses import dataclass
from pathlib import Path

from tiergen.core.addressing import AddressPlan
from tiergen.core.codec import from_json, to_json
from tiergen.core.ir import Action, Scenario
from tiergen.core.program import Program
from tiergen.fit import emit, report
from tiergen.fit.behaviour import Fitted, fit_behaviour
from tiergen.fit.ingest import Labelled, candidates_of, label, read_events
from tiergen.fit.vocabulary import Vocabulary, vocabulary
from tiergen.stats.streams import local_tz

REPORT = "fit-report.md"


class FitError(RuntimeError):
    """The run directory lacks what the fit needs, or the sensor is not one of its."""


@dataclass(frozen=True, slots=True)
class Summary:
    scenario: Scenario
    labelled: Labelled
    fits: list[Fitted]
    out: Path


def _read[T](cls: type[T], path: Path) -> T:
    return from_json(cls, json.loads(path.read_text("utf-8")))


def fit_run(run_dir: Path, sensor: str, out: Path) -> Summary:
    scenario = _read(Scenario, run_dir / "scenario.json")
    names = {s.name for s in scenario.sensors} | {"sim"}
    if sensor not in names:
        raise FitError(f"{sensor!r} is no sensor of {scenario.name}: {', '.join(sorted(names))}")
    plan = _read(AddressPlan, run_dir / "addresses.json")
    programs = [_read(Program, p) for p in sorted(run_dir.glob("program.*.json"))]
    if not programs:
        raise FitError(f"{run_dir}: no programs; was it written by tiergen build?")
    vocab: Vocabulary = vocabulary(programs, plan.addresses)
    labelled = label(read_events(run_dir, sensor), vocab)
    tz = local_tz(scenario.start)
    fits: list[Fitted] = []
    maps: list[dict[str, Action | None]] = []
    resource_names: list[dict[str, str]] = []
    for (kind, behaviour), streams in sorted(labelled.streams.items()):
        candidates = candidates_of(vocab, kind, behaviour)
        order = _state_order(programs, kind, behaviour)
        states = [s for s in order if any(c.state == s for c in candidates)]
        if not states or not any(len(s) for s in streams):
            continue
        fitted = fit_behaviour(kind, behaviour, states, streams, tz)
        action_map = _action_map(programs, kind, behaviour)
        fits.append(fitted)
        maps.append(action_map)
        resource_names.append(emit.write_resources(out, fitted, action_map))
    coverage = {"APP_EVENTS": labelled.app_coverage} if labelled.app_coverage is not None else {}
    emit.write_provenance(out, sensor, coverage)
    fitted_scenario = emit.fitted_scenario(scenario, fits, resource_names, sensor)
    (out / emit.FITTED).write_text(
        json.dumps(to_json(fitted_scenario), indent=2) + "\n", encoding="utf-8"
    )
    (out / REPORT).write_text(
        report.render(scenario.name, sensor, labelled, fits, scenario.start[-6:]), encoding="utf-8"
    )
    return Summary(scenario, labelled, fits, out)


def _state_order(programs: list[Program], kind: str, behaviour: str) -> tuple[str, ...]:
    for p in programs:
        if p.kind == kind:
            for b in p.behaviours:
                if b.name == behaviour:
                    return b.states
    return ()


def _action_map(programs: list[Program], kind: str, behaviour: str) -> dict[str, Action | None]:
    for p in programs:
        if p.kind == kind:
            for b in p.behaviours:
                if b.name == behaviour:
                    return {
                        s: None
                        if a is None
                        else Action(a.signature, a.tie, dict(a.params), a.select)
                        for s, a in b.action_map.items()
                    }
    return {}
