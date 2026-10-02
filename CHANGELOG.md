# Changelog

What was built, and where it departed from `nids-gen-dsl-design.md` and why. The design
document describes the project as it stands; this file keeps the history, so the design does
not have to. Entries are per milestone, newest first. Nothing is released yet, so there are
no version numbers.

## M1: vertical slice, mixed platform (in progress)

### Added

- **core**: the data-link layer. **Breaking:** IR JSON written before this does not load.
  `Segment` (one broadcast domain, one prefix, a VLAN id) replaces `Network`; a
  `CapturePoint` observes one or several segments, tagged or not; `ActorKind.forwards` marks
  a router and routes are derived (`tiergen.core.routing`), with two equally short next
  hops an error; the address plan gains hostnames and MACs from a fitted OUI per binding.
  Decision 4.18 has the surveys behind it: segment-centric because that is what a sensor and
  a directory can recover, with what the emulators lack (VLAN, tags, multi-segment capture
  points, fitted MACs, derived paths) because the sensors key on it.
- **core**: the identity chain before any runtime exists. `LabelKey` is what an
  implementation is given, `InvocationRecord` what the agent logs (attribution key,
  interval, outcome, clock stamp); seeds and sampling in `tiergen.core.sampling` make a run
  a function of IR and seed (per-instance streams, sorted-key weighted choice, invocation
  ids `instance/behaviour#n`); `SensorSpec.name` and flow ids keyed by sensor name and
  capture point; `AttributionRecord.instance`; `Context.ties` resolves to `Peer`s with
  served endpoints; `Action.select` for `multiple` ties; `Scenario.start` anchors the rate
  curves; `Binding.credentials` for the Windows path.
- **cli**, **backends/infra**: `tiergen build` writes `routes.json` and one projected program
  per instance (`tiergen.core.program`): behaviours with every resource inlined, parameters
  resolved, implementation choices, ties resolved to peers with addresses and served
  endpoints, routes, hostname, seed. The agent (task 5) reads nothing else. Run manifests
  carry platform, hostname, MACs, routes, forwarding and the bridge name `build` fixes per
  segment; `InfraBackend.up` returns a `RunState` of substrate names and ids, which
  `tiergen infra up` writes as `state.<backend>.json`. The Docker backend names its bridges,
  sets hostnames and MACs, enables forwarding on forwarders and installs routes with
  `ip route add` (hence `NET_ADMIN` on hosts with routes). The default image is a pinned
  Alpine, which carries iproute2, until the agent's image exists. Verified against the daemon:
  `two_teams`' Linux half routes between its team LANs through `core_router`.
- **check**: check 10 holds every wired tie to reachability over the derived routes and
  reports ambiguous next hops; check 9 warns when no active capture point would see a tie's
  traffic; check 16 requires `select` on `multiple` ties; check 13 holds sensor names unique;
  check 12 holds `start` well formed and `start`/`stop` to every targeted kind; check 11
  refuses a group named like a kind its parent holds; check 7 holds a default host's
  implementations to one base image and warns when a binding has no MAC prefix. `two_teams`
  gained `core_router`, VLAN ids and a tagged trunk SPAN.
- **core**: one resolver (`tiergen.core.resolve`) shared by the checker and `build`, so the
  agent never interprets a resource name; one `ImplRef` and one `HostRef` parser.
- **backends/infra**: the Docker backend, the first `InfraBackend`. `tiergen build` now writes a
  run manifest per backend (`manifest.<backend>.json`), built in `backends/infra/_base` from the
  IR, the address plan and the implementation manifests; `tiergen infra up` and `down` drive the
  backends from the run directory. The `InfraBackend` Protocol became `up(manifest)` and
  `down(manifest)`; `platforms()` and `grantable()` duplicated the descriptor and went. Images
  are pulled before anything is created, containers attach to one network at a time so
  interface order is deterministic, and everything is labelled so `down` needs no state.
  docker-py 7.2 with types-docker, behind one facade module checked at basic strictness, as
  z3 was; `scripts/check_stubs.py` keeps the two in step.
  The backend refuses a daemon that runs Windows containers (the Windows CI runner has one),
  since Windows containers are a later task.
