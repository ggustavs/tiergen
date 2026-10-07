# tiergen: site-specific NIDS dataset generation from a multi-tier DSL

Working name `tiergen` (placeholder). Status: M0 done; M1 in progress. The IR has groups, action parameters and a typed topology; all sixteen checks exist; `tiergen build` writes a run directory and the Docker backend brings its Linux hosts up and down; the Linux agent runs a program's behaviours through the first three runtimes (`httpx`, `nginx`, `nmap`) from the backend's own image, so `linux_slice` generates traffic; dumpcap captures it at the scenario's capture points and an eBPF collector on the host records which invocation caused each connection, keyed by cgroup. The sensor runtimes, the scheduler and `assemble`, which turns the three into labels, follow. Version 5, October 2026.

This file is the project's memory. It records decisions and their rationale so later work (mine or Claude Code's) does not relitigate them without new evidence. *open* marks undecided items, *sketch* marks illustrative material that will change. Code blocks not marked *sketch* show what is implemented. What changed from earlier versions of this design, and why, is in `CHANGELOG.md`.

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

Each step is a CLI subcommand. The engineer stays in control at the describe step; the rest is mechanical. So far the static half of step 4 exists, `tiergen check`, and the backend-independent half of step 5, `tiergen build`, along with `tiergen impls list` for seeing which implementations are installed. Every other step is still design.

1. **collect** (helper, optional). A sensor configuration and a deployment file for a tap or span port, for whichever sensor the network uses. At least two full weeks to cover weekday and weekend cycles. The sensor's exact version and configuration are captured here and reused unchanged in generation, so real and generated traffic are read by the same instrument.
2. **fit** `tiergen fit <sensor-logs> --sensor zeek --out models/`. Reads the sensor's logs through its ingest adapter into the common event model (section 4.3), then: host inventory, role clustering into proposed actor kinds, behaviour model per role, implementation mix per role, service inventory, topology and address plan, diurnal rate curves, external-destination inventory. Emits `scenario_proposed.py`, resources under `models/`, and `fit-report.md` listing everything it could not map. Section 11.
3. **describe**. The engineer edits the scenario: confirms and names kinds, chooses bindings (default container, custom image, Windows container, VM), sets egress policy, adds attack schedules. Section 7.
4. **check** and **predict**. `tiergen check scenario.py [--models DIR] [--emit-json PATH]` runs the static checks (section 8) over a `scenario.py` or over IR JSON, reading resources from `models/` beside the scenario unless told otherwise. It prints diagnostics grouped as errors, warnings and not computed, and exits 0 with no errors, 1 with errors, 2 if the scenario cannot be loaded. `predict` then gives predicted sensor-level statistics from the scenario's denotation and a fidelity report against the real logs, before anything runs (section 9). Iterate until acceptable.
5. **build** `tiergen build scenario.py --out run1/`. Runs the checks and refuses to write anything if there are errors. Implemented so far: the run directory holds the IR as `scenario.json`, the address plan as `addresses.json`, the routes as `routes.json`, one run manifest per infrastructure backend as `manifest.<backend>.json` (section 10), one projected program per instance as `program.<instance>.json` with every resource inlined, and a copy of `models/`, so it checks on its own. Still to come: sensor configuration, attribution configuration, label schema.
6. **run** `tiergen run run1/`. Hosts up, agents started, clock sync verified, capture started, schedule executed, logs collected. Implemented so far: the hosts-up and hosts-down halves, as `tiergen infra up run1/` and `tiergen infra down run1/`, for Docker. `up` builds the agent image from the workspace if the daemon lacks it (the daemon must run with its user-namespace remap on, section 10), starts every default host's agent on its program, and writes `state.<backend>.json`, the substrate's names and ids for every host, bridge and image, which attribution and capture read; the agents write under `run1/out/<instance>/`: `invocations.jsonl`, `agent.log`, and each service's own files. `tiergen capture start run1/` and `stop run1/` capture at the scenario's capture points in between (section 10): `run1/capture/<point>.pcapng`, `capture.json` and `offsets.json`.
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

Interface, as implemented in `interfaces/` (docstrings omitted; no implementation lives there):

```python
class Capability(Enum):
    APP_EVENTS = auto()           # per-request/per-operation records under a connection
    TLS_JA4 = auto()
    TLS_JA3 = auto()
    HTTP_USER_AGENT = auto()
    SSH_STRINGS = auto()
    SMB_DIALECT = auto()
    X509 = auto()
    # extends without touching ConnEvent or any core consumer

@dataclass(frozen=True, slots=True)
class CapabilityInfo:
    schema: str                   # reference to the typed shape this adds to AppEvent.fields
    coverage: float               # fraction of applicable events populated, measured at fit time

@dataclass(frozen=True, slots=True)
class SensorDescriptor:           # static: what the checker reads, without running anything
    id: str                       # "zeek" | "suricata" | ...; equals its entry-point name
    versions: tuple[str, ...]     # sensor versions the backend can reproduce
    modes: tuple[SensorMode, ...] # "offline" | "live"
    capabilities: frozenset[Capability]   # the most any configuration can declare

class Sensor(Protocol):           # runtime: what fit, fidelity and assemble call
    @property
    def id(self) -> str: ...
    @property
    def version(self) -> str: ...
    def capabilities(self) -> Mapping[Capability, CapabilityInfo]: ...
    def ingest(self, native_logs: Path) -> Iterator[Event]: ...   # ConnEvent always; AppEvent iff APP_EVENTS
    def flow_key(self, event: Event) -> SensorFlowId: ...         # the sensor's native connection id
```

A sensor has two halves. The descriptor is data, registered under the entry-point group `tiergen.sensors`, and is all that checks 13 and 14 need. The Protocol is the runtime. A `SensorSpec` in a scenario declares a subset of its descriptor's capabilities: what this configuration of the sensor produces.

The events themselves are in `core/tiergen/core/events.py`. `ConnEvent.state` is one of `attempted`, `established`, `closed`, `reset`, `rejected`, `other`, which each ingest adapter maps its native states into. Duration and the byte and packet counters are `None` when the sensor left them unset for a connection, never zero. Both choices are provisional until the Zeek and Suricata adapters exist (section 16).

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

2026-09-18: "M0 ships no backend" means no backend runtime. Sensors and implementations register static descriptors, which the checker needs, so `backends/sensor/zeek`, `backends/sensor/suricata` and five `impls/` packages exist from M0 as data only; M1 adds their runtime in place. Reasons in `CHANGELOG.md`.

### 4.16 Tool-first quality bar

The output is a usable tool, not a paper. One-command install of `core`, `protocols`, `check`, `semantics` and `fit` on any platform without Docker; a CLI with clear errors; reproducible runs; documentation of the section 3 workflow written for a security engineer; fit and fidelity reports readable without knowing the internals. Novelty is not a criterion for including anything.

### 4.17 Repeated structure is a group; ties are wired, never looked up

A network bigger than one site repeats a structure: a team, a branch, a site. The IR holds that structure as nested `Group`s. Kinds stay global roles, which is what `fit` produces (section 11); a group says how many of each kind it holds, which data-plane networks they join, and, for every tie of every kind it holds, which groups' instances of the target kind the tie reaches. Instances are named by path, `corp/eng/workstation[3]`, as CDK, Pulumi and hardware description languages name theirs.

Wiring is explicit and total. Nothing is resolved by walking up the tree to the nearest group that happens to hold a matching kind, and nothing is inherited from a parent. That rule was considered and rejected (2026-10-02): every system surveyed that emits a flat artefact (CDK, Pulumi, Terraform, Amaranth, the network emulators, ScalaLoci, Choral) wires cross-scope references explicitly, and the closest precedent for the implicit rule, Modelica's `inner`/`outer`, is documented to bind names hard and to fall through silently when a kind is added to an enclosing group. The cost of explicitness is one dictionary per group, which a Python function writes once (`examples/two_teams`); the gain is that `single` and `optional` are checked exactly by counting, and `check` reports against the text the engineer wrote. Composition belongs in Python, per 4.6: the IR is the expanded form, not a template. Per-group overrides of bindings or rates are an open question until a scenario shows Python-side composition is not enough.

### 4.18 The data-link layer: segments, forwarding hosts, observation points

A `Segment` is one broadcast domain carrying one IPv4 prefix, with the VLAN id the real network gives it. Instances attach to segments through their group, one interface each. A kind that `forwards` makes its instances routers in the RFC 1812 sense, and routing is derived from them: a segment's next hop toward another is the forwarder that starts a shortest path, static routes are written into every host's program, and two equally short next hops are a check error rather than a guess. A `CapturePoint` is an observation point in RFC 7011's sense, on one segment or on several for a trunk SPAN, and says whether frames reach the sensor tagged. Addresses, hostnames, MACs (from a fitted OUI per binding) and routes are all functions of the IR (2026-10-02).

