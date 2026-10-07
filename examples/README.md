# Examples

Three versions of one small Active Directory LAN, a three-host Linux slice, and an
organisation of two teams, written with the builders in `tiergen.core.dsl`. Each directory holds a `scenario.py` and the `models/` it refers to.

| directory | what it shows | `tiergen check` |
|---|---|---|
| `hq_lan/` | a well-formed scenario | passes |
| `hq_lan_capgap/` | `fit` relied on a capability the label sensor lacks | passes with a check 14 warning |
| `linux_slice/` | a workstation, a web server and an attacker, all Linux containers; written inline, topology included | passes |
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
uv run tiergen infra up run1      # builds the agent image the first time, then three hosts
uv run tiergen attrib start run1  # the eBPF collector on the three containers' cgroups
uv run tiergen capture start run1 # dumpcap on the LAN's bridge, offloads off in the hosts
sleep 60
cat run1/out/lab-workstation-0/invocations.jsonl    # the workstation's http.get records
cat run1/out/lab-web_server-0/http.nginx/access.log # seen from the web server
cat run1/out/lab-attacker-0/invocations.jsonl       # the attacker's SYN scan, from 30 s in
uv run tiergen capture stop run1  # run1/capture/lan-span.pcapng, capture.json, offsets.json
uv run tiergen attrib stop run1   # run1/attrib/events.jsonl: who caused each connection
uv run tiergen sensors run run1   # zeek and suricata over the capture: run1/sensors/<name>/
uv run tiergen infra down run1
```

`capture` needs dumpcap on the host with the capabilities to capture (the `wireshark` group on
most distributions).

The daemon must run with its user-namespace remap on (`{"userns-remap": "default"}` in
`/etc/docker/daemon.json`, then restart it); `infra up` says so otherwise. The agents run as
the remapped root, so what they write under `run1/out/` belongs to that uid and is readable
through the ACL `up` sets. The collector runs as a privileged container on the host; the first
`attrib start` builds its image, which takes a few minutes, and the first `sensors run` pulls
the two sensor images. Nothing matches the sensors' events to the records yet; that is
`assemble`, the next task.

The other scenarios bind Windows VMs to libvirt, which has no runtime yet, so they build but
do not come up in full. `two_teams`' Linux half does, with its routes: `tiergen infra up`
brings up the file servers, the attacker and `core_router`, and a connection from one team's
file server to the other's crosses the router.
