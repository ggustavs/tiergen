# tiergen: site-specific NIDS dataset generation from a multi-tier DSL

Working name `tiergen` (placeholder). Status: design, nothing implemented. Version 3, September 2026.

This file is the project's memory. It records decisions and their rationale so later work (mine or Claude Code's) does not relitigate them without new evidence. *open* marks undecided items, *sketch* marks illustrative material that will change.

---

## 1. Purpose

Produce labelled network intrusion detection datasets for a specific network: the one the user operates, a small enterprise LAN with Active Directory as the first concrete target. Success means a detector trained on the generated data works when deployed on that network, with a benign false-positive rate the user can measure against real traffic and drive down by iterating on the model. Generalisation to arbitrary networks is not a goal.

The tool is for security engineers, not PL researchers. The DSL is the means; the workflow in section 3 is the product.

Inputs: logs from whatever passive sensor the network already runs (Zeek, Suricata, or another sensor behind the same interface), collected over weeks, plus what the engineer knows about the network.

Outputs, per run:
- pcaps from declared capture points
- for each configured sensor, its logs over the generated traffic, produced by the same sensor version and configuration the network runs
- labels keyed by the sensor's own flow and event identity (Zeek `conn.uid` and per-protocol log entries; Suricata `flow_id` and app-layer events), one label set per configured sensor
- a fidelity report comparing generated traffic to the real network at the sensor-event level
- a conformance report comparing the run to its own model
- flagged events: primitives with no observed traffic, traffic with no attribution
- a reproducibility manifest: image digests, implementation and sensor versions, seeds, and the IR

Guarantees:
1. Every label is correct by construction (emitted when a primitive runs) and confirmed by kernel-level attribution after capture. Unconfirmed means flagged, never defaulted.
2. A run's statistics are predicted before it executes and compared to the target network's real statistics before any host starts.
3. Extension is declarative description plus small implementation packages. No hand-written orchestration, no label glue.
4. All captured traffic comes from real protocol implementations on hosts whose platform (Linux container, Windows container, Linux or Windows VM) is chosen per actor.

---

## 2. Why the existing tooling does not do this

- **DetGen**: exact labels through container isolation; no interleaving, no shared hosts, no topology, hand-written Compose per scenario, cannot be pointed at a network.
- **ID2T**: attacks injected into a background pcap; the background is unlabelled and its errors carry over; nothing about the background is modelled.
- **GHOSTS**: realistic user simulation on real Windows hosts; no flow labels; uncalibrated timing; heavy to run.
- **CICIDS2017/2018, UNSW-NB15**: generic "representative" networks from unreleased profile systems, with documented labelling and flow-construction errors (Engelen et al. 2021, Flood et al. 2024). Flows reconstructed by CICFlowMeter, which no production network runs, so the flow definition in the dataset matches no deployed sensor.
- **Learned generators** (NetShare, NetDiffusion): marginals without session semantics.
- **Volume generators** (TRex, MoonGen, D-ITG): no semantics, no labels.

Common defects: none targets a specific network; none defines flows the way the network's own sensor defines them; none predicts what it will produce; none verifies its labels.

No prior work applies multi-tier or choreographic programming to this problem (searched September 2026). The nearest analogue is motion session types: choreographic types over real-world motion primitives on ROS, the same move as traffic primitives over real tools.

---

## 3. The workflow

Each step is a CLI subcommand. The engineer stays in control at the describe step; the rest is mechanical.

1. **collect** (helper, optional). A sensor configuration and a deployment file for a tap or span port, for whichever sensor the network uses. At least two full weeks to cover weekday and weekend cycles. The sensor's exact version and configuration are captured here and reused unchanged in generation, so real and generated traffic are read by the same instrument.
2. **fit** `tiergen fit <sensor-logs> --sensor zeek --out models/`. Reads the sensor's logs through its ingest adapter into the common event model (section 4.3), then: host inventory, role clustering into proposed actor kinds, behaviour model per role, implementation mix per role, service inventory, topology and address plan, diurnal rate curves, external-destination inventory. Emits `scenario_proposed.py`, resources under `models/`, and `fit-report.md` listing everything it could not map. Section 11.
3. **describe**. The engineer edits the scenario: confirms and names kinds, chooses bindings (default container, custom image, Windows container, VM), sets egress policy, adds attack schedules. Section 7.
4. **check** and **predict**. Static checks (section 8), then predicted sensor-level statistics from the scenario's denotation and a fidelity report against the real logs, before anything runs (section 9). Iterate until acceptable.
5. **build** `tiergen build S --out run1/`. Infra manifests, per-host projected programs, sensor configuration, attribution configuration, label schema.
6. **run** `tiergen run run1/`. Hosts up, agents started, clock sync verified, capture started, schedule executed, logs collected.
7. **assemble** `tiergen assemble run1/`. Every configured sensor over the pcaps, attribution join, per-sensor labels, conformance and fidelity reports, flagged events, manifest.
8. **evaluate** (helper). Train reference detectors on the generated data, test on held-out real logs from the target network (benign FP rate) and on generated attacks. Section 13.
9. Iterate on models, bindings and schedules until fidelity and FP rate are acceptable. Re-fit when the network changes.

---

## 4. Decisions

Each entry: decision, then rationale. Change only with a dated note here.

### 4.1 Site-specific target, measured fidelity

Realism is measured against the target network's own sensor logs, not asserted. The fidelity report (section 9) is the arbiter of every realism decision. This turns "is the generator realistic" into a table of metrics with user-set thresholds.

### 4.2 The deployed sensor defines flows and events; tiergen never reconstructs them

Flows and application events are whatever the network's configured sensor emits. tiergen never builds its own flow abstraction (no CICFlowMeter-style reconstruction anywhere). Labels attach to the sensor's native identity: a connection id and, where the sensor emits per-request or per-operation records, those sub-connection entries. The same sensor version and configuration run on the real network and on the generated traffic, so fit, prediction, fidelity and the dataset all speak one schema. This is what makes a label mean the same thing in training as in deployment.

### 4.3 Sensors: required core plus declared capabilities

Every sensor extracts a different set of fields and links them to a flow differently. The interface handles this by capability negotiation, not by a lowest common denominator. Defining the common event model as the intersection of all sensors would throw away Zeek's richness; defining it as the union would make `fit` and `fidelity` reach into sensor-native fields and the abstraction would leak. Instead: a required core that the tool cannot run without, plus typed optional capabilities a sensor advertises and consumers query before use, plus raw passthrough that no core consumer may read.

**Required core.** `ConnEvent`: a sensor-native connection id, the 5-tuple, start and duration, byte and packet counts per direction, and a connection state. This is the floor: attribution joins on 5-tuple and interval, labels key on the connection id, and the connection-rate and byte-distribution fidelity metrics need exactly these. A pure flow exporter (NetFlow v5, basic IPFIX) meets the floor and nothing more, and the tool still produces a correct, coarse dataset (connection-level labels, no sub-connection granularity). A sensor that cannot meet the floor is rejected at config time, not mid-run.

**Declared capabilities.** Everything above the floor is a named capability the sensor advertises, each a typed schema plus a measured coverage claim, not a boolean. `APP_EVENTS` (per-request or per-operation records under a connection, which is what makes sub-connection labels possible) and per-protocol fingerprint capabilities (`TLS_JA4`, `TLS_JA3`, `HTTP_USER_AGENT`, `SSH_STRINGS`, `SMB_DIALECT`, `X509`, extensible). Coverage is the fraction of applicable events on which the sensor actually populates the field, measured at fit time from the real logs: two sensors can both nominally emit JA4 while differing in how often it is present, and `fit` needs to know whether a fingerprint distribution is trustworthy or sparse.