Why this and not a link graph, which is what RFC 8345, OpenConfig, Batfish and the verification literature use: the IR must be fittable from a sensor and a directory, and `fit` observes prefixes, VLAN tags, gateway MACs, DHCP and ARP but never a switch-to-switch link, a trunk or spanning tree, so links would be invented parameters (section 18). Every emulator driven by hand (Kathará, CORE, Emulab, ns-3, GNS3, Mininet) also makes the segment the first-class object, and none has a router type. What tiergen needs beyond them: a VLAN id and a `tagged` flag, because Suricata keys flows by VLAN and both sensors log tags and MACs; capture points over several segments, because a routed flow is seen once per segment crossed and `predict` and the label key must know; a fitted MAC prefix, because Docker's `02:42` and KVM's `52:54:00` are fingerprints; and a derived path, because the path decides what each observation point records. A forwarder is a transfer function on headers (Header Space Analysis); `forwards: bool` is its degenerate case and leaves room for NAT (M5) without a new object. Known limits, recorded: VLAN tags are not put on the wire inside the lab (plain bridges cannot) but inserted at the capture point; one prefix per segment until IPv6; planned addresses are static where a real workstation leases one, which a DHCP noise role (M5) can make look right by handing out exactly the planned leases.

### 4.19 The invocation's identity on Linux, and what the rate curve does

Decided 2026-10-05, after the first agent ran.

**A cgroup per invocation, under a user-namespace remap.** The attribution key on Linux stays the cgroup, as 4.18's identity chain assumed: the behaviour process moves itself into `/tiergen/<invocation>` under its container's cgroup before the call and back after, so every socket the invocation opens and every child it spawns carries it, concurrent behaviours on one host are told apart, and the eBPF join keys on a kernel-global id (`bpf_get_current_cgroup_id`, `bpf_skb_cgroup_id`) that no namespace changes. What it costs was the question. In a plain container the cgroup filesystem is read-only and writing it took `SYS_ADMIN` plus, on hosts with AppArmor, running unconfined, which is a short step from host root for a container whose job is to look like a workstation. With the daemon's user-namespace remap on, Docker mounts the container's cgroup filesystem writable and runc hands the container's cgroup directory to the remapped root, so the agent needs no capability at all; raw sockets, routes, privileged ports, static addresses, MACs, forwarding and named bridges all work as before, the host still sees the bridges that capture and libvirt need, and the only cost is that the run directory must carry an ACL for the remapped uid. Measured against a second daemon before this was written; the report is with the pull requests. The alternatives: process ids alone need fork tracking in the eBPF join and a second hook for raw sockets; an interval join alone cannot separate overlapping behaviours; a rootless daemon keeps its networks where the host cannot see them, which phase B cannot have. The remap is daemon-wide, so the backend detects it and refuses to bring agent hosts up without it; the pid fallback remains for what it was, a reason in the log. Two notes from task 7 (2026-10-07): the key is the cgroup's kernel id, `cgroup:<id>`, not its path, because that id is what `bpf_get_current_cgroup_id` and `bpf_skb_cgroup_id` report and the agent removes the directory as soon as the invocation ends, so nothing could resolve a path later, while the name carried no information the label lacks; and `AttributionBackend` works per run (`start(manifest, state, run_dir)`, `stop`, `records`), since one collector on the capture host instruments every container of a run and a guest backend sits behind the same three calls.

**The rate curve is a time change of the whole process.** A behaviour's semi-Markov process runs on an operational clock whose speed is the curve's multiplier for the local hour times the schedule's `set_rate` factor: at 2 every holding time takes half the wall time, idle and active alike; at 0 the process is frozen until the hour changes. This is the one reading under which "invocations per wall hour follow the curve" is exact, which is what `fit` measured and what section 9's denotation says, and it keeps the chain a chain, so the CTMC export stands. Scaling only idle states would keep in-session pacing fixed but needs a fit that tells sessions from gaps, which `fit` cannot do from connection timestamps; thinning caps the rate at the fitted maximum and leaves state visits without traffic; a chain per hour fits each matrix from that hour's events, a handful against a dozen free parameters for most hours, so it pools into bands anyway and still needs several times the capture for the same confidence. The time change's blind spot is a mix that changes by hour and not only a rate, night traffic being background services rather than rare browsing. Section 9's hourly per-service rate error is the metric that shows it, and the remedy is a second, always-on background behaviour per kind, which the IR allows today, not more chains.

---

## 5. Glossary

| Term | Meaning |
|---|---|
| Actor kind | A type of participant (`Workstation`, `DomainController`, `FileServer`, `WebServer`, `Printer`, `Attacker`, `InternetStub`) with an interface, behaviours and allowed platforms. Analogue of a ScalaLoci peer type. |
| Actor instance | One running actor of a kind, with a host, platform and data-plane address. |
| Host | Where an instance runs: Linux or Windows, container or VM, and the infrastructure backend that provides it. Carries platform, host type, backend, image or template. |
| Segment | One broadcast domain carrying one IPv4 prefix (RFC 4903), with the VLAN id the real network gives it; realised as one bridge. Data plane or management plane. The largest L2 object a sensor's evidence can recover; links between switches are not modelled because nothing observes them. |
| Forwarder | An instance of a kind that `forwards`: a host that passes packets between the segments it is on (RFC 1812). Routers, L3 switches, firewalls and NAT boxes are all this. Routes are derived from forwarders, never declared. |
| Capture point | An observation point (RFC 7011): every frame on one segment (a SPAN of a VLAN) or on several (a SPAN of a trunk), `tagged` if the frames keep their 802.1Q tags. A routed flow is seen once per segment it crosses, which the label key accounts for. |
| Interface (actor) | Endpoints an actor serves (protocol, port, transport) and ties it requires. |
| Tie | A typed relation from one kind to another with multiplicity `single`, `optional` or `multiple`. Who may talk to whom. |
| Behaviour | A stochastic process over actions attached to a kind, with a time-of-day rate function. |
| Action | What a behaviour state does. States are abstract (`http_get_small`, `smb_read`, `kerberos_tgs`) and derived from the common event model; each maps to an `Action(signature, tie, params, select)` or to `None` for a silent state. The signature is what to run, the tie whose targets to run it against, `params` a value for each parameter the signature declares (a literal, or a weighted choice sampled per invocation, inline or from a resource), and `select`, for a `multiple` tie, whether an invocation hits all targets or one drawn uniformly. |
| Signature | A protocol-level primitive (`http.get`, `smb.read`) with a role, typed parameters and an expected traffic shape (connections, transport, port, permitted follow-on signatures, reuse semantics). A client signature lists the endpoint protocols its target may serve. A server signature (`http.serve`) stands for serving and is what a binding selects a service implementation under. Defined in `protocols/`. The IR references signatures, never tools. |
| Implementation | A per-tool package providing signatures (`PrimitiveImpl`), running a service (`ServiceImpl`) or adapting an external framework (`AdapterImpl`). It has a manifest, `impl.toml`, and a runtime. Registered by what it provides. |
| Descriptor | The static half of a sensor, an implementation or an infrastructure backend, as data: `SensorDescriptor`; `ImplDescriptor`, decoded from `impl.toml`; `InfraDescriptor`, the hosts a backend offers and the capabilities it can grant each. Discovered through entry points. The checker reads descriptors and never imports a runtime. |
| Sensor | A passive traffic sensor behind the interface in 4.3: ingest and label, a pinned version and config, and a declared capability set. Configured under a name, which flow ids and labels key by, so one implementation can be configured twice. Zeek and Suricata are the first two. |
| Common event model | Schema-neutral events every sensor maps into. Required core `ConnEvent`: sensor-native connection id, 5-tuple, start and duration, bytes and packets per direction, state. Optional `AppEvent` (under `APP_EVENTS`): parent connection id, timestamp, protocol, normalised fields, capability-gated fingerprints. Every event keeps raw passthrough that core consumers may not read. |
| Capability | A named, typed extension a sensor declares above the required core: `APP_EVENTS`, `TLS_JA4`, `HTTP_USER_AGENT`, `SSH_STRINGS`, `SMB_DIALECT`, `X509`, extensible. Each carries a schema and a coverage claim. Consumers query capabilities and degrade explicitly when one is absent. |
| Coverage | The fraction of applicable events on which a sensor actually populates a capability's field, measured at fit time. Distinguishes a trustworthy distribution from a sparse one. |
| Binding | For a kind in a scenario: the host (default container, image, VM template), the implementation selection per signature, fixed or weighted, the fitted MAC prefix its instances carry, and the credentials resource its implementations authenticate with. |
| Topology | The segments of a scenario, the named capture points, and any pinned addresses by instance id. Which segments an instance joins is said by its group, one interface each. Every instance also joins the management segment. Addresses, hostnames, MACs and routes not pinned are derived in a fixed order, so the whole plan is a function of the IR. |
| Group | A nested scope holding instances: a team, a branch, a site. Named by path (`corp/eng`). Counts each kind it holds, attaches each to data-plane networks, and wires each tie of each kind it holds to the groups whose instances are its targets. Nothing is inherited. |
| Instance id | `path/kind[i]`: the group's path, the kind, the index. What pinned addresses, schedule targets, labels and backends name a host by. |
| Wiring | A group's `"kind.tie"` to group paths. The targets of a tie from an instance of that kind in that group are the instances of the tie's target kind in the named groups. `single` must find exactly one, `optional` at most one. |
| Scenario | Kinds, groups, bindings, topology, egress policy, schedule, duration, capture points, sensor set, fit provenance, coverage floor. |
| Resource | A named value a scenario refers to instead of carrying inline; fitted parameters are resources. JSON resources live as `models/<name>.json` and have a declared shape. Opaque resources, such as a sensor's configuration, only have to exist. |
| Schedule | Time-indexed events: start or stop behaviours, change rates, run scripted sequences (attacks). A target is a group path, `path/kind` or one instance. |
| Label key | `(scenario, instance, behaviour, action, invocation id, implementation, variant, targets)`: what an invocation is about to do, given to the implementation before it runs. `action` is the action map's key, the state the process entered; the signature it ran is the scenario's to say. Invocation ids are `instance/behaviour#n`. |
| Invocation record | What the agent logs once a primitive ran: the label key, the attribution key the kernel observer saw it as (platform-tagged: a cgroup path, a job object), start and end on the host's clock, the outcome, and a clock stamp (wall, monotonic, offset from the capture host) that moves the interval onto the pcap's timeline. |
| Label | An invocation record confirmed by attribution and attached, per configured sensor, to that sensor's connection id (keyed by sensor name and capture point) and sub-connection events. |
| Peer | What a tie resolves to for one instance: a target instance, its address on the segment reached, and the endpoints it serves there. |
| Attribution | Kernel-level join of observed connections to invocations, sensor-independent: eBPF (Linux), ETW or Sysmon (Windows). A record names the instance (never a substrate name), the attribution key seen, the process, the 5-tuple and the interval. |
| Fidelity | Distance between generated and real traffic at the common-event level, per metric in section 9. |
| Conformance | Distance between a run and its own model; separates implementation bugs from model gaps. |
| Diagnostic | What a static check reports: check id, severity, IR path, message. `error` makes the scenario ill formed; `warning` is a gap the engineer may accept; `not_computed` says part of a check could not run and names what was missing. |

