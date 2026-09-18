"""The ``tiergen`` command. M0 has ``check`` and ``impls list``."""

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from tiergen.check import Diagnostic, run_checks
from tiergen.core.codec import CodecError
from tiergen.core.loader import ScenarioLoadError, load_scenario
from tiergen.core.resources import DirResources
from tiergen.impls._base import load_impls
from tiergen.interfaces.registry import load_sensors

OK, FAILED, UNUSABLE = 0, 1, 2
HEADINGS = (("error", "errors"), ("warning", "warnings"), ("not_computed", "not computed"))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tiergen", description="Site-specific NIDS dataset generation."
    )
    commands = parser.add_subparsers(dest="command", required=True, metavar="command")

    check = commands.add_parser(
        "check",
        help="run the static checks over a scenario",
        description="Run the static checks. Exit status: 0 no errors, 1 errors found, "
        "2 the scenario could not be loaded.",
    )
    check.add_argument("scenario", type=Path, help="scenario.py, or a scenario as IR JSON")
    check.add_argument(
        "--models",
        type=Path,
        metavar="DIR",
        help="resource directory (default: models/ beside the scenario)",
    )
    check.add_argument(
        "--emit-json", type=Path, metavar="PATH", help="also write the scenario's IR as JSON"
    )

    impls = commands.add_parser("impls", help="inspect installed implementations")
    impl_commands = impls.add_subparsers(dest="impls_command", required=True, metavar="subcommand")
    listing = impl_commands.add_parser("list", help="list installed implementations")
    listing.add_argument(
        "--protocol", help="only implementations providing a signature of this protocol"
    )
    listing.add_argument("--platform", choices=("linux", "windows"))
    listing.add_argument("--kind", choices=("primitive", "service", "adapter"))
    return parser


def _check(scenario_path: Path, models: Path | None, emit_json: Path | None) -> int:
    try:
        scenario = load_scenario(scenario_path)
    except (OSError, ScenarioLoadError, CodecError, json.JSONDecodeError) as err:
        print(f"tiergen: cannot load {scenario_path}: {err}", file=sys.stderr)
        return UNUSABLE
    if emit_json is not None:
        emit_json.write_text(json.dumps(scenario.to_json(), indent=2) + "\n", encoding="utf-8")

    resources = DirResources(models if models is not None else scenario_path.parent / "models")
    found = run_checks(scenario, resources, load_impls(), load_sensors())
    _report(scenario.name, found)
    return FAILED if any(d.severity == "error" for d in found) else OK


def _report(name: str, found: list[Diagnostic]) -> None:
    counts: list[str] = []
    for severity, heading in HEADINGS:
        group = [d for d in found if d.severity == severity]
        counts.append(f"{len(group)} {heading}")
        if group:
            print(f"{heading}:")
            for d in group:
                print(f"  {d.check}  {d.path}\n       {d.message}")
    print(f"{name}: {', '.join(counts)}")


def _impls_list(protocol: str | None, platform: str | None, kind: str | None) -> int:
    rows = [
        (d.id, d.kind, ",".join(d.host.platforms), " ".join(d.provides))
        for d in sorted(load_impls().values(), key=lambda d: d.id)
        if (kind is None or d.kind == kind)
        and (platform is None or platform in d.host.platforms)
        and (protocol is None or any(s.startswith(f"{protocol}.") for s in d.provides))
    ]
    if not rows:
        print("no implementations match")
        return OK
    table = [("ID", "KIND", "PLATFORMS", "PROVIDES"), *rows]
    widths = [max(len(row[i]) for row in table) for i in range(3)]
    for row in table:
        padded = [cell.ljust(width) for cell, width in zip(row[:3], widths, strict=True)]
        print("  ".join([*padded, row[3]]))
    return OK


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "check":
        return _check(args.scenario, args.models, args.emit_json)
    return _impls_list(args.protocol, args.platform, args.kind)


if __name__ == "__main__":
    sys.exit(main())