**Typed passthrough with provenance.** Each event keeps its raw sensor record. Nothing in `core`, `fit` or `fidelity` may read it; it exists so sensor-specific analysis or a future capability can be written without re-ingesting, and so nothing is silently discarded. The rule that prevents leaks: any field a consumer depends on must first be promoted to a declared capability. Reaching into passthrough then shows up in review as a bypass of the capability query.

The two operational sides:

- **ingest**: run the sensor over pcaps (offline) or read its live logs; emit `ConnEvent` always, `AppEvent` iff `APP_EVENTS`, with capability fields populated per what the sensor declares. Used by `fit` and `fidelity`.
- **label**: given attribution (invocation to 5-tuple, interval, host) and the sensor's events over the generated pcaps, join to labels keyed by the sensor's connection id and, where `APP_EVENTS` is present, sub-connection event index. Attribution is sensor-independent kernel truth; each sensor's join is a separate mapping into its own id space, so one run can carry Zeek-keyed and Suricata-keyed labels.

Every consumer degrades explicitly against the capability set and records the degradation as a gap, never a silent default (section 4.7 for `fit`, section 9 for `fidelity`). A missing capability makes a metric "not computed," which is different from zero.

**Cross-sensor consistency.** Capability negotiation is not only per sensor. If the fit sensor is richer than a configured label sensor, the model can encode features the deployed sensor cannot produce, and a detector trained on them is useless in deployment. The checker warns when `fit` used a capability that a label sensor lacks (section 8). This is the concrete form of the earlier "is Suricata rich enough" question: it is not yes or no. Suricata declares fewer or lower-coverage capabilities than Zeek for some protocols; `fit` degrades and says so; and fitting from Zeek at Zeek's resolution when the deployment runs Suricata is the actual bug, which the cross-sensor check catches.

Zeek and Suricata are the first two implementations. Zeek maps `conn.log` to `ConnEvent`, declares `APP_EVENTS` from `http`/`ssl`/`ssh`/`smb_*`/`kerberos`/`ntlm`/`dce_rpc`/`rdp`, and declares the fingerprint capabilities its packages provide. Suricata maps flow records to `ConnEvent` (by `flow_id`), declares `APP_EVENTS` from its app-layer events, and declares the fingerprint capabilities present in `eve.json`. A future flow-only exporter declares neither `APP_EVENTS` nor fingerprints and still works at the floor.

Interface, *sketch* (in `interfaces/`, defined M0, no implementations):

```python
from enum import Enum, auto
from typing import Protocol, Mapping, Iterator
from dataclasses import dataclass

class Capability(Enum):
    APP_EVENTS = auto()           # per-request/per-operation records under a connection
    TLS_JA4 = auto(); TLS_JA3 = auto()
    HTTP_USER_AGENT = auto()
    SSH_STRINGS = auto()
    SMB_DIALECT = auto()
    X509 = auto()
    # extends without touching ConnEvent or any core consumer

@dataclass(frozen=True, slots=True)
class CapabilityInfo:
    schema: str                   # reference to the typed shape this adds to AppEvent
    coverage: float               # fraction of applicable events populated, measured at fit time

class Sensor(Protocol):
    id: str                       # "zeek" | "suricata" | ...
    version: str
    def capabilities(self) -> Mapping[Capability, CapabilityInfo]: ...
    def ingest(self, native_logs) -> Iterator["Event"]: ...   # ConnEvent always; AppEvent iff APP_EVENTS
    def flow_key(self, event: "Event") -> "SensorFlowId": ...  # the sensor's native connection id
```

Coverage in `CapabilityInfo` starts as the sensor's own claim and is overwritten with the value `fit` measures on the real logs, so downstream consumers see the empirical number for this network, not a nominal one.

### 4.4 Multi-tier placement, not choreographies

Choreographies fix one global control flow with communicated selections; independent stochastic local choices, dwell distributions and partial failure have no natural home, and the deadlock-freedom they guarantee concerns a control plane that here is out-of-band. (Kuper, ICFP 2026, same verdict.) Placement types keep what matters: every tier-boundary crossing is a typed, compiler-known event, so labels by construction survive. The conformance oracle is statistical (the run should be a trace of the product process), which suits stochastic actors.

### 4.5 Two planes

Coordination between actors is the traffic and is produced by real implementations. The tool's own runtime (agents, scheduler, log collection) lives on a management network that is never captured. Static check: capture points are on data-plane networks only. If runtime transport ever appears in a capture, the dataset represents the runtime.

### 4.6 Declarative core as data, Python leaves as code

Actor kinds, ties, interfaces, behaviours, bindings, schedules, topology and sensor configuration are data. Python code exists only in implementation packages (section 6.1) and in the action-to-signature mapping. Consequences: the checker runs over a finite first-order IR; one behaviour description gets several interpretations by swapping effect handlers (execute, trace for statistics, export to a model checker, enumerate for labels); the IR is JSON and any tool can consume it.

### 4.7 Behaviours are stochastic processes fitted from the target's logs

Default family: semi-Markov over an action vocabulary derived from the common event model, with time-of-day rate multipliers. The vocabulary's resolution is set by the fit sensor's capabilities (section 11): with `APP_EVENTS`, the fine per-protocol vocabulary; without it, connection-level classes by service, port, size and direction. Fits from aggregate per-role statistics are acceptable; the goal is a usable dataset for this network, not a per-individual replica, and the fidelity report says whether a fit is good enough. The process family is behind an interface (`next_action`, `dwell`, `rate(t)`), so HMMs or session-structured models can replace the default.

### 4.8 Hosts are heterogeneous and first class

An actor's host has a platform: Linux container, Windows container (Hyper-V isolation for kernel separation), Linux VM, Windows VM. For an AD LAN, Windows is central (DC, workstations, Kerberos, SMB, NTLM), so Windows is present from the first runnable slice, not deferred. Nothing in `core/` may assume Linux. Attribution has a backend per platform (eBPF on Linux, ETW or Sysmon on Windows). The Linux-container default is documented as a transport-layer monoculture (one kernel, one TCP stack shared by co-located actors); the realism budget for hosts that matter goes to Windows containers or VMs.

### 4.9 Substrate is agnostic behind an interface; Docker and libvirt first

The infra backend is an interface. Docker (Linux and Windows daemons) and libvirt (Linux and Windows VMs) are the first two implementations, because their per-node platform cost is lowest and together they cover the AD LAN slice: containers for cheap dense actors, VMs for the DC and any actor needing a real kernel or transport fidelity. Kubernetes is a possible later backend and is deliberately not early: on k8s you do not own the node kernel through the API, so eBPF attribution, `cgroup_skb` for raw-socket scanners, and promiscuous capture need privileged DaemonSets and CNI cooperation, managed control planes restrict exactly that, and Windows nodes are a weaker story. Its capacity scaling is real but is not the bottleneck at a few hundred hosts. For a multi-node backend, Nomad is the lighter fit to evaluate before k8s, because it schedules containers and VMs as equals and does not assume it owns the network. The cost asymmetry is a property of the substrates, not of the tool; only the infra-backend package depends on the choice.

### 4.10 Implementation diversity is fitted, not guessed

Fingerprints in the common event model (JA4 from TLS events, user agent from HTTP, client and server strings from SSH, dialects and OS strings from SMB and NTLM) give the real client and server mix. `fit` maps these to available implementation variants and their weights; unmapped fingerprints are listed in the fit report as gaps to fill with new implementation packages. The chosen implementation and variant go into every label, so diversity is recoverable per connection.

