# Examples

Three versions of one small Active Directory LAN, a three-host Linux slice, and an
organisation of two teams, written with the builders in `tiergen.core.dsl`. Each directory holds a `scenario.py` and the `models/` it refers to.

| directory | what it shows | `tiergen check` |
|---|---|---|
| `hq_lan/` | a well-formed scenario | passes |
| `hq_lan_capgap/` | `fit` relied on a capability the label sensor lacks | passes with a check 14 warning |
| `linux_slice/` | a workstation, a web server and an attacker, all Linux containers; written inline, topology included | passes |
| `two_teams/` | one organisation, two teams built by a function; each team's workstations wired to their own file server | passes |
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
uv run tiergen infra up run1      # three idle containers on their planned addresses
uv run tiergen infra down run1
```

The other scenarios bind Windows VMs to libvirt, which has no runtime yet, so they build but
do not come up.
