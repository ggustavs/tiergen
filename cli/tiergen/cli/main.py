"""The ``tiergen`` command: ``check``, ``build``, ``infra up`` and ``down``, ``capture start``
and ``stop``, ``impls list``."""

import argparse
import json
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path

from tiergen.backends.infra._base import build_manifests
from tiergen.check import Diagnostic, run_checks
from tiergen.check.context import Context
from tiergen.core.addressing import plan_addresses
from tiergen.core.codec import CodecError, from_json, to_json
from tiergen.core.ir import Scenario
from tiergen.core.loader import ScenarioLoadError, load_scenario
from tiergen.core.program import build_programs, programs_by_file
from tiergen.core.resolve import Resolver
from tiergen.core.resources import DirResources
from tiergen.core.routing import plan_routes
from tiergen.impls._base import load_impls
from tiergen.interfaces import BackendError, RunManifest
from tiergen.interfaces.registry import load_infra, load_infra_backends, load_sensors
from tiergen.protocols import SIGNATURES
from tiergen.runtime.capture import dumpcap, offsets, points

SERVERS = frozenset(s.id for s in SIGNATURES.values() if s.role == "server")

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

    build = commands.add_parser(
        "build",
        help="check a scenario and write its run directory",
        description="Check a scenario and, if it has no errors, write a self-contained run "
        "directory: the IR, the address plan, and a copy of the resources. Exit status as "
        "for check; nothing is written when there are errors.",
    )
    build.add_argument("scenario", type=Path, help="scenario.py, or a scenario as IR JSON")
    build.add_argument(
        "--out", type=Path, required=True, metavar="DIR", help="run directory to create"
    )
    build.add_argument(
        "--models",
        type=Path,
        metavar="DIR",
        help="resource directory (default: models/ beside the scenario)",
    )

    infra = commands.add_parser("infra", help="bring a built run's hosts up or down")
    infra_commands = infra.add_subparsers(dest="infra_command", required=True, metavar="subcommand")
    for verb, text in (
        ("up", "create the run's networks and hosts and start them"),
        ("down", "remove them"),
    ):
        sub = infra_commands.add_parser(verb, help=text)
        sub.add_argument("run_dir", type=Path, help="a directory written by tiergen build")

    capture = commands.add_parser("capture", help="capture at a running run's capture points")
    capture_commands = capture.add_subparsers(
        dest="capture_command", required=True, metavar="subcommand"
    )
    for verb, text in (
        ("start", "start dumpcap at every capture point, over the run's bridges"),
        ("stop", "stop them, insert the tags of tagged points, write capture.json"),
    ):
        sub = capture_commands.add_parser(verb, help=text)
        sub.add_argument("run_dir", type=Path, help="a directory tiergen infra up brought up")

    impls = commands.add_parser("impls", help="inspect installed implementations")
    impl_commands = impls.add_subparsers(dest="impls_command", required=True, metavar="subcommand")
    listing = impl_commands.add_parser("list", help="list installed implementations")
    listing.add_argument(
        "--protocol", help="only implementations providing a signature of this protocol"
    )
    listing.add_argument("--platform", choices=("linux", "windows"))
    listing.add_argument("--kind", choices=("primitive", "service", "adapter"))
    return parser


def _load(scenario_path: Path) -> Scenario | None:
    try:
        return load_scenario(scenario_path)
    except (OSError, ScenarioLoadError, CodecError, json.JSONDecodeError) as err:
        print(f"tiergen: cannot load {scenario_path}: {err}", file=sys.stderr)
        return None


def _models(scenario_path: Path, models: Path | None) -> Path:
    return models if models is not None else scenario_path.parent / "models"


def _dump(value: object, path: Path) -> None:
    path.write_text(json.dumps(to_json(value), indent=2) + "\n", encoding="utf-8")


def _check(scenario_path: Path, models: Path | None, emit_json: Path | None) -> int:
    scenario = _load(scenario_path)
    if scenario is None:
        return UNUSABLE
    if emit_json is not None:
        _dump(scenario, emit_json)
    resources = DirResources(_models(scenario_path, models))
    found = run_checks(scenario, resources, load_impls(), load_sensors(), load_infra())
    _report(scenario.name, found)
    return FAILED if any(d.severity == "error" for d in found) else OK