### 4.11 Labels are expected until confirmed

A label is emitted when a primitive executes and becomes confirmed only when attribution joins observed connections to that invocation. Primitive with no observed traffic: flagged `failed`. Traffic with no invocation: flagged `unattributed`, never defaulted to benign. Traffic from a primitive whose tool reported failure (a failed exploit) is real traffic and is labelled with `outcome=failed`.

### 4.12 Egress: stub by default, swappable to real

External destinations (Microsoft 365, Windows Update, websites) are not in the lab, so the generator has to stand in for them. Default is a **stub**: a local server impersonating the fitted external hostnames, with a lab certificate authority (a private CA whose root is installed in the actor images' trust stores, so the stub can present valid-looking certs for any name). Fully offline, fully reproducible, every external flow labelled by construction; the cost is fidelity, since one stub answering for many services gets TLS fingerprints, timing and payload shapes wrong. The stub is built so that any subset of services can be swapped for a real endpoint: many providers offer staging or test environments, so an engineer can point selected names at those and keep the rest stubbed. The far end of the spectrum, `egress="allowlist"`, routes real traffic to the real internet through a NAT restricted to the fitted destination set: faithful, not reproducible, needs real access and possibly real accounts. Per-service replacement between the two extremes is the intended normal mode. All egress is labelled whichever way it resolves. The fidelity report tells the engineer when the stub stops being good enough for a given service.

### 4.13 GHOSTS is a backend

A fitted process samples a timeline; the timeline is handed to GHOSTS. Statistics are then known by construction. Application fan-out is attributed to the parent action through the process-to-socket join. Relevant mainly for Windows users with real Office and Outlook.

### 4.14 Python only, embedded DSL, no external syntax initially

The type system is small and first-order; every tool SDK, container SDK, fitting library and pcap tool is Python; the contributor pool is Python. External syntax means parser, formatter, LSP and error-message work before anyone can use the tool. Revisit only if higher-order placed computations or dependent multiplicities become necessary. They should not.

### 4.15 Interfaces from M0, named first implementations in M1

The backend interfaces (`Sensor`, `InfraBackend`, `AttributionBackend`) and the common event model are defined in M0 alongside the core, so the abstractions exist before any backend shapes them, but M0 ships no backend and installs without Docker. The first concrete implementations (Docker, libvirt, Zeek, Suricata, Linux eBPF and Windows ETW/Sysmon attribution) land together in the M1 vertical slice. Within M1 the Linux container path is brought up first as an integration step, then the Windows host is added; the milestone's exit criterion is the mixed slice, so this is an implementation order, not a Linux-only milestone.

### 4.16 Tool-first quality bar

The output is a usable tool, not a paper. One-command install of `core`, `protocols`, `check`, `semantics` and `fit` on any platform without Docker; a CLI with clear errors; reproducible runs; documentation of the section 3 workflow written for a security engineer; fit and fidelity reports readable without knowing the internals. Novelty is not a criterion for including anything.

---

## 5. Glossary

| Term | Meaning |
|---|---|
| Actor kind | A type of participant (`Workstation`, `DomainController`, `FileServer`, `WebServer`, `Printer`, `Attacker`, `InternetStub`) with an interface, behaviours and allowed platforms. Analogue of a ScalaLoci peer type. |
| Actor instance | One running actor of a kind, with a host, platform and data-plane address. |
| Host | Where an instance runs: Linux or Windows, container or VM. Carries platform, image or template, resources. |
| Interface (actor) | Endpoints an actor serves (protocol, port, transport) and ties it requires. |
| Tie | A typed relation from one kind to another with multiplicity `single`, `optional` or `multiple`. Who may talk to whom. |
| Behaviour | A stochastic process over actions attached to a kind, with a time-of-day rate function. |
| Action | An abstract state of a behaviour (`http_get_small`, `smb_read`, `kerberos_tgs`), derived from the common event model. Maps to a signature or is silent. |
| Signature | A protocol-level primitive (`http.get`, `smb.read`) with typed parameters and an expected traffic shape (connections, transport, ports, permitted follow-on connections, reuse semantics). Defined in `protocols/`. The IR references signatures, never tools. |
| Implementation | A per-tool package providing signatures (`PrimitiveImpl`), running a service (`ServiceImpl`) or adapting an external framework (`AdapterImpl`). Registered by what it provides, with a manifest of host requirements and fingerprint metadata. |
| Sensor | A passive traffic sensor behind the interface in 4.3: ingest and label, a pinned version and config, and a declared capability set. Zeek and Suricata are the first two. |
| Common event model | Schema-neutral events every sensor maps into. Required core `ConnEvent`: sensor-native connection id, 5-tuple, start and duration, bytes and packets per direction, state. Optional `AppEvent` (under `APP_EVENTS`): parent connection id, timestamp, protocol, normalised fields, capability-gated fingerprints. Every event keeps raw passthrough that core consumers may not read. |
| Capability | A named, typed extension a sensor declares above the required core: `APP_EVENTS`, `TLS_JA4`, `HTTP_USER_AGENT`, `SSH_STRINGS`, `SMB_DIALECT`, `X509`, extensible. Each carries a schema and a coverage claim. Consumers query capabilities and degrade explicitly when one is absent. |
| Coverage | The fraction of applicable events on which a sensor actually populates a capability's field, measured at fit time. Distinguishes a trustworthy distribution from a sparse one. |
| Binding | For a kind in a scenario: the host (default container, image, VM template) and the implementation selection per signature, fixed or weighted. |
| Scenario | Kinds, instance counts, bindings, topology, egress policy, schedule, duration, capture points, sensor set. |
| Schedule | Time-indexed events: start or stop behaviours, change rates, run scripted sequences (attacks). |
| Label | `(scenario, instance, behaviour, action, invocation id, implementation id, variant, expected target, outcome)`; attached, per configured sensor, to that sensor's connection id and sub-connection events. |
| Attribution | Kernel-level join of observed connections to invocations, sensor-independent: eBPF (Linux), ETW or Sysmon (Windows), keyed by cgroup or PID and time. |
| Fidelity | Distance between generated and real traffic at the common-event level, per metric in section 9. |
| Conformance | Distance between a run and its own model; separates implementation bugs from model gaps. |

---

## 6. Architecture

```
tiergen/                  uv workspace; one package per directory, one per implementation
  core/                   IR, JSON round-trip, embedded DSL builders, common event model
  protocols/              signatures with expected traffic shapes, one module per protocol; no tool deps
  check/                  static checker (well-formedness, interfaces, platform, Z3 constraints)
  semantics/              process interface, semi-Markov default, product-process analysis, prediction, Storm export
  fit/                    ingestion via Sensor, host inventory, role clustering, behaviour and impl-mix fitting, proposal
  interfaces/             backend Protocols: Sensor (+ Capability enum, CapabilityInfo), InfraBackend, AttributionBackend (defined M0, no impls)
  backends/
    sensor/
      _base/              Sensor Protocol re-export, common event model helpers
      zeek/  suricata/    Sensor implementations
    infra/
      _base/              InfraBackend Protocol, address planning, manifest helpers
      docker/  libvirt/   InfraBackend implementations (nomad/, k8s/ later)
    attrib/
      _base/              AttributionBackend Protocol, join logic
      linux_ebpf/  windows_etw/   AttributionBackend implementations (nfstream fallback)
    predict/              predicted sensor-level statistics and pre-run fidelity report
    assemble/             sensors over pcaps, attribution join, per-sensor labels, conformance and fidelity reports
  runtime/
    agent_linux/  agent_windows/  per-host agents: projected program, behaviour loop, primitive execution, logging
    scheduler/            management-plane orchestrator: hosts, agents, clock check, schedule, log collection
    capture/              dumpcap at capture points, pcapng with interface ids, per-host clock offsets
  impls/                  one package per tool, discovered via entry points (6.1)
    _base/                interfaces, manifest schema, subprocess/cgroup/job-object execution, timing, outcomes, retry
    httpx/ playwright/ curl/ dig/ paramiko/ impacket/ nmap/ smbclient_win/ ...   primitive impls
    nginx/ apache/ caddy/ unbound/ bind/ postfix/ dovecot/ samba/ win_fileserver/ ...  service impls
    caldera/ atomic/ ghosts/ metasploit(opt-in)/                                  adapters
  evaluate/               reference detectors over common-event features, FP-rate harness against held-out real logs
```

Data flow:

```
real network ──sensor──► native logs ──fit (ingest)──► models/ + scenario_proposed.py
                                              │ describe (engineer edits)
                                              ▼
                                       scenario.py ──build──► IR (JSON)
                                              │ check
                                              ├──► predict ──► predicted stats, fidelity report (vs real logs)
                                              ├──► infra backend ──► manifests, projected programs
                                              ├──► sensor backends ──► per-sensor config for generation
                                              └──► labels ──► schema, attribution config
                                       run ──► pcaps, agent logs, attribution logs
                                       assemble ──► pcaps, <sensor>/ logs, labels.<sensor>.jsonl,
                                                    flagged.jsonl, conformance.md, fidelity.md, manifest.json
                                       evaluate ──► detector trained on dataset, tested on held-out real logs
```

### 6.1 Implementation packages

Three things scale differently and are kept apart: protocol-level signatures (a few dozen, stable), tool-level implementations (open-ended, each with its own dependencies and host requirements) and adapters for frameworks whose catalogs hold hundreds of entries.

**`protocols/`** (in core). One module per protocol. A signature has typed parameters and an expected traffic shape: number of connections, transport, destination port, direction, permitted follow-on connections (DNS before HTTP, redirects), and reuse semantics (may this primitive reuse an existing connection of the same process, and if so how are per-request labels delimited). Attribution uses the shape to match observed connections to an invocation; conformance tests use it to check implementations. Adding a protocol touches one module.

**`impls/<tool>/`**. One workspace package per tool with its own dependencies. Layout by tool, because tools are what get installed and pinned and one tool often serves several protocols (Impacket: SMB, LDAP, Kerberos, DCERPC). Navigation by protocol through the registry: `tiergen impls list --protocol smb --platform windows`. Registration through the entry-point group `tiergen.impls`, discovered with `importlib.metadata`; core never imports implementations at load time, so an uninstalled one is simply unresolved.

Manifest per package (`impl.toml`):

```toml
id = "http.playwright"
version = "0.1.0"
kind = "primitive"                 # primitive | service | adapter
provides = ["http.browse", "http.get", "http.post_form"]
variants = ["chromium", "firefox", "webkit"]
[host]
platforms = ["linux", "windows"]
binaries = []                      # resolved per platform by the package
capabilities = []                  # e.g. ["net_raw"] for scanners
image_base = { linux = "tiergen/base-desktop", windows = "tiergen/base-desktop-win" }
[fingerprint]
role = "client"
product = "playwright"
ja4 = { chromium = "auto", firefox = "auto", webkit = "auto" }   # measured by the conformance test
user_agent = "auto"
```

Interfaces in `impls/_base`:
- `PrimitiveImpl`: `run(ctx, **params) -> Outcome`. Executes on the client actor's host inside the invocation's cgroup (Linux) or job object (Windows). `ctx` gives resolved ties, sampling, the label tuple and timing helpers.
- `ServiceImpl`: `start(ctx)`, `healthcheck(ctx)`, `stop(ctx)`, `served() -> tuple[Endpoint, ...]`. Doubles as the binding manifest for default-compiled server actors.
- `AdapterImpl`: `catalog() -> Iterable[CatalogEntry]` so the checker validates references statically; `run(ctx, catalog_id, **params)`. Catalog entries are data, never one file per ability.

**Selection is data.** A binding resolves each `(kind, signature)` to one implementation or a weighted set sampled per instance. Weights come from `fit` (4.10) or the engineer. Resolved id and variant go into every label.

**Conformance test per implementation.** Each primitive implementation ships a test that runs it against a reference service implementation in a two-host fixture and asserts that the observed connections from the invocation match the signature's traffic shape. The test also records the implementation's measured fingerprints (JA4, user agent, SSH strings) and per-primitive connection profiles (bytes, packets, duration distributions), which `predict` uses. It catches tools that quietly open extra connections that would otherwise become unattributed traffic.

---

## 7. IR sketch

*Sketch.* Frozen slotted dataclasses; every node has a stable `id`; `to_json`/`from_json` on the root.

```python
from dataclasses import dataclass
from typing import Literal

Multiplicity = Literal["single", "optional", "multiple"]
Transport = Literal["tcp", "udp"]
Platform = Literal["linux", "windows"]
HostType = Literal["container", "vm"]

@dataclass(frozen=True, slots=True)
class Endpoint:
    protocol: str; port: int; transport: Transport

@dataclass(frozen=True, slots=True)
class Tie:
    name: str; target_kind: str; multiplicity: Multiplicity

@dataclass(frozen=True, slots=True)
class Distribution:
    family: str                                  # "exponential" | "lognormal" | "weibull" | "empirical"
    params: tuple[float, ...] | str              # inline or resource reference

@dataclass(frozen=True, slots=True)
class SemiMarkov:
    states: tuple[str, ...]
    initial: tuple[float, ...] | str
    transitions: tuple[tuple[float, ...], ...] | str
    dwell: tuple[Distribution, ...]              # one per state
    rate: str | None                             # resource: hourly multipliers, 24 or 168 values

@dataclass(frozen=True, slots=True)
class Behaviour:
    name: str
    process: SemiMarkov                          # later: Process union
    action_map: dict[str, str | None]            # action -> signature, None = silent

@dataclass(frozen=True, slots=True)
class ActorKind:
    name: str
    serves: tuple[Endpoint, ...]
    ties: tuple[Tie, ...]
    behaviours: tuple[Behaviour, ...]
    platforms: tuple[Platform, ...]              # allowed platforms

@dataclass(frozen=True, slots=True)
class Host:
    platform: Platform
    host_type: HostType
    ref: str                                     # "default" | "image:<ref>" | "template:<ref>"
    manifest: str | None                         # served-endpoint manifest for custom hosts

@dataclass(frozen=True, slots=True)
class ImplSelection:
    signature: str
    choices: dict[str, float]                    # "impl_id[:variant]" -> weight

@dataclass(frozen=True, slots=True)
class Binding:
    kind: str
    host: Host
    impls: tuple[ImplSelection, ...]

@dataclass(frozen=True, slots=True)
class ScheduleEvent:
    at_s: float
    target: str                                  # instance or kind selector
    op: Literal["start", "stop", "set_rate", "run_sequence"]
    arg: str | float | None

@dataclass(frozen=True, slots=True)
class SensorSpec:
    impl: str                                    # "zeek" | "suricata" | ...
    version: str                                 # pinned
    config: str                                  # resource: the exact config used on real + generated traffic
    mode: Literal["offline", "live"]
    capabilities: tuple[str, ...]                # Capability names this config declares, from the sensor
    role: Literal["label", "fit", "both"]        # "fit" marks the sensor the model was fitted from

@dataclass(frozen=True, slots=True)
class FitProvenance:
    sensor: str                                  # impl id of the fit sensor
    capabilities_used: tuple[str, ...]           # Capabilities fit actually relied on, recorded by `fit`
    coverage: dict[str, float]                   # measured coverage per capability used

@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    kinds: tuple[ActorKind, ...]
    instances: dict[str, int]
    bindings: tuple[Binding, ...]
    topology: str                                # resource or builtin
    egress: Literal["stub", "allowlist", "none"]
    egress_overrides: dict[str, str]             # hostname or service -> real endpoint, for per-service swap
    schedule: tuple[ScheduleEvent, ...]
    duration_s: float
    capture_points: tuple[str, ...]
    sensors: tuple[SensorSpec, ...]              # one or more; labels emitted per sensor
    fit_provenance: FitProvenance | None         # what fit relied on; enables the cross-sensor check
    seed: int
```

Embedded DSL, *sketch*, as `fit` would propose it and the engineer would edit:

```python
from tiergen import kind, endpoint, tie, semi_markov, resource, host, binding, scenario, sensor, at, hours

Dc  = kind("domain_controller", serves=[endpoint("kerberos", 88, "tcp"), endpoint("ldap", 389, "tcp"),
                                        endpoint("smb", 445, "tcp"), endpoint("dns", 53, "udp")],
           platforms=["windows"])
Fs  = kind("file_server", serves=[endpoint("smb", 445, "tcp")], platforms=["windows", "linux"])
Web = kind("intranet_web", serves=[endpoint("https", 443, "tcp")], platforms=["linux"])
Net = kind("internet_stub", serves=[endpoint("https", 443, "tcp"), endpoint("http", 80, "tcp")], platforms=["linux"])

Ws = kind("workstation",
    ties=[tie("dc", Dc, "single"), tie("fs", Fs, "multiple"), tie("web", Web, "multiple"), tie("net", Net, "single")],
    behaviours=[semi_markov("office",
        states=resource("ws_office.states"),
        transitions=resource("ws_office.transitions"),
        dwell=resource("ws_office.dwell"),
        rate=resource("ws_office.rate_week"),
        action_map=resource("ws_office.action_map"))],
    platforms=["windows", "linux"])

Atk = kind("attacker", ties=[tie("dc", Dc, "single"), tie("victim", Ws, "multiple")], platforms=["linux"])

S = scenario("hq_lan",
    instances={Ws: 60, Dc: 1, Fs: 2, Web: 1, Net: 1, Atk: 1},
    bindings={
        Dc:  binding(host("windows", "vm", "template:win2022-dc")),
        Ws:  binding(host("windows", "container", "default"),
                     impls={"http.browse": resource("ws_office.browser_mix"),
                            "smb.read": {"smb.windows_native": 1.0}}),
        Fs:  binding(host("linux", "container", "image:tiergen/samba:4.20")),
        Web: binding(host("linux", "container", "image:nginx:1.27")),
        Net: binding(host("linux", "container", "default"), impls={"internet.serve": {"internet.stub": 1.0}}),
        Atk: binding(host("linux", "container", "default"), impls={"attack.run": {"attack.caldera": 1.0}}),
    },
    topology=resource("hq_lan.topology"),
    egress="stub",
    egress_overrides={"update.microsoft.com": "real"},          # example per-service swap
    schedule=[at(hours(30), Atk, "run_sequence", "caldera:discovery-then-kerberoast")],
    duration_s=7 * 24 * 3600,
    capture_points=["core-switch-span"],
    sensors=[sensor("zeek", "7.0", resource("hq_lan.zeek"), "offline",
                    caps=["APP_EVENTS", "TLS_JA4", "HTTP_USER_AGENT", "SSH_STRINGS", "SMB_DIALECT", "X509"], role="both"),
             sensor("suricata", "7.0.7", resource("hq_lan.suricata"), "offline",
                    caps=["APP_EVENTS", "TLS_JA4", "HTTP_USER_AGENT"], role="label")],
    fit_provenance=resource("hq_lan.fit_provenance"),   # emitted by `fit`; here fit used Zeek
    seed=1)
```

In this example `fit` used Zeek and relied on `SMB_DIALECT`, which the Suricata label sensor does not declare. Check 14 (section 8) flags that: a detector trained on SMB-dialect-derived features will not see them in a Suricata deployment. The engineer either drops that capability from the fit, adds the Suricata config that provides it, or accepts the gap knowingly.

---

## 8. Static checks

Each is a named check with unit tests and, where the input space allows, a hypothesis property test.

1. Tie targets exist; multiplicities are satisfiable by instance counts (Z3).
2. Every signature a kind's actions use is directed at a tie whose target serves a compatible endpoint (protocol, transport).
3. Every behaviour state maps to exactly one signature or is explicitly silent.
4. Transition matrices row-stochastic; all states reachable; one dwell per state; rate resources have 24 or 168 entries.
5. Resource references resolve; resolved shapes match declared shapes.
6. Host bindings satisfy the kind's interface: default hosts via the chosen `ServiceImpl`s, custom hosts via their manifest.
7. Binding platform is in the kind's allowed platforms; every selected implementation supports that platform; host capabilities (`net_raw`, admin) are grantable by the infra backend for that host type.
8. Every `(kind, signature)` resolves to at least one registered implementation; weights positive and normalisable; adapter catalog ids referenced by sequences exist.
9. Management network disjoint from all data-plane networks; every capture point is data-plane; every sensor's capture interface is data-plane.
10. Address plan collision-free; every instance has a data-plane address; topology realisable by the chosen infra backend; egress policy consistent with the presence of an `internet_stub` kind or an allowlist resource; every `egress_overrides` key is a fitted external destination.
11. Label tuple unique per invocation; no primitive executable outside a labelled context.
12. Schedule events reference defined targets; times within `duration_s`.
13. Each `SensorSpec` names a registered sensor implementation whose pinned version and config the sensor backend can reproduce; at least one sensor is configured; every declared capability name is one the implementation actually supports; the required core is met by every sensor.
14. Cross-sensor consistency: every capability in `fit_provenance.capabilities_used` is declared by every sensor whose `role` includes `label`. A violation is a warning, not an error, and names the capability, the fit sensor and the label sensor lacking it, because the engineer may accept the gap deliberately. Exactly one sensor has a `role` including `fit`, and it matches `fit_provenance.sensor`.
15. Coverage sanity: every capability `fit` relied on has measured coverage above a floor the scenario sets (default 0.5); below it, warn that the fitted distribution for that capability is sparse.

Runtime checks before capture: clock sync within tolerance on every host; attribution backend loaded per host platform; capture and sensor interfaces up; every service healthcheck passes.

---

## 9. Prediction, fidelity, conformance

**Denotation.** A scenario denotes the product of its actors' processes under the schedule's time-inhomogeneous control. Semi-Markov default: embedded-chain stationary distribution per behaviour, mean dwell per state, long-run occupancy, expected invocations per unit time per `(role, action)` modulated by the weekly rate curve. Exponential dwell gives a CTMC exportable to Storm or PRISM; general dwell is simulated from the same process objects.

**Prediction.** Invocation rates combined with signature traffic shapes and the per-implementation connection profiles measured by conformance tests yield predicted statistics at the common-event level: connections per service per hour per role, duration and byte distributions per service, HTTP request rate and size mix, DNS query rate, TLS SNI and JA4 mix, SMB operation mix, Kerberos request mix, per-role peer counts.

**Fidelity metrics** (generated or predicted vs real, at the common-event level, per role and overall):
- per-service connection rate error, hourly, over the week
- distribution distances (Wasserstein, KS) on connection duration, bytes per direction, inter-connection time, per service and role
- service-mix divergence per role (Jensen-Shannon)
- client and server fingerprint mix divergence (JA4, user agent, SSH strings)
- external-destination mix divergence (SNI, hostnames) under the chosen egress policy
- per-sensor alert-rate comparison on benign traffic where the sensor emits alerts (a generator that trips rules the real network does not trip is wrong in a way that matters for deployment)

Each metric depends on capabilities: the fingerprint-mix divergences need the relevant fingerprint capability, the SMB and Kerberos operation mixes need `APP_EVENTS`. A metric whose capability the sensor lacks is reported as "not computed" with the missing capability named, never as zero or as a pass. The report header lists which metrics were available for the sensor in use, so a thin report reads as thin rather than as good.

Reported as a table with user-set thresholds. `predict` runs it before build; `assemble` runs it after. Because both real and generated logs pass through the same sensor ingest into the common event model, the comparison is apples to apples regardless of which sensor produced them.

**Conformance** (a run vs its own model): the same metrics against the denotation instead of the real logs, plus per-invocation exactness (every confirmed label matches its signature's shape). A conformance gap is an implementation or infrastructure bug; a fidelity gap with good conformance is a model gap. Keeping them apart is what makes iteration tractable.

---

## 10. Runtime

- **Agents** (`agent_linux`, `agent_windows`). Receive the projected program: behaviours, action map, resolved implementations and variants, ties resolved to addresses, seed. Loop: sample state and dwell, execute the primitive through its implementation inside a fresh cgroup (Linux) or job object (Windows), log `(invocation id, label tuple, start, end, outcome, monotonic and wall clock)`. Long-lived processes such as a browser kept open across invocations are allowed when the scenario asks for them; their per-request labels rely on interval matching and carry a confidence field.
- **Scheduler** (management plane): brings hosts up through the infra backend, starts agents, verifies clock sync, starts capture and any live sensors, drives the schedule, collects logs, stops.
- **Attribution** (sensor-independent kernel truth). Linux: bcc programs on `tcp_connect`, `inet_csk_accept`, UDP send and receive, keyed by cgroup and PID; a `cgroup_skb` program for raw-socket tools. Windows: Sysmon event 3 (network connection with PID) by default, ETW `Microsoft-Windows-Kernel-Network` as the alternative. VMs use their guest OS backend. Fallback: nfstream system-visibility mode, coarser. The join produces `(host, pid/cgroup, 5-tuple, interval)` records; each configured sensor's label step maps those onto its own event ids by 5-tuple and time window. Known holes, handled by flagging rather than guessing: DNS via a system resolver daemon, OS background traffic, connection reuse across invocations in one process.
- **Capture.** dumpcap at declared capture points; pcapng with interface ids; chrony on Linux, w32time on Windows, PTP where the substrate has it; per-host clock offsets recorded and applied at join.
- **Sensors.** Offline mode (default, reproducible): every configured sensor runs over the pcaps in `assemble` with the target's pinned config. Live mode: sensors run in-network during the run, for exercising the exact deployment path. Same config either way.

TLS: clients that support `SSLKEYLOGFILE` write keys alongside the pcap so payload-level labels remain possible; sensors are not given the keys by default, so the dataset reflects what the deployed sensor actually sees.

---

## 11. Fitting from sensor logs

Input: the target network's logs for the collection period, read through the sensor's ingest adapter into the common event model, so fitting is written once against `ConnEvent` and `AppEvent` and works for any sensor. Output: resources referenced from `scenario_proposed.py`, a `FitProvenance` recording which capabilities were used and their measured coverage, and a fit report of everything unmapped.

0. **Capability probe.** Read the sensor's declared capabilities and measure each one's coverage on the actual logs (the fraction of applicable events where the field is present). This sets the resolution of everything below and populates `FitProvenance`. Every later step checks the capabilities it needs and degrades explicitly, writing a report line rather than silently defaulting.
1. **Host inventory.** Internal hosts from `ConnEvent` endpoints and any host-identity `AppEvent`s; internal versus external by subnet; per-host service mix as originator and responder. Needs only the required core, so it always runs.
2. **Role clustering.** Feature vector per host: service mix both directions, weekly activity profile, peer count, bytes. Cluster (HDBSCAN, silhouette as a sanity metric); propose one actor kind per cluster named from its dominant services. Engineer confirms, merges, splits, renames. Required core only.
3. **Action vocabulary.** With `APP_EVENTS`: the fine per-protocol vocabulary (`http_get_small`, `http_get_large`, `http_post`, `dns_query`, `tls_session`, `smb_read`, `smb_write`, `kerberos_as`, `kerberos_tgs`, `ldap_search`, `ssh_session`, `rdp_session`, `ntp`, `idle`), small/large thresholds from the data, each action mapping to one signature. Without `APP_EVENTS`: connection-level classes by service, port, size and direction, which map to coarser signatures. The report states which vocabulary was used.
4. **Behaviour per role.** Sessionise each host's actions by idle gap; estimate transition matrix and dwell per action (family by AIC among exponential, lognormal, Weibull, empirical); weekly rate curve from hourly activity. Pool hosts within a role; per-host models only where a role has enough data. Report effective sample sizes.
5. **Implementation mix per role.** For each fingerprint capability present, map its values (JA4, user agent, SSH strings, SMB dialect and OS strings) to installed implementation variants using the fingerprints measured by conformance tests, weighting by that capability's coverage. Absent capability: no fingerprint-driven mix for that protocol, so bindings fall back to a single default client per role and the report says the diversity is unfitted rather than silently uniform. Unmapped fingerprint values go in the report with their traffic share.
6. **Services.** Responders' endpoints and any version strings become server kinds and suggested bindings (`nginx:1.27`, `samba:4.20`, a Windows DC template).
7. **External destinations.** SNI and hostname distribution per role; emitted for the internet stub or as an egress allowlist. SNI needs `TLS_JA4` or a TLS `AppEvent` carrying server name; without it, external destinations are known only by IP and the report flags the coarser egress model.
8. **Topology and address plan.** Subnets from observed addresses, gateway behaviour from `ConnEvent` routing patterns, VLAN hints from the engineer.
9. **Privacy.** Fitted resources can carry hostnames, SNI and user agents. `fit --anonymise` replaces them with consistent pseudonyms; the report says what was replaced.

Identifiability caveat, recorded so nobody rediscovers it: aggregate fits describe the role, not any individual. That is fine for the purpose in section 1; the fidelity report, not the fit, decides whether it is good enough.

---

## 12. Data plane

- **Hosts.** Linux containers (default, cheapest); Windows containers with Hyper-V isolation, through a Windows Docker daemon alongside the WSL2 Linux engine (two daemons, two contexts; verify concurrent operation early); Linux and Windows VMs via libvirt for the DC, Windows workstations with real Office and Outlook, and anything needing transport fidelity; a multi-node backend (Nomad or k8s) only once one machine runs out of room, per 4.9.
- **Implementations.** Several browsers (Playwright: Chromium, Firefox, WebKit; native Edge on Windows), several HTTP clients, native Windows SMB and Kerberos clients where the platform is Windows, Impacket where it is Linux; several servers per role (nginx, Apache, Caddy; BIND, Unbound; Postfix, Dovecot; Samba; a real Windows DC). Weights from `fit`.
- **Internet.** `egress="stub"`: an `internet_stub` kind serving the fitted SNI and hostname set behind a lab CA, using real server implementations behind the right names, with any subset swappable to a real staging or production endpoint through `egress_overrides`. `egress="allowlist"`: real egress through a NAT restricted to the fitted destination list. Both fully labelled. Per-service swap is the expected normal mode.
- **Noise roles.** NTP, update mirrors, mDNS/SSDP, telemetry stubs, printers, as small kinds with simple processes, so noise is labelled as noise.
- **Attacks.** CALDERA abilities and Atomic Red Team as the default adapter with ATT&CK ids in labels; Impacket-based AD attacks (Kerberoasting, lateral movement, DCSync) as primitives; the target's threat model decides which sequences are scheduled. No live malware in the repository.
- **Network conditions.** Per-link `tc netem` on Docker networks first; emergent conditions from a real topology backend later.

---

## 13. Evaluation loop

The engineer has the real network, so evaluation is direct:

1. Split real logs into a fit period and a held-out period.
2. Generate a dataset from the fitted scenario, with attacks scheduled.
3. Train a detector on the generated dataset.
4. Measure benign false-positive rate on the held-out real logs, and detection rate on generated attacks and any real red-team logs the network has.
5. Read the fidelity report next to the FP rate; adjust models, bindings, noise roles, egress; regenerate.

`evaluate/` ships reference detectors so the loop works out of the box: gradient boosting over `ConnEvent` and `AppEvent` features per connection, an autoencoder over per-host time windows, and the configured sensor's own rules as a signature baseline. Features come from the common event model, so the harness is sensor-neutral. They are examples; the harness that trains on generated and tests on real is the point.

---

## 14. Libraries

Core, protocols, checker, interfaces: `dataclasses`/`attrs` (frozen, slots), `match`, `pydantic` at the user boundary, `z3-solver`, `networkx`, `mypy --strict` or `pyright` strict, `ruff`, `hypothesis`, `tomllib`, `importlib.metadata`, `typing.Protocol` for the backend interfaces.

Semantics and fit: `numpy`, `scipy.stats`, `hmmlearn` or `pomegranate`, `scikit-learn` and `hdbscan` for role clustering, `polars` or `pandas` for logs (`zat` for Zeek, a small `eve.json` reader for Suricata), `stormpy` (Storm) or PRISM via subprocess.

Backends: `docker` SDK or `python-on-whales` (both daemons), `libvirt-python`, `jinja2`, `ruamel.yaml`, `pyroute2`; later `python-nomad`, then a `kubernetes` client with KubeVirt if k8s is adopted.

Sensors: Zeek and Suricata as pinned containers driven over pcaps; ingest adapters written against their log schemas into the common event model.

Runtime and implementations: `playwright`, `httpx`, `paramiko`, `impacket`, `python-nmap`, `pymetasploit3` (opt-in), CALDERA REST API, GHOSTS REST API, `scapy` for the few crafted cases; on Windows, `pywin32` for job objects and services, `wmi`, `python-evtx` or the event log APIs for Sysmon.

Attribution and capture: `bcc`, `nfstream`, `dpkt`, `pyshark`.

Reference DSLs to read before designing `core/`: Amaranth (embedded DSL with typed IR and backends), Exo (research DSL over Python AST), JAX (tracing, multiple interpretations), Pyro `poutine` and `effectful` (effect handlers), Mininet `Topo` (topology DSL), Pulumi Python and cdk8s (program to manifests), Scapy and z3py (operator-overloading AST builders).

---

## 15. Roadmap

No dates. Each milestone ends with something an engineer can run.

- **M0 Core and interfaces.** IR (platform, multi-sensor, egress overrides), JSON round-trip, embedded builders, common event model, `protocols/` with `http`, `dns`, `smb`, `kerberos`, `ssh`, `scan` signatures, `impls/_base` interfaces and registry, the backend Protocols (`Sensor`, `InfraBackend`, `AttributionBackend`) in `interfaces/` with no implementations, checker with tests, `tiergen check` and `tiergen impls list`. Three example scenarios, one ill-formed. Installs without Docker.
- **M1 Vertical slice, mixed platform.** First backends behind the M0 interfaces: Docker (Linux and Windows daemons) and libvirt; Zeek and Suricata sensors (offline); Linux eBPF and Windows ETW/Sysmon attribution; `agent_linux` and `agent_windows`. First implementations: `httpx`, `nmap`, `nginx`, native Windows SMB and Kerberos client, `samba` or a Windows file server. Scenario: one DC (Windows VM via libvirt), one Windows workstation, one Linux server, one attacker; stub egress; dumpcap; per-sensor labels keyed by Zeek `uid` and Suricata `flow_id`; `assemble`. Integration order inside the milestone: Linux path first, then add the Windows host. Deliverable: labelled pcaps plus Zeek and Suricata logs from one command on a mixed slice.
- **M2 Processes and prediction.** Semi-Markov behaviours, resources, weekly rates, `predict`, fidelity report against a real sensor-log sample, Storm export for the CTMC case, conformance report.
- **M3 Attribution hardening.** cgroup per invocation and `cgroup_skb` for scanners, interleaved actors on shared hosts, per-implementation conformance tests measuring fingerprints and connection profiles, label-exactness check against an isolated-mode run, DNS-resolver and connection-reuse holes handled by flagging.
- **M4 Fit.** Ingestion via the Sensor interface, host inventory, role clustering, action vocabulary, behaviour and implementation-mix fitting, proposed scenario emission, anonymisation, fit report. Drive it with the AD LAN.
- **M5 Internet and diversity.** Internet stub with lab CA, per-service `egress_overrides`, allowlist mode, noise roles, browser and client variants with fitted weights, Impacket and CALDERA attack sequences, GHOSTS adapter for Windows users.
- **M6 Scale (if needed).** Nomad backend for multi-node, evaluated before any k8s work; more service implementations as roles demand.
- **M7 Evaluation loop.** `evaluate/` harness and reference detectors; run the full workflow against a real AD LAN end to end; fix what the fidelity report exposes; write the engineer-facing documentation from that experience.

---

## 16. Open questions

- *open* Windows workstation as a Hyper-V-isolated container versus a VM for the M1 slice. Container is cheaper and denser; VM is more faithful at the transport layer and simpler for real Office. Likely container for M1, VM as a binding option.
- *open* Multi-sensor labels: emit one label file per sensor (assumed) versus a unified label file with per-sensor id columns. Per-sensor files are simpler and match how the sensors are consumed downstream.
- *open* Common event model coverage: the field subset needed so fit and fidelity do not have to reach back into sensor-native logs. Grows as protocols are added; keep raw passthrough so nothing is lost.
- *open* First target substrate to develop M1 against: Docker Desktop on Windows (both daemons on one box) versus a Linux host with libvirt for the Windows VM. Decides which concurrency issue is hit first.
- *open* The initial `Capability` set and each one's typed schema. The enum in 4.3 is a starting list; adding OT and ICS protocols (Modbus, DNP3, S7) will extend it, and the schemas need to be defined before the second sensor is written so they are not Zeek-shaped by accident.
- *open* Where the coverage floor for check 15 should sit per capability, and whether it should be per protocol rather than one global default.
- *open* Whether `fit` should offer to synthesise the config that would give a label sensor a capability it lacks (for example a Suricata config change), or only report the gap.
- *open* How much of the AD LAN's SaaS egress the stub can represent before the fidelity report says swap to real for a service.
- *open* Sensor version drift between collection and generation; pinning is required, upgrade policy is not defined.
- *open* Long-lived browser per user (realistic, interval-based per-request labels) versus browser per invocation (clean attribution, unrealistic reuse). Probably long-lived with confidence fields.
- *open* Keep a per-invocation netns isolation mode as an option for DetGen-style microstructure control.

---

## 17. References

Verify before citing; entries are from memory.

Sensors and formats
- Zeek documentation: log schemas (`conn`, `http`, `ssl`, `ssh`, `smb_*`, `kerberos`, `dce_rpc`, `software`), `uid` semantics, package manager.
- Suricata documentation: `eve.json` flow and app-layer records, `flow_id`.
- FoxIO. JA4+ network fingerprinting.
- Sysmon documentation: event 3 (network connection). ETW `Microsoft-Windows-Kernel-Network`.
- bcc and libbpf documentation; `cgroup_skb` programs.

Datasets and their problems
- Sommer, Paxson. Outside the Closed World. IEEE S&P 2010.
- Sharafaldin, Lashkari, Ghorbani. CICIDS2017. ICISSP 2018.
- Moustafa, Slay. UNSW-NB15. MilCIS 2015.
- Garcia, Grill, Stiborek, Zunino. CTU-13. Computers & Security 2014.
- Engelen, Rimmer, Joosen. Troubleshooting an Intrusion Detection Dataset: the CICIDS2017 Case Study. IEEE S&P Workshops 2021.
- Flood, Engelen, Aspinall, Desmet. Bad Design Smells in Benchmark NIDS Datasets. IEEE EuroS&P 2024.
- Ring, Wunderlich, Scheuring, Landes, Hotho. A Survey of Network-based Intrusion Detection Data Sets. Computers & Security 2019.

Generators
- Clausen, Flood, Aspinall. DetGen (2019) and Controlling Network Traffic Microstructures for Machine-Learning Model Probing (SecureComm 2021). https://github.com/detlearsom/DetGen
- Cordero et al. ID2T. ACM TOPS 2021.
- Updyke et al. GHOSTS in the Machine. CMU SEI 2018. https://github.com/cmu-sei/GHOSTS
- Vishwanath, Vahdat. Swing. IEEE/ACM ToN 2009.
- Molnár, Megyesi, Szabó. How to Validate Traffic Generators? ICC Workshops 2013.
- Yin et al. NetShare. SIGCOMM 2022.
- Jiang et al. NetDiffusion. SIGMETRICS 2024.

Multi-tier and choreographies
- Weisenburger, Köhler, Salvaneschi. Distributed System Development with ScalaLoci. OOPSLA 2018.
- Weisenburger, Wirth, Salvaneschi. A Survey of Multitier Programming. ACM CSUR 2020.
- Murphy, Crary, Harper. ML5. TGC 2007.
- Cooper, Lindley, Wadler, Yallop. Links. FMCO 2006.
- Radanne, Vouillon, Balat. Eliom. APLAS 2016.
- Montesi. Introduction to Choreographies. CUP 2023.
- Giallorenzo, Montesi, Peressotti. Choral. TOPLAS 2024.
- Shen, Kashiwa, Kuper. HasChor. ICFP 2023.
- Bocchi, Yang, Yoshida. Timed Multiparty Session Types. CONCUR 2014.
- Majumdar, Pirron, Yoshida, Zufferey. Motion Session Types for Robotic Interactions. ECOOP 2019.

DSL engineering in Python
- Amaranth HDL. https://github.com/amaranth-lang/amaranth
- Ikarashi et al. Exocompilation. PLDI 2022.
- Bingham et al. Pyro. JMLR 2019; `effectful`.
- JAX documentation on tracing and jaxpr.
- Vehicle (own prior work; resource binding and multi-backend architecture). https://github.com/vehicle-lang/vehicle

Detectors for the evaluation harness
- Mirsky, Doitshman, Elovici, Shabtai. Kitsune. NDSS 2018.

---

## 18. Working agreements

- Read this file first. Do not reopen decisions in section 4 without a dated note there.
- Python 3.12+, uv workspace, `pyright` strict, `ruff`. Members build with hatchling and share the PEP 420 namespace `tiergen.*`: no `tiergen/__init__.py` anywhere, a `py.typed` in every package (2026-09-18: pyright chosen over mypy for Protocol and namespace-package handling; hatchling because its editable installs are path-based, which pyright resolves). Every check has a unit test; every IR type has a JSON round-trip property test.
- The IR is JSON. No callables in it; signatures, implementations, sensors, resources by name.
- Nothing in `core/`, `protocols/`, `check/`, `semantics/`, `fit/` or `interfaces/` may assume Linux, Docker or network access. They install and run anywhere.
- Backend interfaces live in `interfaces/` and are defined before their implementations. A backend is one package under `backends/`; no cross-imports between backend implementations; shared code in each family's `_base`.
- One package per tool under `impls/`, registered by what it provides. No imports between implementation packages; shared code in `impls/_base`. Adapter catalogs are data.
- The deployed sensor defines flows and events. Never reconstruct flows anywhere; consume the sensor's output through the common event model.
- The required core (`ConnEvent`) is the floor; everything above it is a declared `Capability`. `core`, `fit` and `fidelity` read only the required core and declared capabilities, never an event's raw passthrough. A field a consumer needs must be promoted to a capability first.
- Every consumer degrades explicitly against the capability set and records the degradation as a report line. A missing capability is "not computed," never a silent default or a zero.
- Management-plane traffic never enters a capture. Any networking change keeps check 9 passing.
- No invented statistics, distributions or "typical" parameters. Parameters are resources; a missing resource fails the check, it does not default.
- No label without a confirmed attribution join. Unknown means flagged.
- The fidelity report decides realism arguments. If a proposed change cannot be expressed as a metric it moves, it is not a realism change.
- No live malware; attacks only through emulation adapters and documented primitives.
- Reproducibility: every dataset ships `manifest.json` with image digests, implementation and sensor versions, seeds and the IR.
- Commits follow Conventional Commits 1.0.0 with a fixed scope list; branches follow Conventional Branch 1.1.0; `main` is linear, pull requests merge by rebase. `commit-check` enforces all of it from `cchk.toml`, in local hooks and in CI. `CONTRIBUTING.md` has the details (2026-09-18).
- Documentation and commit bodies in plain prose. Engineer-facing docs describe the workflow in section 3, not the internals.
- When this file is wrong, fix it in the same commit.

First tasks for M0:
1. Scaffold the uv workspace (section 6), pyproject per package, shared dev config, CI running tests without Docker.
2. IR from section 7 with `to_json`/`from_json` and hypothesis round-trip tests.
3. Common event model (`ConnEvent` required core, `AppEvent` optional) in `core/`; the `Capability` enum, `CapabilityInfo`, and the `Sensor`, `InfraBackend` and `AttributionBackend` Protocols in `interfaces/`, with docstrings and no implementations.
4. `protocols/` with the six M0 signatures and their traffic shapes; `impls/_base` interfaces, manifest schema, entry-point registry.
5. Checks 1 through 8 and 11 through 15 with tests and one ill-formed scenario each, including a cross-sensor capability-gap scenario for check 14.
6. Embedded builders (`kind`, `endpoint`, `tie`, `semi_markov`, `resource`, `host`, `binding`, `sensor` with `caps` and `role`, `scenario`) producing IR; three example scenarios, one with a deliberate fit-versus-label capability gap.
7. `tiergen check` and `tiergen impls list`.