---

## 6. Architecture

```
tiergen/                  uv workspace; one distribution per directory, all sharing the namespace tiergen.*
  core/                 ✔ IR, JSON codec, embedded DSL builders, resources, scenario loader, common event model, labels
  protocols/            ✔ signatures with expected traffic shapes, one module per protocol; no tool deps
  interfaces/           ✔ backend Protocols (Sensor, InfraBackend, AttributionBackend), Capability, Sensor and Infra descriptors, entry-point discovery; no impls
  check/                ✔ static checker: checks 1-16, diagnostics, runner
  cli/                  ✔ the `tiergen` command: `check`, `build`, `infra up`, `infra down`, `impls list`
  examples/             ✔ hq_lan, hq_lan_capgap, hq_lan_broken, linux_slice; each a scenario.py plus models/
  semantics/              process interface, semi-Markov default, product-process analysis, prediction, Storm export
  fit/                    ingestion via Sensor, host inventory, role clustering, behaviour and impl-mix fitting, proposal
  backends/
    sensor/
      _base/              common event model helpers shared by ingest adapters
      zeek/  suricata/  ◐ descriptor only; ingest and label runtime in M1
    infra/
      _base/            ✔ run manifests from the IR, the address plan and the implementation manifests
      docker/           ✔ Linux containers on the local daemon: networks, the agent image, agent hosts up and down
      libvirt/          ◐ descriptor only (nomad/, k8s/ later)
    attrib/
      _base/            ✔ the collector's event line, the join to records
      linux_ebpf/       ✔ CO-RE programs and loader, built in their image, run as a privileged helper
      windows_etw/          AttributionBackend for Windows guests (nfstream fallback)
    predict/              predicted sensor-level statistics and pre-run fidelity report
    assemble/             sensors over pcaps, attribution join, per-sensor labels, conformance and fidelity reports
  runtime/
    agent_linux/        ✔ `tiergen-agent`: the program, services first, one process per behaviour, a cgroup per invocation, the invocation log
    agent_windows/        the same with a job object per invocation
    scheduler/            management-plane orchestrator: hosts, agents, clock check, schedule, log collection
    capture/            ✔ dumpcap at capture points, pcapng reader and writer, tag insertion, per-host clock offsets
  impls/                  one package per tool, discovered via entry points (6.1)
    _base/              ✔ descriptor and manifest schema, loader, registries (descriptors and runtimes), the Context, ServiceContext, PrimitiveImpl/ServiceImpl/AdapterImpl Protocols
    httpx/ nmap/        ✔ runtimes        smbclient_win/ ◐ manifest only          playwright/ curl/ dig/ paramiko/ impacket/ ...   primitive impls
    nginx/              ✔ runtime         samba/ ◐ manifest only                  apache/ caddy/ unbound/ bind/ postfix/ dovecot/ win_fileserver/ ...  service impls
    caldera/ atomic/ ghosts/ metasploit(opt-in)/                                  adapters
  evaluate/               reference detectors over common-event features, FP-rate harness against held-out real logs
  CHANGELOG.md  CONTRIBUTING.md  cchk.toml  .pre-commit-config.yaml  .github/workflows/ci.yml
```

✔ implemented, ◐ data only, unmarked not started. A member's code is at `<member>/tiergen/<name>/`, for example `core/tiergen/core/ir.py` and `impls/nginx/tiergen/impls/nginx/impl.toml`, with its tests in `<member>/tests/`. There is no `tiergen/__init__.py` anywhere: `tiergen` is a PEP 420 namespace, so modules import as `tiergen.core.dsl`, never from `tiergen` itself. The Protocols each backend family implements live in `interfaces/`, not in the family's `_base`.

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

**`protocols/`**. One module per protocol. A signature has a role, typed parameters and an expected traffic shape: number of connections (or `many`), transport, destination port when it is fixed, permitted follow-on signatures (a DNS lookup before an HTTP request, a Kerberos ticket before an SMB session), and reuse semantics (may this primitive ride on a connection an earlier invocation opened, and if so per-request labels rely on `AppEvent`s). Attribution uses the shape to match observed connections to an invocation; conformance tests use it to check implementations. Adding a protocol touches one module.

Serving is a signature too. `http.serve`, `dns.serve`, `smb.serve`, `kerberos.serve` and `ssh.serve` have role `server`, open no connections, and are what a binding selects a `ServiceImpl` under. They never appear in an action map. A client signature lists the endpoint protocols a tie's target may serve, so `http.get` fits an `https` endpoint. Scans list none: a scan needs a tie to aim at, not an endpoint served on the other side.

**`impls/<tool>/`**. One workspace package per tool with its own dependencies. Layout by tool, because tools are what get installed and pinned and one tool often serves several protocols (Impacket: SMB, LDAP, Kerberos, DCERPC). Navigation by protocol through the registry: `tiergen impls list --protocol smb --platform windows`. Registration through the entry-point group `tiergen.impls`, discovered with `importlib.metadata`; core never imports implementations at load time, so an uninstalled one is simply unresolved.

Manifest per package (`impl.toml`). It decodes into a frozen `ImplDescriptor` through `tomllib` and the IR's codec, strictly: an unknown key or a wrong type is an error naming the file and the path.

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

A service says what it serves, which is what check 6 compares with a kind's interface. An adapter lists its catalog, `catalog = [{ id = "...", name = "...", attack_ids = ["T1558.003"] }]`, so check 8 validates a sequence's references without importing the adapter.

```toml
id = "http.nginx"
version = "0.0.1"
kind = "service"
provides = ["http.serve"]
[host]
platforms = ["linux"]
binaries = ["nginx"]
[service]
served = [
    { protocol = "http", port = 80, transport = "tcp" },
    { protocol = "https", port = 443, transport = "tcp" },
]
```

Runtime interfaces in `impls/_base`. A package registers its runtime class under a second entry-point group, `tiergen.impls.runtimes`, by the same id; only the agent loads it, on the host that runs it.
- `PrimitiveImpl`: `run(ctx, signature, **params) -> Outcome`. One package provides several signatures, so the call says which. Executes on the client actor's host inside the invocation's cgroup (Linux) or job object (Windows). `ctx` gives the label key, the invocation id, the targets this invocation aims at (one for `select="one"`, every peer for `"all"`), every tie resolved to peers, the selected variant and the `impl` stream as a seeded `Random`. A tool failure is an outcome, not an exception; an implementation that raises is logged and recorded as `failed`.
- `ServiceImpl`: `start(ctx)`, `healthcheck(ctx) -> bool`, `stop(ctx)`, `served() -> tuple[Endpoint, ...]`, the same endpoints the manifest declares. A service is not an invocation, so its `ServiceContext` carries no label: the instance, the served endpoints, a directory under the run's outputs for its logs, and a seeded `Random`.
- `AdapterImpl`: `catalog() -> Iterable[CatalogEntry]`, the same entries the manifest lists; `run(ctx, catalog_id, **params)`. Catalog entries are data, never one file per ability.

Implemented (2026-10-02): `http.httpx` runs `http.get` and `http.post_form` with one client per invocation, so a connection never outlives its invocation; `http.nginx` runs nginx in the foreground as a child of the agent, serving a generated site from under its output directory with the access log beside it, `https` on a self-signed certificate until the lab CA exists; `scan.nmap` runs one nmap over the targets' addresses, nmap's own in everything that reaches the wire except name resolution. Their tests are unit tests against this host; the conformance tests that measure a connection's shape and fingerprints need capture (task 6) and come with it.

**Selection is data.** A binding resolves each `(kind, signature)` to one implementation or a weighted set sampled per instance. Weights come from `fit` (4.10) or the engineer. Resolved id and variant go into every label.

**Conformance test per implementation.** Each primitive implementation ships a test that runs it against a reference service implementation in a two-host fixture and asserts that the observed connections from the invocation match the signature's traffic shape. The test also records the implementation's measured fingerprints (JA4, user agent, SSH strings) and per-primitive connection profiles (bytes, packets, duration distributions), which `predict` uses. It catches tools that quietly open extra connections that would otherwise become unattributed traffic.

