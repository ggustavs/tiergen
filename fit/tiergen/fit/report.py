"""``fit-report.md``: what was fitted from what, and everything that was not."""

from collections.abc import Sequence

from tiergen.fit.behaviour import Fitted
from tiergen.fit.ingest import Labelled


def _matrix(f: Fitted) -> list[str]:
    head = "| from \\ to | " + " | ".join(f.states) + " | n |"
    lines = [head, "|" + "---|" * (len(f.states) + 2)]
    for i, s in enumerate(f.states):
        cells: list[str] = []
        for j in range(len(f.states)):
            p = f.transitions.probabilities[i][j]
            iv = f.transitions.intervals[i][j]
            cells.append("n/a" if p != p else f"{p:.3f} ({iv.low:.2f}, {iv.high:.2f})")
        lines.append(f"| {s} | " + " | ".join(cells) + f" | {f.transitions.row_total(i)} |")
    return lines


def render(
    scenario: str, sensor: str, labelled: Labelled, fits: Sequence[Fitted], tz_name: str
) -> str:
    lines = [
        f"# Fit of {scenario} from sensor {sensor}",
        "",
        "## Method",
        "",
        "The observable chain: a semi-Markov process over the acting states of each behaviour, "
        "a state's dwell being the gap from one of its actions to the instance's next action "
        "(connections of a many-connection action, a scan, within a second are one action), "
        "on the operational clock set by the fitted rate curve (peak 1). Silent states are not "
        "fitted; a scenario written with one is compared through its projection. Transition "
        "rows and the initial distribution carry Wilson intervals; dwell families are chosen "
        "by AIC among exponential, lognormal and Weibull, empirical under five samples.",
        "",
        "## Input",
        "",
        f"- connections: {labelled.connections}, window {labelled.window[0]:.0f} to "
        f"{labelled.window[1]:.0f} ({(labelled.window[1] - labelled.window[0]) / 3600:.1f} h), "
        f"local time {tz_name}",
        "- application events on HTTP connections: "
        + ("not applicable" if labelled.app_coverage is None else f"{labelled.app_coverage:.2f}"),
    ]
    if labelled.unmapped.by_reason:
        lines.append(
            "- unmapped connections: "
            + ", ".join(f"{n} {reason}" for reason, n in labelled.unmapped.by_reason.items())
        )
        for address, n in list(labelled.unmapped.originators.items())[:10]:
            lines.append(f"  - {address}: {n} from an originator no instance has")
    else:
        lines.append("- unmapped connections: none")
    for f in fits:
        lines += [
            "",
            f"## {f.kind} / {f.behaviour}",
            "",
            f"{f.instances} instance(s), {f.events} action(s).",
            "",
            "Initial: "
            + ", ".join(
                f"{s} {p:.2f} ({iv.low:.2f}, {iv.high:.2f})"
                for s, p, iv in zip(f.states, f.initial, f.initial_intervals, strict=True)
            ),
            "",
            *_matrix(f),
            "",
            "| state | family | params | n | mean |",
            "|---|---|---|---|---|",
        ]
        for s, d in zip(f.states, f.dwell, strict=True):
            params = (
                ", ".join(f"{v:.4g}" for v in d.params) if d.family != "empirical" else "samples"
            )
            lines.append(f"| {s} | {d.family} | {params} | {d.n} | {d.mean:.4g} |")
        for note in f.placeholders:
            lines.append(f"- placeholder: {note}")
        unfitted = [str(h) for h, seen in enumerate(f.curve.observed) if not seen]
        lines += [
            "",
            "Rate curve by local hour (peak 1): " + " ".join(f"{v:.2f}" for v in f.curve.values),
            (
                "Hours never observed, filled with the observed mean: " + ", ".join(unfitted)
                if unfitted
                else "Every hour of the day was observed."
            ),
        ]
    return "\n".join(lines) + "\n"