- **workspace**: pre-commit hooks run `uv run --frozen`, so a hook never rewrites `uv.lock`.
- **core**: groups. **Breaking:** IR JSON written before this does not load. `Scenario.instances`
  and `Topology.attachments` are gone; a `Group` holds instance counts, data-plane attachments
  and the wiring of every tie of every kind it holds, and groups nest by path. An instance is
  `path/kind[i]`; schedule targets are a group path, `path/kind` or one instance. Wiring is
  explicit: a tie reaches the instances of its target kind in the groups its wiring names, and
  nothing is looked up by walking the tree. Design decision 4.17 has the survey behind it.
  `examples/two_teams` shows a `team()` function building two teams of one set of kinds.
- **core**: `tiergen.core.groups`, the pure functions every consumer shares: paths, instance
  ids, tie targets, schedule-target selection.
- **check**: check 1 holds every tie to its wiring and its multiplicity exactly (`single` is
  one, `optional` at most one, by counting). The old reading, "`single` needs at least one
  instance somewhere", was the most a flat IR allowed. z3-solver is no longer a dependency:
  with explicit wiring there is nothing left for a solver to decide. Check 11 holds group
  paths unique and parents real; check 12 resolves the new target forms.
- **interfaces**, **backends/infra**: `InfraDescriptor`, the hosts a backend offers and the host
  capabilities it can grant each, registered under `tiergen.infra`. `docker` offers Linux
  containers; `libvirt` offers Linux and Windows VMs, which own their kernel, so there is
  nothing to grant. Both are descriptors only so far.
- **check**: check 7's third clause is real. It was `not_computed` in M0 for want of a backend
  to ask. Check 7 also reports a backend that is not installed or does not offer the bound
  platform and host type, which the design had under check 10; it sits better beside the
  other questions about whether a host suits its binding.
- **cli**: `tiergen build`. It checks a scenario and, only if there are no errors, writes a run
  directory that checks on its own: `scenario.json`, `addresses.json`, a copy of `models/`.
  Backend manifests join it when the backends exist.
- **examples**: `linux_slice`, three Linux containers on one LAN, written inline. It is the
  scenario phase A of M1 runs.
- **check**: checks 9 and 10. Check 9 keeps the planes apart: one management network,
  overlapping no data-plane network, and no capture point on it. Check 10 reports whatever
  stops the address plan, overlapping data-plane networks, and kinds left off the data plane.
  Two clauses are `not_computed`: a live sensor's capture interface, which `SensorSpec` does not
  name, and the egress clauses, which need the external destinations `fit` will emit.
  `hq_lan_broken` now makes six mistakes.
- **core**: typed topology and `Host.backend`. **Breaking:** IR JSON written before this does
  not load. `Scenario.topology` was an opaque resource name and is now a `Topology`, inline or
  a resource: networks by CIDR on the data or management plane, which data-plane networks each
  kind joins, capture points, pinned addresses. `Host` names the backend that provides it. M0
  left open whether infrastructure belongs in the IR or in a run configuration beside it; it is
  in the IR, so checks 9, 10 and 7 stay static and the run manifest is the IR alone.
- **core**: `plan_addresses`, the address plan as a function of the IR. The first usable address
  of each network is the gateway's, pins are placed first, everyone else takes the next free
  address in kind then instance order. The checker sees the plan before anything runs, and
  every backend realises the same one. An allocation order is not a fitted parameter, so
  section 18's "no defaults" is not touched.
- **check**: a custom host whose kind serves nothing needs no manifest (check 6). The Windows
  workstation in `hq_lan` is now a libvirt VM, which made the old rule ask for an empty file.
- **core**: action parameters. `Action.params` gives each parameter of the signature a literal or
  a `Choice`, sampled per invocation, inline or through a `ChoiceRef` to a resource. M0 left
  open where an invocation's `path` or `ports` come from, and no primitive can run without it.
  In the IR, so a run is reproducible from IR and seed and `predict` can see what is asked for.
- **core**: the codec decodes a union whose arms share a JSON shape (`int | float`, two
  dataclasses) by trying each in order. `ParamScalar` needed it.
- **check**: check 16, action parameters against the signature. Numbered 16 so that section 8's
  numbers, which commits and tests refer to, stay put.
- **workspace**: a `test-windows` CI job. Section 18 says `core`, `protocols`, `check` and
  `interfaces` run anywhere, and until now nothing tested it.

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
