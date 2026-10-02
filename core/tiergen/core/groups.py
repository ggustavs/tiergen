"""Reading a scenario's groups: paths, instance ids, tie targets, schedule targets.

Everything here is a pure function of the IR, shared by the checker, the address planner
and the backends, so they all agree on what an instance is called and whom a tie reaches.
"""

import re
from dataclasses import dataclass

from tiergen.core.ir import Scenario


def paths(scenario: Scenario) -> list[str]:
    """Every group's path, in scenario order."""
    return [g.path for g in scenario.groups]


def instance_id(group_path: str, kind: str, index: int) -> str:
    return f"{group_path}/{kind}[{index}]"


def instance_ids(scenario: Scenario) -> list[tuple[str, str, str]]:
    """Every ``(group path, kind, instance id)``: groups in order, then the scenario's kind
    order, then index. A kind a group counts but the scenario does not define is skipped."""
    kinds = [k.name for k in scenario.kinds]
    return [
        (g.path, kind, instance_id(g.path, kind, i))
        for g in scenario.groups
        for kind in kinds
        for i in range(max(g.instances.get(kind, 0), 0))
    ]


def descendants(scenario: Scenario, group_path: str) -> list[str]:
    """``group_path`` and every group path under it, in scenario order."""
    return [p for p in paths(scenario) if p == group_path or p.startswith(group_path + "/")]


def targets(scenario: Scenario, group_path: str, kind: str, tie: str) -> list[str] | None:
    """The instance ids a tie reaches from instances of ``kind`` in the group at
    ``group_path``, or None if the tie is not wired there. A wired group that holds no
    instance of the target kind contributes nothing."""
    group = next((g for g in scenario.groups if g.path == group_path), None)
    actor = next((k for k in scenario.kinds if k.name == kind), None)
    if group is None or actor is None:
        return None
    relation = next((t for t in actor.ties if t.name == tie), None)
    wired = group.wiring.get(f"{kind}.{tie}")
    if relation is None or wired is None:
        return None
    found: list[str] = []
    for path, target_kind, instance in instance_ids(scenario):
        if target_kind == relation.target_kind and path in wired:
            found.append(instance)
    return found


@dataclass(frozen=True, slots=True)
class Target:
    """A parsed schedule target: a head of one or more ``/`` segments, optionally an index."""

    head: str
    index: int | None


def parse_target(text: str) -> Target | None:
    """``path``, ``path/kind`` or ``path/kind[i]`` by shape alone; None if the text is none
    of these. Which segments are the group and which the kind is decided against the
    scenario by ``select``."""
    match = re.fullmatch(r"(?P<head>[^\[\]/][^\[\]]*?)(?:\[(?P<index>\d+)\])?", text)
    if match is None or "//" in match["head"] or match["head"].endswith("/"):
        return None
    index = None if match["index"] is None else int(match["index"])
    if index is not None and "/" not in match["head"]:
        return None  # an index needs a kind, and a kind needs a group before it
    return Target(match["head"], index)


def select(scenario: Scenario, text: str) -> list[str] | None:
    """The instance ids a schedule target names, or None if it names nothing that exists.

    If the whole head is a group path, every instance under that group. Otherwise the last
    segment is a kind and the rest a group path: every instance of that kind under the
    group, or the one at the index.
    """
    parsed = parse_target(text)
    if parsed is None:
        return None
    known = set(paths(scenario))
    if parsed.index is None and parsed.head in known:
        under = set(descendants(scenario, parsed.head))
        return [i for p, _, i in instance_ids(scenario) if p in under]
    group_path, _, kind = parsed.head.rpartition("/")
    if group_path not in known or kind not in {k.name for k in scenario.kinds}:
        return None
    under = set(descendants(scenario, group_path))
    found = [i for p, k, i in instance_ids(scenario) if k == kind and p in under]
    if parsed.index is None:
        return found
    exact = instance_id(group_path, kind, parsed.index)
    return [exact] if exact in found else None