def _build(scenario_path: Path, models: Path | None, out: Path) -> int:
    scenario = _load(scenario_path)
    if scenario is None:
        return UNUSABLE
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        print(f"tiergen: {out} exists and is not an empty directory", file=sys.stderr)
        return UNUSABLE

    source = _models(scenario_path, models)
    resources = DirResources(source)
    impls, sensors, infra = load_impls(), load_sensors(), load_infra()
    found = run_checks(scenario, resources, impls, sensors, infra)
    _report(scenario.name, found)
    if any(d.severity == "error" for d in found):
        print(f"tiergen: {scenario.name} has errors; nothing written", file=sys.stderr)
        return FAILED

    # No errors, so check 5 resolved the topology and check 10 found the plan complete.
    topology = Context(scenario, resources, impls, sensors, infra, SIGNATURES).topology()
    assert topology is not None
    plan, _ = plan_addresses(scenario, topology)
    routes, _ = plan_routes(scenario, topology, plan)
    manifests = build_manifests(scenario, topology, plan, routes, impls, resources)
    programs = programs_by_file(
        build_programs(scenario, topology, plan, routes, Resolver(resources), SERVERS)
    )

    out.mkdir(parents=True, exist_ok=True)
    _dump(scenario, out / "scenario.json")
    _dump(plan, out / "addresses.json")
    _dump(routes, out / "routes.json")
    for backend, manifest in manifests.items():
        _dump(manifest, out / f"manifest.{backend}.json")
    for name, program in programs.items():
        _dump(program, out / name)
    if source.is_dir():
        shutil.copytree(source, out / "models")
    written = [
        "scenario.json",
        "addresses.json",
        "routes.json",
        *(f"manifest.{b}.json" for b in manifests),
        f"{len(programs)} program files",
    ]
    if source.is_dir():
        written.append("models/")
    print(f"wrote {out}: {', '.join(written)}")
    return OK


def _infra(verb: str, run_dir: Path) -> int:
    paths = sorted(run_dir.glob("manifest.*.json"))
    if not paths:
        print(
            f"tiergen: {run_dir} holds no manifest; was it written by tiergen build?",
            file=sys.stderr,
        )
        return UNUSABLE
    manifests = [from_json(RunManifest, json.loads(p.read_text(encoding="utf-8"))) for p in paths]
    backends = load_infra_backends(only={m.backend for m in manifests})
    missing = sorted({m.backend for m in manifests} - set(backends))
    if missing:
        print(
            f"tiergen: no runtime installed for backend(s): {', '.join(missing)}", file=sys.stderr
        )
        return UNUSABLE
    try:
        for manifest in manifests:
            backend = backends[manifest.backend]
            if verb == "up":
                _dump(backend.up(manifest, run_dir), run_dir / f"state.{manifest.backend}.json")
            else:
                backend.down(manifest)
                (run_dir / f"state.{manifest.backend}.json").unlink(missing_ok=True)
            print(f"{manifest.backend}: {verb} {manifest.run}, {len(manifest.hosts)} host(s)")
    except BackendError as err:
        print(f"tiergen: {err}", file=sys.stderr)
        return UNUSABLE
    return OK


def _capture(verb: str, run_dir: Path) -> int:
    out = run_dir / "capture"
    try:
        if verb == "start":
            run = points.load_run(run_dir)
            found = points.capture_points(run.scenario, run.topology, run.bridges)
            state = dumpcap.start(run.scenario.name, found, out)
            offsets.write_offsets(out, offsets.offsets(run.states))
            for c in state.captures:
                print(f"{c.point}: {', '.join(c.bridges)} -> capture/{c.file}")
        else:
            state = dumpcap.stop(out)
            for c in state.captures:
                tagged = state.tagged_packets.get(c.point)
                suffix = f", {tagged} packet(s) tagged" if tagged is not None else ""
                print(f"{c.point}: capture/{c.file}{suffix}")
    except (OSError, CodecError, points.CaptureError) as err:
        print(f"tiergen: {err}", file=sys.stderr)
        return UNUSABLE
    return OK


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
    if args.command == "build":
        return _build(args.scenario, args.models, args.out)
    if args.command == "infra":
        return _infra(args.infra_command, args.run_dir)
    if args.command == "capture":
        return _capture(args.capture_command, args.run_dir)
    return _impls_list(args.protocol, args.platform, args.kind)


if __name__ == "__main__":
    sys.exit(main())
