# Examples

Three versions of one small Active Directory LAN, written with the builders in
`tiergen.core.dsl`. Each directory holds a `scenario.py` and the `models/` it refers to.

| directory | what it shows | `tiergen check` |
|---|---|---|
| `hq_lan/` | a well-formed scenario | passes, with one `not computed` line (see below) |
| `hq_lan_capgap/` | `fit` relied on a capability the label sensor lacks | passes with a check 14 warning |
| `hq_lan_broken/` | four deliberate mistakes, listed at the top of its `scenario.py` | fails checks 1, 4, 5 and 12 |

```
uv run tiergen check examples/hq_lan/scenario.py
```

Every example reports one check 7 line as `not computed`: nmap needs the `net_raw` host
capability, and whether a host can be granted it is a question for an infrastructure
backend, which arrives in M1. `not computed` is not a failure and not a pass.

The numbers under `models/` are placeholders chosen to exercise the checker: a four-state
workstation process, a two-state attacker, made-up coverage values. They are not fitted
from any network and say nothing about real traffic. In normal use `tiergen fit` writes
`models/` from the target network's sensor logs, and the sensor configuration files are the
network's own. The scenarios run nothing in M0; they exist to be checked.