---

## 7. IR

Frozen slotted dataclasses in `core/tiergen/core/ir.py`, shown here without docstrings. The root has `to_json` and `from_json`; both go through `core/tiergen/core/codec.py`, a codec driven by the type annotations that serves every dataclass in the project, `impl.toml` manifests included. Decoding is strict: an unknown key, a missing field, a wrong shape or a non-finite float is an error carrying the path of the offending value, for example `kinds[2].behaviours[0].process.dwell[1].family`. Nodes have no separate id. Names are the ids, and check 11 enforces their uniqueness.

A field typed `... | str` takes an inline value or the name of a resource that holds one, so a fitted process can live entirely under `models/`. A field typed plain `str` and commented as a resource is always a name. Names are resolved by the checker, never in the IR.

```python
from dataclasses import dataclass, field
from typing import Literal

Multiplicity = Literal["single", "optional", "multiple"]
Transport = Literal["tcp", "udp"]
Platform = Literal["linux", "windows"]
HostType = Literal["container", "vm"]
EgressPolicy = Literal["stub", "allowlist", "none"]
ScheduleOp = Literal["start", "stop", "set_rate", "run_sequence"]
SensorMode = Literal["offline", "live"]
SensorRole = Literal["label", "fit", "both"]
Plane = Literal["data", "management"]
Select = Literal["all", "one"]
ParamScalar = str | int | float | bool

@dataclass(frozen=True, slots=True)
class Endpoint:
    protocol: str
    port: int
    transport: Transport

@dataclass(frozen=True, slots=True)
class Tie:
    name: str
    target_kind: str
    multiplicity: Multiplicity                   # single = exactly one peer, optional = 0..1, multiple = 0..n

@dataclass(frozen=True, slots=True)
class Distribution:
    family: str                                  # "exponential" | "lognormal" | "weibull" | "empirical"
    params: tuple[float, ...] | str              # inline or resource; (mean), (mu, sigma), (shape, scale), (samples...)

@dataclass(frozen=True, slots=True)
class SemiMarkov:
    states: tuple[str, ...] | str
    initial: tuple[float, ...] | str
    transitions: tuple[tuple[float, ...], ...] | str
    dwell: tuple[Distribution, ...] | str        # one per state
    rate: str | None                             # resource: hourly multipliers, 24 or 168 values

@dataclass(frozen=True, slots=True)
class Choice:                                    # a parameter value sampled per invocation
    options: tuple[ParamScalar, ...]
    weights: tuple[float, ...]                   # one positive weight per option

@dataclass(frozen=True, slots=True)
class ChoiceRef:
    resource: str                                # a Choice held in a resource, e.g. fitted path popularity

ParamValue = ParamScalar | Choice | ChoiceRef

@dataclass(frozen=True, slots=True)
class Action:
    signature: str
    tie: str                                     # the tie whose targets the signature is run against
    params: dict[str, ParamValue] = field(default_factory=dict)   # one entry per signature parameter
    select: Select | None = None                 # for a multiple tie: hit all targets, or one drawn uniformly

@dataclass(frozen=True, slots=True)
class Behaviour:
    name: str
    process: SemiMarkov                          # later: Process union
    action_map: dict[str, Action | None] | str   # state -> Action, None = silent

@dataclass(frozen=True, slots=True)
class ActorKind:
    name: str
    serves: tuple[Endpoint, ...]
    ties: tuple[Tie, ...]
    behaviours: tuple[Behaviour, ...]
    platforms: tuple[Platform, ...]              # allowed platforms
    forwards: bool = False                       # a router (RFC 1812): passes packets between its segments

HostRefKind = Literal["default", "image", "template"]

@dataclass(frozen=True, slots=True)
class HostRef:                                   # Host.ref taken apart; HostRef.parse(text) -> HostRef | None
    kind: HostRefKind
    ref: str

@dataclass(frozen=True, slots=True)
class Host:
    platform: Platform
    host_type: HostType
    backend: str                                 # infrastructure backend that provides it: "docker" | "libvirt"
    ref: str                                     # "default" | "image:<ref>" | "template:<ref>"
    manifest: str | None                         # resource: endpoints a custom host serves; None if it serves nothing

@dataclass(frozen=True, slots=True)
class ImplSelection:
    signature: str
    choices: dict[str, float] | str              # "impl_id[:variant]" -> weight

@dataclass(frozen=True, slots=True)
class Binding:
    kind: str
    host: Host
    impls: tuple[ImplSelection, ...]
    mac_oui: str | None = None                   # "3c:ec:ef": the fitted MAC prefix; None = the substrate's, a realism gap
    credentials: str | None = None               # opaque resource: domain, accounts, secrets the implementations use

@dataclass(frozen=True, slots=True)
class ScheduleEvent:
    at_s: float
    target: str                                  # group path, "path/kind" or "path/kind[i]"
    op: ScheduleOp
    arg: str | float | None                      # start/stop: behaviour; set_rate: multiplier; run_sequence: "adapter:entry"

@dataclass(frozen=True, slots=True)
class SensorSpec:
    name: str                                    # unique per scenario; what flow ids and labels key by
    impl: str                                    # "zeek" | "suricata" | ...
    version: str                                 # pinned
    config: str                                  # resource: the exact config used on real + generated traffic
    mode: SensorMode
    capabilities: tuple[str, ...]                # Capability names this config declares
    role: SensorRole                             # "fit" or "both" marks the sensor the model was fitted from

@dataclass(frozen=True, slots=True)
class FitProvenance:
    sensor: str                                  # impl id of the fit sensor
    capabilities_used: tuple[str, ...]           # Capabilities fit actually relied on, recorded by `fit`
    coverage: dict[str, float]                   # measured coverage per capability used

@dataclass(frozen=True, slots=True)
class Segment:                                   # one broadcast domain with one IPv4 prefix, realised as one bridge
    name: str
    cidr: str
    plane: Plane                                 # data-plane segments are captured; the management one never is
    vlan: int | None = None                      # 802.1Q id as the real network numbers it

@dataclass(frozen=True, slots=True)
class CapturePoint:                              # an observation point (RFC 7011)
    name: str
    segments: tuple[str, ...]                    # one: a SPAN of that VLAN; several: a SPAN of a trunk
    tagged: bool = False                         # frames reach the sensor with their 802.1Q tags

@dataclass(frozen=True, slots=True)
class Topology:
    segments: tuple[Segment, ...]
    capture_points: tuple[CapturePoint, ...]
    addresses: dict[str, str] = field(default_factory=dict)   # instance id -> pinned address; the rest is allocated

@dataclass(frozen=True, slots=True)
class Group:
    name: str                                    # unique among siblings; path = parent + "/" + name
    parent: str | None                           # enclosing group's path; None at the top
    instances: dict[str, int]                    # kind -> count held here
    attachments: dict[str, tuple[str, ...]]      # kind -> its data-plane networks here; management is implicit
    wiring: dict[str, tuple[str, ...]] = field(default_factory=dict)   # "kind.tie" -> group paths of its targets

@dataclass(frozen=True, slots=True)
class Scenario:
    name: str
    kinds: tuple[ActorKind, ...]
    groups: tuple[Group, ...]
    bindings: tuple[Binding, ...]
    topology: Topology | str
    egress: EgressPolicy
    egress_overrides: dict[str, str]             # hostname or service -> real endpoint, for per-service swap
    schedule: tuple[ScheduleEvent, ...]
    start: str                                   # ISO 8601 with offset, the network's local time: anchors the rate curves
    duration_s: float
    capture_points: tuple[str, ...]              # the topology's capture points active in this run
    sensors: tuple[SensorSpec, ...]              # one or more; labels emitted per sensor
    fit_provenance: FitProvenance | str | None   # what fit relied on; enables the cross-sensor check
    seed: int
    coverage_floor: float = 0.5                  # check 15: below this, a capability fit relied on is sparse
```

Embedded DSL, in `core/tiergen/core/dsl.py`. The builders only assemble data: they refuse what the IR cannot represent, such as two kinds with one name, and leave everything else to the checker. `kind()` returns a handle that works as a dictionary key and as a tie target; `group()` returns one that works as a parent and as a wiring target, and fills in the one convenience the IR does not have: a tie left unwired is wired to the group itself if the group holds the target kind, else left for check 1 to report. `scenario` takes its kinds from its groups and bindings, in order of first mention. This is `examples/hq_lan/scenario.py`, as `fit` would propose it and the engineer would edit:

