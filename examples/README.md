# Examples

Three versions of one small Active Directory LAN, a three-host Linux slice, an office of
five workstations, and an organisation of two teams, written with the builders in `tiergen.core.dsl`. Each directory holds a `scenario.py` and the `models/` it refers to.

| directory | what it shows | `tiergen check` |
|---|---|---|
| `hq_lan/` | a well-formed scenario | passes |
| `hq_lan_capgap/` | `fit` relied on a capability the label sensor lacks | passes with a check 14 warning |
| `linux_slice/` | a workstation, a web server and an attacker, all Linux containers; written inline, topology included | passes |
| `office_slice/` | five workstations over three request paths with a daily rate curve, two web servers and an attacker, all Linux containers: the fit's round trip on a real run | passes |
| `two_teams/` | one organisation, two teams built by a function on three VLANs behind one forwarding host, captured at a tagged trunk SPAN; each team's workstations wired to their own file server | passes |
| `hq_lan_broken/` | six deliberate mistakes, listed at the top of its `scenario.py` | fails checks 1, 4, 5, 9, 10 and 12 |

```
uv run tiergen check examples/hq_lan/scenario.py
```

The numbers under `models/` are placeholders chosen to exercise the checker: a four-state
workstation process, a two-state attacker, made-up paths, shares and coverage values. They are not fitted
from any network and say nothing about real traffic. In normal use `tiergen fit` writes
`models/` from the target network's sensor logs, and the sensor configuration files are the
network's own.

`linux_slice` is the one that runs so far. With a Docker daemon reachable:

```
uv run tiergen build examples/linux_slice/scenario.py --out run1
uv run tiergen run run1 --for 60  # the images the first time; then three hosts, the eBPF
                                  # collector on their cgroups, dumpcap on the LAN's bridge,
                                  # the agents for a minute (the scan from 30 s in), down
cat run1/out/lab-workstation-0/invocations.jsonl    # the workstation's http.get records
cat run1/out/lab-web_server-0/http.nginx/access.log # seen from the web server
cat run1/attrib/events.jsonl                        # who caused each connection
uv run tiergen assemble run1      # zeek and suricata over run1/capture/lan-span.pcapng,
                                  # then run1/labels.zeek.jsonl, labels.suricata.jsonl,
                                  # flagged.jsonl and manifest.json
```

The pieces are commands of their own, in the order `run` uses them: `infra up`, `attrib
start`, `capture start`, then `capture stop`, `attrib stop`, `sensors run`, `infra down`.

`capture` needs dumpcap on the host with the capabilities to capture (the `wireshark` group on
most distributions).

The daemon must run with its user-namespace remap on (`{"userns-remap": "default"}` in
`/etc/docker/daemon.json`, then restart it); `infra up` says so otherwise. The agents run as
the remapped root, so what they write under `run1/out/` belongs to that uid and is readable
through the ACL `up` sets. The collector runs as a privileged container on the host; the first
`run` builds its image and the agent's, which takes a few minutes, and the first `assemble`
pulls the two sensor images.

The other scenarios bind Windows VMs to libvirt, which has no runtime yet, so they build but
do not come up in full. `two_teams`' Linux half does, with its routes: `tiergen infra up`
brings up the file servers, the attacker and `core_router`, and a connection from one team's
file server to the other's crosses the router.

## The round trip: `office_slice`

The fit is validated on the simulator (`fit/tests`), where the generating scenario is the
truth. `office_slice` is the same check on a real run: five workstations whose behaviour
has every dwell family once, three acting states told apart by request path, a silent
idle state, and a daily rate curve, against two web servers. Two hours is enough for the
chain and the dwells; the curve needs the hours the run covers.

```
uv run tiergen build examples/office_slice/scenario.py --out office
uv run tiergen run office --for 7200          # two hours; overnight, it needs nothing from you
uv run tiergen assemble office                # labels, flagged.jsonl, conformance.md, manifest.json
uv run tiergen fit office --sensor zeek --out office/fit
```

Then compare `office/fit/workstation.office.transitions.json` with the scenario's matrix
projected onto the acting states (`tiergen.fit.compare.projection` does it, with the
dwell means), the fitted dwell families and means with the scenario's plus the expected
idle time, and the fitted curve's covered hours with `models/office.rate_day.json`. The
difference between this and the same fit on a simulated run of the scenario
(`tiergen.sim.write`, then `tiergen fit` with `--sensor sim`) is what the runtime, the
tools and the sensor add; `fit-report.md` lists what the sensor could not place.
`conformance.md` reads the run against its own model with five hosts a side, enough
relabellings for its verdicts to mean something.
