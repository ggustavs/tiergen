# Changelog

What was built, and where it departed from `nids-gen-dsl-design.md` and why. The design
document describes the project as it stands; this file keeps the history, so the design does
not have to. Entries are per milestone. Nothing is released yet, so there are no version
numbers.

## M0: core and interfaces (2026-09-20)

Installs and runs without Docker. Nothing generates traffic yet.

### Added

- **core**: the scenario IR as frozen slotted dataclasses; a JSON codec driven by type
  annotations, strict, with the path of the offending value in every error; the common event
  model (`ConnEvent`, `AppEvent`) and the label tuple; the embedded builders; a resource
  resolver over a `models/` directory; a loader for `scenario.py` and IR JSON.
- **protocols**: signatures with traffic shapes for `http`, `dns`, `smb`, `kerberos`, `ssh`
  and `scan`.
- **interfaces**: `Capability`, `CapabilityInfo`, the `Sensor`, `InfraBackend` and
  `AttributionBackend` Protocols, `SensorDescriptor`, and entry-point discovery.
- **backends/sensor**: `zeek` and `suricata`, descriptors only.
- **impls**: `_base` with the `impl.toml` schema, its loader, the registry and the
  `PrimitiveImpl`, `ServiceImpl` and `AdapterImpl` Protocols; `httpx`, `nmap`, `nginx`,
  `samba` and `smbclient_win`, manifests only.
- **check**: checks 1 to 8 and 11 to 15 of section 8, a diagnostics model and a runner.
- **cli**: `tiergen check` and `tiergen impls list`.
- **examples**: `hq_lan`, `hq_lan_capgap`, `hq_lan_broken`.
- **workspace**: uv workspace, pyright strict, ruff, pytest with hypothesis, CI on Python
  3.12 and 3.14.

### Changed from the design sketch

IR (section 7):

- `Action(signature, tie)` replaced the bare signature string in `Behaviour.action_map`.
  Check 2 asks whether a signature is aimed at a tie whose target can answer it, and a
  signature alone does not say which tie.
- `SemiMarkov.states`, `SemiMarkov.dwell`, `Behaviour.action_map`, `ImplSelection.choices` and
  `Scenario.fit_provenance` accept a resource name, as `initial`, `transitions` and `rate`
  already did. The sketch's own DSL example passed `resource(...)` for all five.
- `Scenario.coverage_floor`, default 0.5, is the floor check 15 refers to. The sketch had
  nowhere to put it.
- Nodes have no separate `id`. Names are the ids, and check 11 enforces their uniqueness.

Builders (section 7):

- They import from `tiergen.core.dsl`. `tiergen` is a PEP 420 namespace shared by every
  package and has no module of its own to import from.
- `kind()` returns a handle. An `ActorKind` that holds a dict is unhashable, and the sketch
  used kinds as dictionary keys. `scenario` takes its kinds from the keys of `instances`.
- `semi_markov` requires `initial`. The sketch omitted it, and a parameter is never defaulted.

Signatures and implementations (section 6.1):

- Serving is a signature: `http.serve`, `dns.serve`, `smb.serve`, `kerberos.serve`,
  `ssh.serve`, role `server`. It is what a binding selects a service implementation under.
  The sketch's `internet.serve` had this shape without saying so.
- A client signature lists the endpoint protocols a tie's target may serve, so `http.get` fits
  an `https` endpoint. Scans list none: they need a tie to aim at, not a served endpoint.
- `impl.toml` gained a `[service] served` table and an adapter catalog, so checks 6 and 8 read
  manifests and never import a runtime.
- `PrimitiveImpl.run` is `run(ctx, signature, **params)`. One package provides several
  signatures, so the call has to say which.
- Manifests decode through `tomllib` and the IR's codec, not pydantic. `impls/_base` is in
  every implementation's dependency closure, and a manifest is written by a tool author, not
  at the engineer boundary section 14 reserves pydantic for.

Descriptors (section 4.15):

- Sensors and implementations register static descriptors, separate from their runtime.
  Checks 6, 8, 13 and 14 need to know what exists and what it can do, and M0 ships no runtime.
  "M0 ships no backend" now means no backend runtime; `backends/sensor/zeek`,
  `backends/sensor/suricata` and five `impls/` packages exist as data.

Checks (section 8):

- Check 1 reads multiplicities as ScalaLoci does: `multiple` is zero or more. Only a `single`
  tie constrains instance counts. With fixed counts Z3 decides plain arithmetic; it stays,
  behind a typed facade, because counts are the first thing likely to become ranges.
- Check 5 alone reports a missing or ill-shaped resource. Every other check skips what it
  cannot resolve, so one missing file is one diagnostic.
- Check 6 also pairs kinds with bindings. On a default host an endpoint counts as served only
  if every weighted alternative of some service selection serves it.
- Check 7's third clause, host capabilities grantable by the infrastructure backend, reports
  `not_computed` until a backend exists. It is never a pass.
- Check 12 fixed the target syntax, `kind` or `kind[i]`, and what each operation's argument is.
- Diagnostics have three severities: `error`, `warning`, `not_computed`.

Event model (section 4.3):

- `ConnEvent.state` is a six-value vocabulary each ingest adapter maps into. Duration and the
  byte and packet counters are `None` when the sensor left them unset, never zero. Both are
  provisional until the Zeek and Suricata adapters exist.

Tooling (sections 14 and 18):

- pyright strict, not mypy: better Protocol and namespace-package handling.
- hatchling as build backend. Its editable installs are path-based, which pyright resolves;
  setuptools uses import hooks it cannot follow. Every package ships `py.typed`.
- stdlib dataclasses, not attrs.
- The codec module is `codec.py`, not `json.py`, so it cannot shadow the standard library.
- argparse for the CLI. Two subcommands do not justify a dependency.

### Repository

- Conventional Commits 1.0.0 and Conventional Branch 1.1.0, enforced by commit-check in local
  hooks and in CI. commit-check has no scope allowlist, so `cchk.toml` sets the whole message
  pattern, scopes included. AI co-author trailers are refused.
- `main` is linear and takes pull requests by rebase-merge only.
- Signed commits are not required on `main`. GitHub recreates every commit in a rebase-merge
  and cannot sign what it recreates, so the rule could only ever be met by bypassing it.
- Required approvals are 0. An author cannot approve their own pull request, so 1 is
  unsatisfiable with a single maintainer. Raise it when there is a second.