```python
from tiergen.core.dsl import (
    action,
    at,
    binding,
    dist,
    endpoint,
    group,
    host,
    hours,
    kind,
    resource,
    scenario,
    semi_markov,
    sensor,
    tie,
)

Dc = kind(
    "domain_controller",
    serves=[
        endpoint("kerberos", 88, "tcp"),
        endpoint("ldap", 389, "tcp"),
        endpoint("smb", 445, "tcp"),
        endpoint("dns", 53, "udp"),
    ],
    platforms=["windows"],
)
Fs = kind("file_server", serves=[endpoint("smb", 445, "tcp")], platforms=["windows", "linux"])
Web = kind("intranet_web", serves=[endpoint("https", 443, "tcp")], platforms=["linux"])

# The workstation's behaviour is what `fit` would emit: every part is a resource under models/.
Ws = kind(
    "workstation",
    ties=[tie("dc", Dc, "single"), tie("fs", Fs, "multiple"), tie("web", Web, "multiple")],
    behaviours=[
        semi_markov(
            "office",
            states=resource("ws_office.states"),
            initial=resource("ws_office.initial"),
            transitions=resource("ws_office.transitions"),
            dwell=resource("ws_office.dwell"),
            rate=resource("ws_office.rate_week"),
            action_map=resource("ws_office.action_map"),
        )
    ],
    platforms=["windows", "linux"],
)

# The attacker's behaviour is written inline, as an engineer adding it by hand would.
Atk = kind(
    "attacker",
    ties=[tie("dc", Dc, "single"), tie("victim", Ws, "multiple")],
    behaviours=[
        semi_markov(
            "recon",
            states=["idle", "syn_scan"],
            initial=[1.0, 0.0],
            transitions=[[0.0, 1.0], [1.0, 0.0]],
            dwell=[dist("exponential", [600.0]), dist("exponential", [45.0])],
            action_map={
                "idle": None,
                "syn_scan": action("scan.tcp_syn", "victim", {"ports": "1-1024"}, select="all"),
            },
        )
    ],
    platforms=["linux"],
)

# One site. Every kind here is wired to this group by default, which is where it lives.
Hq = group(
    "hq",
    instances={Ws: 60, Dc: 1, Fs: 2, Web: 1, Atk: 1},
    attachments={Dc: ["lan"], Fs: ["lan"], Web: ["lan"], Ws: ["lan"], Atk: ["lan"]},
)

S = scenario(
    "hq_lan",
    groups=[Hq],
    bindings={
        # A VM from a template is a custom host: its manifest says what it serves. The
        # workstation is one too, and serves nothing, so it needs no manifest.
        Dc: binding(
            host(
                "windows",
                "vm",
                "template:win2022-dc",
                backend="libvirt",
                manifest=resource("hq_lan.dc_manifest"),
            ),
            mac_oui="00:15:5d",
        ),
        Ws: binding(
            host("windows", "vm", "template:win11-workstation", backend="libvirt"),
            {
                "http.get": {"http.httpx": 1.0},
                "smb.read": {"smb.windows_native": 1.0},
                "kerberos.tgs": {"smb.windows_native": 1.0},
            },
            mac_oui="00:15:5d",
        ),
        # Default hosts serve through the service implementations selected here.
        Fs: binding(
            host("linux", "container", backend="docker"),
            {"smb.serve": {"smb.samba": 1.0}},
            mac_oui="3c:ec:ef",
        ),
        Web: binding(
            host("linux", "container", backend="docker"),
            {"http.serve": {"http.nginx": 1.0}},
            mac_oui="3c:ec:ef",
        ),
        Atk: binding(
            host("linux", "container", backend="docker"),
            {"scan.tcp_syn": {"scan.nmap": 1.0}},
            mac_oui="3c:ec:ef",
        ),
    },
    topology=resource("hq_lan.topology"),
    egress="none",
    schedule=[at(0, Hq, "start", "office", kind=Ws), at(hours(30), Hq, "start", "recon", kind=Atk)],
    start="2026-10-05T08:00:00+02:00",
    duration_s=7 * 24 * 3600,
    capture_points=["core-switch-span"],
    sensors=[
        sensor(
            "zeek",
            "7.0.11",
            resource("hq_lan.zeek"),
            "offline",
            caps=["APP_EVENTS", "TLS_JA4", "HTTP_USER_AGENT", "SSH_STRINGS", "SMB_DIALECT", "X509"],
            role="both",
        ),
        sensor(
            "suricata",
            "7.0.7",
            resource("hq_lan.suricata"),
            "offline",
            caps=["APP_EVENTS", "TLS_JA4", "HTTP_USER_AGENT"],
            role="label",
        ),
    ],
    fit_provenance=resource("hq_lan.fit_provenance"),
    seed=1,
)
```

The whole LAN is one group, `hq`, so every tie is wired to `hq` by default. `examples/two_teams` is the same idea with structure: a `team()` function returns a group with its own LAN and file server, wires the workstations' `dc` tie to the organisation, and is called twice. The workstation's behaviour is what `fit` emits, every part a resource under `models/`, its action map included: there `http.get` draws its `path` from a fitted popularity resource, `smb.read` has a literal `share` and an inline choice of `path`, and `kerberos.tgs` a literal `spn`. The attacker's is written inline, as an engineer adding it by hand would. The DC and the workstations are VMs from templates, custom hosts provided by libvirt. The DC's manifest resource says what it serves; a workstation serves nothing and needs none. The file server, web server and attacker are default hosts provided by Docker, which serve through the service implementations selected for them.

`examples/hq_lan_capgap` is the same scenario with one resource changed: its fit provenance says `fit` relied on `SMB_DIALECT`, which the Suricata label sensor does not declare. Check 14 warns: a detector trained on SMB-dialect-derived features will not see them in a Suricata deployment. The engineer either drops that capability from the fit, adds the Suricata config that provides it, or accepts the gap knowingly. `examples/hq_lan_broken` makes six deliberate mistakes and fails checks 1, 4, 5, 9, 10 and 12, plus the consequences check 10 draws from them.

*Sketch*, not checkable before M5: external destinations and adapter-driven attacks take the same shapes. An `internet_stub` kind bound with `{"internet.serve": {"internet.stub": 1.0}}`, `egress="stub"` with `egress_overrides={"update.microsoft.com": "real"}`, an attacker bound with `{"attack.run": {"attack.caldera": 1.0}}`, and a schedule entry `at(hours(30), Atk, "run_sequence", "attack.caldera:discovery-then-kerberoast")`, which check 8 resolves against the adapter's catalog.

---

## 8. Static checks

All sixteen checks are implemented in `check/`, one module each, with unit tests and, where the input space allows, a hypothesis property test.

A diagnostic has a check id (`C01` to `C16`), a severity, an IR path and a message. `error` makes the scenario ill formed. `warning` is a gap the engineer may accept knowingly. `not_computed` says part of a check could not run and names what was missing; it is never a pass. Check 5 is the only check that reports a missing or ill-shaped resource. Every other check skips what it cannot resolve, so one missing file is one diagnostic, not a cascade.

1. Every group's instance counts name kinds and are not negative; tie targets exist. Every tie of every kind a group holds is wired there, to groups that exist, and the wiring satisfies the multiplicity exactly: `single` reaches exactly one instance of the target kind across the named groups, `optional` at most one, `multiple` any number. A wiring key for a kind the group does not hold, or a tie the kind does not have, is an error. Nothing is looked up by walking the tree, so an unwired tie is reported here rather than guessed at run time. Plain counting; the Z3 dependency of M0 went with the old reading of multiplicities.
2. Every action is directed at a tie its kind has, and the tie's target serves an endpoint the signature accepts (protocol, transport). A scan needs the tie and no endpoint.
3. Every behaviour state has exactly one action-map entry, an action or an explicit `None`; no entry names a state that does not exist; every signature is a known client signature.
4. Initial distribution and transition rows are stochastic; the matrix is square over the states; all states are reachable from the initial support; one dwell per state; a rate resource has 24 or 168 entries.
5. Resource references resolve, and resolved shapes match declared shapes, distribution parameters included. Sensor configurations and the topology are opaque: they only have to exist.
6. Every kind with instances has exactly one binding, and the host satisfies the kind's interface. A default host serves what its selected service implementations serve, and an endpoint counts only if every weighted alternative of some selection serves it. A custom host (`image:`, `template:`) serves what its manifest resource lists.
7. Binding platform is in the kind's allowed platforms. The binding's backend is installed and offers that platform and host type. Every chosen implementation supports the platform, and the host capabilities it needs (`net_raw`, admin) are ones the backend's descriptor says it can grant such a host. A VM owns its kernel, so there a backend has nothing to grant and nothing to refuse. On a default host every chosen implementation agrees on the base image. A binding without a MAC prefix gets the substrate's, which a sensor can fingerprint: a warning.
8. Every client signature a kind's actions use has a selection in its binding; every choice names an installed implementation that provides the signature, and a variant it has; weights are positive; a `run_sequence` names an installed adapter and an entry of its catalog.
9. Exactly one management segment, overlapping no data-plane segment. Every capture point is defined once and observes segments that exist and are data-plane: a capture on the management segment records the tool, not the network. At least one capture point is active, and every active one is defined. A wired tie neither of whose ends sits on an observed segment would produce invocations no sensor sees: a warning. A `live` sensor's capture interface is `not_computed`, because a `SensorSpec` does not name one yet; M1 runs sensors offline.
10. The address plan and the routes (section 7; `core/tiergen/core/addressing.py`, `routing.py`) are complete and collision-free: every CIDR parses, no segment is defined twice, every segment has room for the instances attached to it, every pinned address belongs to an instance, lies on a segment that instance joins, and is free; no instance has two equally short next hops to a segment. Data-plane segments do not overlap each other. Each group's attachments name real kinds and data-plane segments, and a kind a group holds joins at least one data-plane segment in that group. Every wired tie is reachable: source and target share a segment, or the source has a route to the target's segment through forwarders. That the backend can provide each bound host is check 7's. Whether egress is backed by an `internet_stub` kind or an allowlist resource, and whether every `egress_overrides` key is a fitted external destination, is `not_computed` unless egress is `none`: the destinations come from `fit` (M4).
11. Label tuple unique per invocation: kind, tie, behaviour and state names are unique where a label is built from them, group paths are unique, every `parent` names a group, no group is named like a kind its parent holds (a schedule target could mean either), and no signature is selected twice in a binding. No primitive executable outside a labelled context: a client implementation selected for a signature no action invokes is a warning.
12. `Scenario.start` is ISO 8601 with a UTC offset. Schedule events reference defined targets at times within `duration_s`: a group path (every instance under it), `path/kind` (every instance of that kind under the group) or `path/kind[i]` (one instance), each resolved against the scenario by `tiergen.core.groups.select`. `start` and `stop` take a behaviour every targeted kind has, `set_rate` a non-negative multiplier, `run_sequence` an `adapter_id:catalog_entry` string.
13. At least one sensor is configured and sensor names are unique. Each `SensorSpec` names an installed sensor whose descriptor lists the pinned version and the mode, and every declared capability is one the descriptor can declare. An installed sensor meets the required core by construction. Reproducing the config itself is the sensor backend's job in M1.
14. Cross-sensor consistency: every capability in `fit_provenance.capabilities_used` is declared by every sensor whose `role` includes `label`. A violation is a warning, not an error, and names the capability, the fit sensor and the label sensor lacking it, because the engineer may accept the gap deliberately. Exactly one sensor has a `role` including `fit`, and it matches `fit_provenance.sensor`; these two are errors. A scenario without fit provenance has nothing to compare.
15. Coverage sanity: every capability `fit` relied on has measured coverage above the scenario's `coverage_floor` (default 0.5); below it, or with no coverage recorded, warn that the fitted distribution for that capability is sparse.
16. Action parameters: an action on a `multiple` tie says `select`, all or one, and one on any other tie does not; every required parameter of the action's signature has a value and no parameter is unknown; literals and choice options have the declared type; a choice has at least one option and one positive weight per option. A choice held in a resource is resolved by check 5.

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

