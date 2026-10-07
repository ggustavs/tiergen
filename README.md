# tiergen

Labelled network intrusion detection datasets for one specific network: yours. A scenario
describes the network's hosts, what they do and how they are wired; `tiergen` checks it,
brings it up on real hosts running real tools, captures the traffic at the points a sensor
would see it, and records which invocation caused each connection at the kernel, so every
label is confirmed by attribution rather than inferred from an address and a time window.
The dataset is meant to be read by the same sensor, at the same version, that the network
runs. Fitting a scenario from the network's own sensor logs, predicting what the sensor will
see before anything runs, and scoring the result against the real logs are the parts still
to come.

The design, its decisions and their reasons live in
[`nids-gen-dsl-design.md`](nids-gen-dsl-design.md); its first lines say what is implemented
today, and [`CHANGELOG.md`](CHANGELOG.md) says what changed and why. This file is the short
way in.

## What works today

A three-host Linux scenario (`examples/linux_slice`) goes from a Python file to a run
directory holding pcaps, invocation records and attribution events, on a Linux host with
Docker:

```
uv sync
uv run tiergen check examples/linux_slice/scenario.py
uv run tiergen build examples/linux_slice/scenario.py --out run1
uv run tiergen infra up run1       # the hosts, each running its agent on its program
uv run tiergen attrib start run1   # the eBPF collector on the hosts' cgroups
uv run tiergen capture start run1  # dumpcap at the scenario's capture points
sleep 60
uv run tiergen capture stop run1
uv run tiergen attrib stop run1
uv run tiergen sensors run run1  # zeek and suricata over the capture, pinned images
uv run tiergen infra down run1
```

Afterwards `run1/` holds `capture/lan-span.pcapng`, `out/<instance>/invocations.jsonl` per
host (what each invocation meant to do, keyed by its cgroup), `attrib/events.jsonl` (what the
kernel saw, keyed the same way) and `sensors/<name>/<point>/events.jsonl` (what each sensor
saw, keyed by its own connection ids). Matching the three into per-sensor labels is the next
task.

Requirements for the run: a Linux host, Docker with its user-namespace remap on, `setfacl`,
and dumpcap with the capability to capture. [`CONTRIBUTING.md`](CONTRIBUTING.md) has the two
lines that switch the daemon over and what the switch does. Checking and building a scenario
needs none of that and runs anywhere Python 3.12 does.

## Where things are

- `core/` the intermediate representation, the builders a scenario is written with, the
  address and route plans and the projected program each host runs.
- `protocols/` the signatures: what a primitive is, independent of the tool that runs it.
- `check/` the sixteen static checks a scenario passes before anything is built.
- `impls/` one package per tool, discovered by entry points: httpx, nginx and nmap run today.
- `backends/` infrastructure (Docker), attribution (eBPF on Linux) and sensors (Zeek, Suricata).
- `runtime/` the Linux agent and capture.
- `cli/` the `tiergen` command.
- `examples/` five scenarios, described in [`examples/README.md`](examples/README.md).

Section 6 of the design document has the full layout and the data flow between these.

## Working on it

[`CONTRIBUTING.md`](CONTRIBUTING.md): setup, the checks to run before pushing, the commit
and branch conventions and how pull requests land. Read the design document first; section
18 lists the agreements the code follows.

## Licence

GPL-3.0-or-later, see [`LICENSE`](LICENSE). The eBPF programs are GPL-2.0-or-later, which
is what the kernel requires to load them. A dataset a run produces is not a derivative of the
tool; each release names its own licence, CC BY 4.0 unless there is a reason otherwise.
