"""Write the calibration table: every shipped test at every reference perturbation and
sample size, measured on the harness. Takes a while; ``--seeds`` and ``--sizes`` trade
precision for time.

    uv run python scripts/calibrate.py --seeds 400 --out docs/calibration.md
"""

import argparse
import sys
import time
from pathlib import Path

import numpy as np

from tiergen.stats import Calibration, calibrate, markdown, statistics
from tiergen.stats.calibrate import TABLE, dump
from tiergen.stats.harness import office, perturb_transition, scale_dwell, scale_rate, streams_of

SIZES = ((3, 2.0), (10, 8.0), (20, 12.0))
CURVE = [0.2] * 8 + [1.0] * 10 + [0.2] * 6
PACKAGE_TABLE = Path(__file__).parents[1] / "stats" / "tiergen" / "stats" / TABLE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Write the calibration table of the shipped tests."
    )
    parser.add_argument("--seeds", type=int, default=400)
    parser.add_argument("--rounds", type=int, default=200, help="permutation rounds per test")
    parser.add_argument("--sizes", default=",".join(f"{h}x{t:g}" for h, t in SIZES))
    parser.add_argument("--out", type=Path, default=Path("docs/calibration.md"))
    args = parser.parse_args(argv)
    sizes = [(int(h), float(t)) for h, t in (s.split("x") for s in args.sizes.split(","))]
    rng = np.random.default_rng(2026)
    rows: list[Calibration] = []
    began = time.monotonic()
    for hosts, hours in sizes:
        truth = office(hosts, rate=CURVE)
        alternatives = {
            "transition +0.1": perturb_transition(truth, "web_get", "api_get", 0.1),
            "dwell x1.25": scale_dwell(truth, "web_get", 1.25),
            "rate x1.25 at 10h": scale_rate(truth, 10, 1.25),
        }
        # Every cell at this size reads the same draws, simulated once: seeds 2s and 2s + 1
        # under the truth, seed 2s + 1 under each perturbation.
        null = {seed: streams_of(truth, seed, hours=hours) for seed in range(2 * args.seeds)}
        alt = {
            label: {2 * s + 1: streams_of(a, 2 * s + 1, hours=hours) for s in range(args.seeds)}
            for label, a in alternatives.items()
        }
        print(
            f"{time.monotonic() - began:7.0f} s  simulated {hosts} hosts x {hours:g} h",
            file=sys.stderr,
        )
        for name, statistic in statistics(truth.tz).items():
            for label in alternatives:
                rows.append(
                    calibrate(
                        name,
                        statistic,
                        null.__getitem__,
                        alt[label].__getitem__,
                        perturbation=label,
                        hosts=hosts,
                        hours=hours,
                        seeds=args.seeds,
                        rng=rng,
                        rounds=args.rounds,
                    )
                )
                print(f"{time.monotonic() - began:7.0f} s  {rows[-1]}", file=sys.stderr)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "# Calibration of the shipped tests\n\n"
        f"Measured on the harness scenario (`tiergen.stats.harness.office`) with "
        f"{args.seeds} seed pairs per cell and {args.rounds} permutation rounds, at level "
        "0.05. Type I is the rejection rate between two draws of the same scenario; power "
        "is the rate against the named perturbation. A permutation test's smallest p-value "
        "is about one over the number of ways the hosts can be relabelled, so with 3 hosts "
        "against 3 (20 ways) no test can reject at 0.05 and those rows show it. Regenerate "
        "with `uv run python scripts/calibrate.py`.\n\n"
    )
    args.out.write_text(header + markdown(rows), encoding="utf-8")
    PACKAGE_TABLE.write_text(dump(rows), encoding="utf-8")
    print(f"wrote {args.out} and {PACKAGE_TABLE}: {len(rows)} rows")
    return 0


if __name__ == "__main__":
    sys.exit(main())