- **Agents** (`agent_linux` implemented, `agent_windows` phase B). Receive the projected program: behaviours with every resource resolved, action map, resolved implementations and variants, ties resolved to peers (instance, address, served endpoints), the server signatures to start, the schedule narrowed to the instance, static routes, hostname, seed. `tiergen-agent <program.json>` reads nothing else. It validates what the checks cannot see (dwell families and their parameters: exponential takes a mean, lognormal mu and sigma of the log, weibull shape and scale, empirical the samples), starts one service per server signature and waits for its healthcheck (a service that cannot be loaded, started or reached is logged and counted, and the host stays up with its addresses and routes), then runs each behaviour in a forked process of its own; scenario time starts when the services are up. The loop: a behaviour runs between its `start` and `stop` events and never before a `start`; on entering a state it runs the state's action, then holds for a time drawn from the state's dwell distribution in operational time, which the rate curve and the schedule's `set_rate` factor turn into wall time by a time change of the whole process (at multiplier 2 everything happens twice as fast, at 0 the process freezes until the hour changes; the curve is read at `Scenario.start` plus scenario time, by hour or by weekday and hour, Monday first), then draws the next state. Draws come from three streams named by the behaviour's id, `instance/behaviour`: `behaviour` for states and holding times, `selection` for targets, implementation and `Choice` parameters, `impl` handed to the implementation. The implementation runs inside a fresh cgroup (Linux) or job object (Windows), and an `InvocationRecord` (label key, attribution key, start, end, outcome, clock stamp) goes to `invocations.jsonl`, one line per record, with the agent's log beside it; the clock offset is 0 until the scheduler measures it. Streams are derived from the scenario seed (`tiergen.core.sampling`), so the run is a function of IR and seed whatever order agents start in, and the loop under a fake clock is what the tests hold that against. Long-lived processes such as a browser kept open across invocations are allowed when the scenario asks for them; their per-request labels rely on interval matching and carry a confidence field.
  On Linux the cgroup is the behaviour process moving itself into `/tiergen/<invocation>` under the container's cgroup root before the call and back out after, so every socket the invocation opens and every child it spawns carries the cgroup. That needs the cgroup filesystem writable, which the backend arranges through the daemon's user-namespace remap (decision 4.19) and no capability. Without a writable cgroup filesystem the key is the behaviour process's id, told apart by interval, and `agent.log` says so; the eBPF join keys on either.
