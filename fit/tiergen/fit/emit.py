"""The fit as files: resources in the formats the examples use, the scenario with its
fitted processes pointing at them, and the provenance."""

import json
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from tiergen.core.codec import to_json
from tiergen.core.ir import Action, ActorKind, Behaviour, FitProvenance, Scenario, SemiMarkov
from tiergen.fit.behaviour import Fitted

FITTED = "scenario_fitted.json"
PROVENANCE = "fit_provenance"


def resource_names(f: Fitted) -> dict[str, str]:
    stem = f"{f.kind}.{f.behaviour}"
    return {
        part: f"{stem}.{part}"
        for part in ("states", "initial", "transitions", "dwell", "rate", "action_map")
    }


def write_resources(out: Path, f: Fitted, action_map: dict[str, Action | None]) -> dict[str, str]:
    """Writes one JSON file per resource under ``out`` and returns their names by part."""
    out.mkdir(parents=True, exist_ok=True)
    names = resource_names(f)
    values: dict[str, object] = {
        "states": list(f.states),
        "initial": list(f.initial),
        "transitions": [list(row) for row in f.rows()],
        "dwell": list(f.distributions()),
        "rate": list(f.curve.values),
        "action_map": {s: action_map.get(s) for s in f.states},
    }
    for part, name in names.items():
        (out / f"{name}.json").write_text(
            json.dumps(to_json(values[part]), indent=2) + "\n", encoding="utf-8"
        )
    return names


def fitted_scenario(
    scenario: Scenario, fits: Sequence[Fitted], names: Sequence[dict[str, str]], sensor: str
) -> Scenario:
    """The scenario with each fitted behaviour's process replaced by resource references.
    When ``sensor`` is one of the scenario's, it takes the fit role and the provenance is
    set; a simulation (``sim``) is no sensor, so the scenario then carries no provenance."""
    by_key = {(f.kind, f.behaviour): n for f, n in zip(fits, names, strict=True)}
    kinds: list[ActorKind] = []
    for kind in scenario.kinds:
        behaviours: list[Behaviour] = []
        for b in kind.behaviours:
            n = by_key.get((kind.name, b.name))
            if n is None:
                behaviours.append(b)
                continue
            process = SemiMarkov(n["states"], n["initial"], n["transitions"], n["dwell"], n["rate"])
            behaviours.append(replace(b, process=process, action_map=n["action_map"]))
        kinds.append(replace(kind, behaviours=tuple(behaviours)))
    sensors = tuple(
        replace(s, role="both" if s.role == "label" else "fit") if s.name == sensor else s
        for s in scenario.sensors
    )
    real = any(s.name == sensor for s in scenario.sensors)
    return replace(
        scenario,
        name=f"{scenario.name}_fitted",
        kinds=tuple(kinds),
        sensors=sensors,
        fit_provenance=PROVENANCE if real else None,
    )


def write_provenance(out: Path, sensor: str, coverage: dict[str, float]) -> FitProvenance:
    provenance = FitProvenance(sensor, tuple(sorted(coverage)), coverage)
    (out / f"{PROVENANCE}.json").write_text(
        json.dumps(to_json(provenance), indent=2) + "\n", encoding="utf-8"
    )
    return provenance