- **Infrastructure backend** (Docker, implemented). `tiergen build` writes one run manifest per backend the bindings name: the networks to create, each with its CIDR, planned gateway and plane, and the hosts, each with image, command, host capabilities as the substrate names them, and its attachments in order with planned addresses. A backend reads nothing but its manifest. The Docker backend pulls the images, creates one bridge network per segment with the planned gateway and the bridge name `build` fixed (`tg-` and a hash, so libvirt attaches its taps to the same bridge; data-plane segments `internal` while egress is `none`), creates each container with its hostname and planned MAC attached to its first segment at its address and connects it to each further segment one at a time (so interface order inside the container is the manifest's; two networks given at creation attach in Go map order), sets `net.ipv4.ip_forward` on forwarders, starts them, and installs each host's static routes with `ip route add` (which needs `NET_ADMIN`, added for hosts with routes). A container forwarding between two internal bridges and routes added inside containers were both tried against the daemon before this was written. Everything carries `tiergen.run=<run>`, so `down` needs no state and a failed `up` cleans up after itself. A default Linux host runs the agent from the backend's own image, `tiergen/base-linux`: Python, nginx, nmap, iproute2 and the workspace packages the agent imports, built through the SDK from a context the backend assembles out of the installed members (tests and caches left out) and tagged with a hash of that context, so a source change makes a new image and an unchanged one is reused; the id that ran goes into the run state. Such a host gets the run directory mounted read-only at `/tiergen/run`, its own `run/out/<instance>` read-write at `/tiergen/out` and a private cgroup namespace, and runs `tiergen-agent /tiergen/run/program.<instance>.json`. Agent hosts need the daemon's user-namespace remap (`"userns-remap"` in `daemon.json`, decision 4.19): under it the daemon mounts the container's cgroup filesystem writable and owned by the container's root, so the cgroup per invocation costs no capability, and `up` refuses to bring an agent host up without it rather than fall back to a privileged container. The remapped root is a host uid, so `up` sets ACLs letting it read the run directory and write its own `out/<instance>`; what the agents write belongs to that uid and is readable by the user. A custom image runs its own entrypoint and gets none of that, and could opt out of the remap per container (`--userns=host`) if it ever needs host root, which nothing planned does. `HostSpec.agent` is what tells the two apart.
- **Scheduler** (management plane): brings hosts up through the infra backend, starts agents, verifies clock sync, starts capture and any live sensors, drives the schedule, collects logs, stops.
- **Attribution** (sensor-independent kernel truth; Linux implemented 2026-10-07, `backends/attrib/linux_ebpf`). Linux: eBPF programs on the capture host, libbpf with CO-RE built once in their own image against BTF and run through the daemon as a privileged helper (`--privileged --userns=host --pid=host --network host`, the host's cgroup tree read-only), so nothing compiles at run time and the image is host-independent; the toolchain was chosen over bcc because bcc compiles at load time against the host's kernel headers, which the daemon route exists to avoid. The hooks: kprobe and kretprobe on `tcp_v4_connect` (the originator's 4-tuple on return), kretprobe on `inet_csk_accept` (the responder), kprobe on `tcp_close` (the interval's end, by socket), kprobe on `udp_sendmsg` and kretprobe on `udp_recvmsg` (the peer from the message), and a `cgroup_skb` egress program attached to each container's cgroup, which sees every packet of every socket in it, raw sockets included, and reports the first packet of each (cgroup, flow), so a SYN scan costs one event per port. Every event carries the cgroup id of the task or socket that caused it, which is the key the agent recorded (4.19), and the id of the cgroup at the containers' depth, so user space maps events to instances by the kernel's own numbers and never resolves a path after the fact. The collector is a C program that prints one JSON line per event on the host's wall clock; everything above that line is Python (`backends/attrib/_base`): the join opens a record on `connect` or `accept` and ends it on the matching `close`, makes UDP exchanges and raw packets records of their own, and drops, counted, anything from a cgroup that is no container of the run. `tiergen attrib start run1/` and `stop run1/` write `run1/attrib/containers.json` and `events.jsonl`; `AttributionRecord`s (instance, key, process, 5-tuple, interval) come from `records()`. Windows: Sysmon event 3 (network connection with PID) by default, ETW `Microsoft-Windows-Kernel-Network` as the alternative. VMs use their guest OS backend. Fallback: nfstream system-visibility mode, coarser. Each configured sensor's label step (task 9) matches records to invocation records by key and interval, and maps them onto its own flow ids, keyed by sensor name and capture point, by 5-tuple and time window. Known holes, handled by flagging rather than guessing: DNS via a system resolver daemon, OS background traffic, connection reuse across invocations in one process.
- **Capture** (implemented 2026-10-06, `runtime/capture`). `tiergen capture start run1/` reads the IR and the run state and nothing else: for every active capture point it starts one dumpcap on the host over the bridges of the point's segments, in the point's order, so interface id i of `capture/<point>.pcapng` is segment i; `stop` sends SIGINT, which has dumpcap close the file, then rewrites a `tagged` point's file with an 802.1Q header on every frame of a segment that has a VLAN id, through the tool's own pcapng reader and writer (sections, interfaces with their timestamp resolution, packets; other blocks copied), and leaves `capture/capture.json` with what was captured and how many frames each point got tagged. Before dumpcap starts, every backend `quiesce`s its hosts: segmentation offloads off, so a capture holds wire-sized frames. On Docker that is TSO and GSO off on each container's own interfaces, done by a helper that joins the container's network namespace with `NET_ADMIN`; measured first, a 20 MB transfer showed 65 KB frames on the bridge until the sender's offloads were off and 1514 bytes after, with the host-side veths and the bridge making no difference. `capture/offsets.json` holds each host's clock offset to the capture host and how it was known: zero and `shared-kernel` for containers, by construction; VMs say `unmeasured` until phase B measures them (chrony on Linux, w32time on Windows, PTP where the substrate has it), and the join applies the offsets. The run's first seconds are not captured, since `infra up` starts the agents at once; the scheduler (task 9) splits creating hosts from starting them so capture can start between.
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
8. **Topology, groups and address plan.** Subnets from observed addresses, gateway behaviour from `ConnEvent` routing patterns, VLAN hints from the engineer; or, where the network has a directory, its sites, subnets and organisational units read directly, which propose groups and their networks from better evidence than traffic.
9. **Privacy.** Fitted resources can carry hostnames, SNI and user agents. `fit --anonymise` replaces them with consistent pseudonyms; the report says what was replaced.

Identifiability caveat, recorded so nobody rediscovers it: aggregate fits describe the role, not any individual. That is fine for the purpose in section 1; the fidelity report, not the fit, decides whether it is good enough.

---

## 12. Data plane

- **Hosts.** Linux containers (default, cheapest); Windows containers with Hyper-V isolation, through a Windows Docker daemon alongside the WSL2 Linux engine (two daemons, two contexts; developed and verified on a Windows host at the end of M1, section 16); Linux and Windows VMs via libvirt for the DC, Windows workstations with real Office and Outlook, and anything needing transport fidelity; a multi-node backend (Nomad or k8s) only once one machine runs out of room, per 4.9.
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

Core, protocols, checker, interfaces, CLI, as used so far: stdlib `dataclasses` (frozen, slots), `typing.Protocol` for the backend interfaces, `tomllib`, `importlib.metadata`, `argparse`, `ipaddress`. `z3-solver` was used by check 1 in M0 and dropped with groups: with explicit wiring the multiplicity check is plain counting. Tooling: `uv`, `hatchling`, `pyright` strict, `ruff`, `pytest`, `hypothesis`, `pre-commit`, `commit-check`. Planned and not used yet: `pydantic` at the user boundary (M0's boundaries, `impl.toml` and IR JSON, go through the IR's own codec), `networkx` (check 4's reachability is a short search and does not need it).

Semantics and fit: `numpy`, `scipy.stats`, `hmmlearn` or `pomegranate`, `scikit-learn` and `hdbscan` for role clustering, `polars` or `pandas` for logs (`zat` for Zeek, a small `eve.json` reader for Suricata), `stormpy` (Storm) or PRISM via subprocess.

Backends: `docker` (docker-py) with `types-docker` for the Docker daemons (2026-10-02: chosen over `python-on-whales`, which shells out to the CLI and brings pydantic into a backend package; the SDK is wrapped in one facade module checked at basic strictness), `libvirt-python`, `jinja2`, `ruamel.yaml`, `pyroute2`; later `python-nomad`, then a `kubernetes` client with KubeVirt if k8s is adopted.

Sensors: Zeek and Suricata as pinned containers driven over pcaps; ingest adapters written against their log schemas into the common event model.

Runtime and implementations: `playwright`, `httpx`, `paramiko`, `impacket`, `python-nmap`, `pymetasploit3` (opt-in), CALDERA REST API, GHOSTS REST API, `scapy` for the few crafted cases; on Windows, `pywin32` for job objects and services, `wmi`, `python-evtx` or the event log APIs for Sysmon.

Attribution and capture: `bcc`, `nfstream`, `dpkt`, `pyshark`.

Reference DSLs to read before designing `core/`: Amaranth (embedded DSL with typed IR and backends), Exo (research DSL over Python AST), JAX (tracing, multiple interpretations), Pyro `poutine` and `effectful` (effect handlers), Mininet `Topo` (topology DSL), Pulumi Python and cdk8s (program to manifests), Scapy and z3py (operator-overloading AST builders).

---

## 15. Roadmap

No dates. Each milestone ends with something an engineer can run.

- **M0 Core and interfaces.** Done, 2026-09-20. IR with JSON round-trip, embedded builders, resources, common event model, signatures for `http`, `dns`, `smb`, `kerberos`, `ssh` and `scan`, the backend Protocols with no implementations, descriptors for two sensors and five implementations, checks 1 to 8 and 11 to 15, `tiergen check` and `tiergen impls list`, three example scenarios, one ill-formed. Installs without Docker. Detail in `CHANGELOG.md`.
- **M1 Vertical slice, mixed platform.** Next. Developed on a Linux host: Docker for Linux containers, libvirt/KVM for Windows guests. First backends behind the M0 interfaces: Docker (Linux daemon) and libvirt; Zeek and Suricata sensors (offline); Linux eBPF and Windows ETW/Sysmon attribution; `agent_linux` and `agent_windows`. First runtimes, in the packages that already hold their manifests: `httpx`, `nmap`, `nginx`, native Windows SMB and Kerberos client, `samba`. Checks 9 and 10, and check 7's third clause. Scenario: one DC (Windows VM), one Windows workstation (VM), one Linux server, one attacker; stub egress; dumpcap; per-sensor labels keyed by Zeek `uid` and Suricata `flow_id`; `build`, `run`, `assemble`. Integration order inside the milestone: Linux path first, then the Windows guests. Deliverable and exit criterion: labelled pcaps plus Zeek and Suricata logs from one command on the mixed slice. After it, still in M1: the Docker backend for the Windows daemon, Hyper-V-isolated containers as a binding option for the workstation, developed on a Windows host. Task list at the end of section 18.
- **M2 Processes and prediction.** Semi-Markov behaviours, resources, weekly rates, `predict`, fidelity report against a real sensor-log sample, Storm export for the CTMC case, conformance report.
- **M3 Attribution hardening.** cgroup per invocation and `cgroup_skb` for scanners, interleaved actors on shared hosts, per-implementation conformance tests measuring fingerprints and connection profiles, label-exactness check against an isolated-mode run, DNS-resolver and connection-reuse holes handled by flagging.
- **M4 Fit.** Ingestion via the Sensor interface, host inventory, role clustering, action vocabulary, behaviour and implementation-mix fitting, proposed scenario emission, anonymisation, fit report. Drive it with the AD LAN.
- **M5 Internet and diversity.** Internet stub with lab CA, per-service `egress_overrides`, allowlist mode, noise roles, browser and client variants with fitted weights, Impacket and CALDERA attack sequences, GHOSTS adapter for Windows users.
- **M6 Scale (if needed).** Nomad backend for multi-node, evaluated before any k8s work; more service implementations as roles demand.
- **M7 Evaluation loop.** `evaluate/` harness and reference detectors; run the full workflow against a real AD LAN end to end; fix what the fidelity report exposes; write the engineer-facing documentation from that experience.

---

## 16. Open questions

- *closed 2026-09-20* First target substrate for M1: a Linux host, Docker for Linux containers and libvirt/KVM for Windows guests. It is the machine development happens on, and a Windows Docker daemon cannot run there. The same machine's Windows boot serves for the Windows daemon work at the end of M1.
- *closed 2026-09-20* Windows workstation in the M1 slice: a VM, which follows from the substrate. More faithful at the transport layer and simpler for real Office. The Hyper-V-isolated container becomes a binding option once the slice runs.
- *open* Multi-sensor labels: emit one label file per sensor (assumed) versus a unified label file with per-sensor id columns. Per-sensor files are simpler and match how the sensors are consumed downstream.
- *open* Common event model coverage: the field subset needed so fit and fidelity do not have to reach back into sensor-native logs. Grows as protocols are added; keep raw passthrough so nothing is lost. The first cut (4.3) fixes a six-value `ConnEvent.state` vocabulary and uses `None`, never zero, for counters the sensor left unset. Both are provisional until the Zeek and Suricata adapters exist.
- *open* The initial `Capability` set and each one's typed schema. The enum in 4.3 is a starting list; adding OT and ICS protocols (Modbus, DNP3, S7) will extend it, and the schemas need to be defined before the second sensor is written so they are not Zeek-shaped by accident. `CapabilityInfo.schema` already names such a shape, and none is defined anywhere yet.
- *open* Where the coverage floor for check 15 should sit per capability, and whether it should be per protocol rather than one global default.
- *open* Whether `fit` should offer to synthesise the config that would give a label sensor a capability it lacks (for example a Suricata config change), or only report the gap.
- *open* How much of the AD LAN's SaaS egress the stub can represent before the fidelity report says swap to real for a service.
- *open* Sensor version drift between collection and generation; pinning is required, upgrade policy is not defined.
- *open* Long-lived browser per user (realistic, interval-based per-request labels) versus browser per invocation (clean attribution, unrealistic reuse). Probably long-lived with confidence fields.
- *open* Keep a per-invocation netns isolation mode as an option for DetGen-style microstructure control.
- *closed 2026-09-20* Action parameters live in the IR: `Action.params` gives each parameter a literal or a weighted choice, inline or from a resource, and check 16 holds them to the signature. Leaving values to each implementation would have hidden them from `check` and `predict`, made them differ between implementations of one signature, and amounted to the invented parameters section 18 forbids. Still open: numeric parameters drawn from a distribution, not a finite choice (body sizes), which `Distribution` could serve once something needs it.
- *closed 2026-09-20* Infrastructure lives in the IR. `Host.backend` names the backend that provides a host, next to the platform and host type it already carried; the M1 slice uses two at once, Docker for containers and libvirt for VMs. Networks, the management network included, are in a typed `Topology`. Checks 9, 10 and 7 stay static over the IR, and the run manifest is complete with the IR alone. The cost, accepted: a scenario names its substrate, and moving it to another means editing bindings. A separate run configuration would have kept scenarios portable at the price of a second artifact and schema.
- *closed 2026-10-02* Repeated structure: nested groups with explicit wiring, decision 4.17. Instance ids carry the group path.
- *open* Per-group overrides: a different binding, browser mix or rate for one group. Deferred until a scenario shows that a Python function returning a group is not enough; the schedule's `set_rate` on a group path covers rates now.
- *open* Users and identities per group. Actors are hosts; a logged-in user is a behaviour. A directory's user population has an obvious home in a group once something needs it, probably the GHOSTS adapter in M5.
- *open* Directory import for `fit`: AD sites and OUs, NetBox sites and prefixes, as a source of groups beside observed traffic. Section 11 step 8 names it; nothing is designed.
- *closed 2026-09-20* `Topology` has a schema (section 7), and addresses are allocated deterministically from each network's CIDR with optional pins, in `core/tiergen/core/addressing.py`. An allocation order is not a statistic, so "no defaults" is untouched. Still open: links, gateways and per-link conditions (`tc netem`), which the schema has no place for yet.
- *open* IPv6, or a second prefix on a segment: `Segment.cidr` becomes a tuple when something needs it.
- *open* DHCP: planned addresses are static; a DHCP noise role (M5) handing out exactly the planned leases makes the wire look right without changing the plan.
- *open* Weighted target selection on a `multiple` tie (`select` is `all` or `one` today), and a distribution-valued parameter (body sizes) beside the finite `Choice`.
- *open* Long-lived processes: `ImplSelection.session` and a `confidence` on labels (M5, browsers).
- *closed 2026-10-05* The rate curve as a time change of the whole process versus scaling only the idle holding times: the time change, decision 4.19; the hourly per-service rate error is what would reopen it.
- *closed 2026-10-05* A cgroup per invocation cost the container `SYS_ADMIN` and no AppArmor confinement: under the daemon's user-namespace remap it costs nothing, decision 4.19; the backend moves to it next.
- *open* Deferred from the 2026-10-02 reviews, each to its task: Zeek `-D` for stable `uid`s (task 8; offloads on captured interfaces were task 6's and are done); per-platform join tolerance (task 9; the clock reference host is the capture host, whose clock the collector stamps events with); a run id distinct from the scenario name and a `lock.json` of digests and versions (task 9); guest network injection for libvirt (phase B); `set_rate` naming a behaviour; the responder's implementation in the label; shared-host actors (M3); the lab CA's home (M5).
- *open* `Fingerprint` in `impl.toml` covers what the 6.1 sample shows, JA4 and user agent. SSH strings, SMB dialects and OS strings have no slot, and 4.10 needs them.
- *open* Whether to require signed commits on pull-request branches through a second ruleset. `main` cannot require them: GitHub recreates every commit in a rebase-merge and cannot sign what it recreates.

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
- Python 3.12+, uv workspace, `pyright` strict, `ruff`. Members build with hatchling and share the PEP 420 namespace `tiergen.*`: no `tiergen/__init__.py` anywhere, a `py.typed` in every package. Every check has a unit test; every IR type has a JSON round-trip property test.
- The IR is JSON. No callables in it; signatures, implementations, sensors, resources by name.
- Nothing in `core/`, `protocols/`, `check/`, `semantics/`, `fit/` or `interfaces/` may assume Linux, Docker or network access. They install and run anywhere.
- A third-party SDK without complete types (z3 in M0, docker-py now) is used from one facade module per backend, checked at basic strictness; nothing else imports the SDK, and the facade is a Protocol the rest of the backend is tested against with a fake.
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
- Commits follow Conventional Commits 1.0.0 with a fixed scope list; branches follow Conventional Branch 1.1.0. `commit-check` enforces both from `cchk.toml`, in local hooks and in CI. `main` is linear and takes pull requests by rebase-merge only, behind the `lint`, `types`, `test`, `lock` and `conventions` checks. Signed commits are not required on `main` and required approvals are 0 while there is one maintainer; `CHANGELOG.md` says why. `CONTRIBUTING.md` has the details.
- The code is GPL-3.0-or-later (2026-10-07: chosen over Apache-2.0 so that a product built on the tool stays open; loosening later costs nothing while the copyright is in one hand, tightening later cannot recall released copies). The eBPF programs carry GPL-2.0-or-later for the kernel's sake. Datasets a run produces are not derivatives and carry their own licence per release.
- Documentation and commit bodies in plain prose. Engineer-facing docs describe the workflow in section 3, not the internals.
- When this file is wrong, fix it in the same commit. This file says how things are; `CHANGELOG.md` says what changed and why, in the same commit. A decision in section 4 still takes a dated note in place.

First tasks for M1. Two preliminaries, then three phases. Phases A and B run on the Linux boot. Phase C needs the Windows boot, and it is the only part of M1 that does: under libvirt the DC, the Windows workstation, `agent_windows` and Sysmon attribution all run in guests on the Linux host. When a task says switch, work stops on a named branch, which is then pulled on the other boot.

Before phase A, both done (2026-09-21):
1. ~~Add `windows-latest` to the CI test matrix.~~ A `test-windows` job runs the suite on Windows.
2. ~~Settle the three open questions that block a run, then checks 9 and 10.~~ Action parameters, `Host.backend` and the typed `Topology` are in the IR (section 7); the address plan is a function of the IR; checks 9, 10 and 16 exist.

Phase A, the Linux path. Exit: one Linux workstation, one web server, one attacker; labelled pcaps plus Zeek and Suricata logs from one command.
3. ~~An `InfraBackend` descriptor, and the Docker backend for the Linux daemon.~~ Done (2026-10-02): descriptors, run manifests, the Docker backend, `tiergen infra up` and `down`; `examples/linux_slice` comes up on its two segments with the planned addresses and goes down without a trace, and `examples/two_teams`' Linux half routes between its team LANs through `core_router`. `build` writes every instance's projected program. Default hosts ran a pinned Alpine that idled until task 5's image replaced it; `image_base` in `impl.toml` is still unused, since one base serves every Linux implementation so far.
4. ~~Runtimes for `httpx`, `nginx` and `nmap`, in the packages that already hold their manifests.~~ Done (2026-10-02), with unit tests; the conformance tests of 6.1 need capture and move to task 6.
5. ~~`agent_linux`: the projected program, the behaviour loop over the IR's process, a cgroup per invocation, the invocation log.~~ Done (2026-10-02). The cgroup per invocation needs a private cgroup namespace and `SYS_ADMIN` to remount the cgroup filesystem; the agent falls back to the process id and says so. The Docker backend grants it, builds the agent's image from the workspace and mounts the run directory (section 10); `examples/linux_slice` browses and scans, with every invocation on record, which the integration test holds against the daemon.
5b. ~~Agent hosts under the daemon's user-namespace remap, no `SYS_ADMIN`.~~ Done (2026-10-05): decision 4.19; the developer daemon and the CI runners carry the setting.
6. ~~`capture`: dumpcap on the data-plane bridge, pcapng, per-host clock offsets.~~ Done (2026-10-06): `tiergen capture start` and `stop`, one dumpcap per capture point over its bridges, tags inserted for tagged points by the tool's own pcapng code, offloads quiesced through the backend after measuring which ones matter, offsets recorded; `linux_slice`'s capture holds the browsing and the SYN scan in wire-sized frames.
7. ~~`attrib/linux_ebpf`: eBPF on `tcp_connect`, `inet_csk_accept`, UDP send and receive, and `cgroup_skb` for raw sockets; the join to `AttributionRecord`s.~~ Done (2026-10-07) with libbpf and CO-RE rather than bcc, through the daemon (section 10); `linux_slice`'s browsing and SYN scan are attributed to their invocations' cgroups by the kernel.
8. Zeek, then Suricata, offline over the pcaps, each with its ingest adapter into `ConnEvent` and `AppEvent`. The capability schemas are defined between the two, so they are not Zeek-shaped by accident. This is also where the `ConnEvent.state` vocabulary is confirmed or changed.
9. `scheduler`, `tiergen build`, `tiergen run`, `tiergen assemble`: per-sensor labels, `flagged.jsonl`, `manifest.json`.

Phase B, Windows guests under libvirt, still on the Linux boot. Exit: the mixed slice, which is M1's exit criterion.
10. The libvirt backend; a Windows Server 2022 DC template and a Windows workstation template.
11. `agent_windows` with a job object per invocation; `attrib/windows_etw` from Sysmon event 3; the w32time clock check.
12. Runtimes for `smbclient_win` and `samba`. The `hq_lan` slice: DC VM, Windows workstation VM, Linux server, attacker.

Phase C, Windows containers. **Switch to the Windows boot here.**
13. The Docker backend for the Windows daemon, Hyper-V isolation, as a binding option for the workstation. Verify that both daemons run concurrently (section 12). It comes after the exit criterion, so it never blocks the milestone.
