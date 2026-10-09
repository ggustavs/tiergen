"""Which connection is which action, from the scenario's own programs.

Every acting state of every behaviour of an instance is a candidate: its action reaches
the peers of a tie on the ports the signature's protocol is served on. A connection from
the instance to such a peer and port is that action, unless two actions agree on tie and
signature; then the request's path (an HTTP ``AppEvent``) decides, matching a literal
parameter or one of a choice's options. What matches nothing or several things is
unmapped, with the reason.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from tiergen.core.codec import JsonValue
from tiergen.core.events import AppEvent, ConnEvent
from tiergen.core.ir import Choice, ParamScalar
from tiergen.core.program import Program
from tiergen.protocols import SIGNATURES


@dataclass(frozen=True, slots=True)
class Candidate:
    """One acting state as the wire would show it."""

    instance: str
    kind: str
    behaviour: str
    state: str
    signature: str
    tie: str
    endpoints: frozenset[tuple[str, int | None, str]]
    """(address, port, transport) of every peer and port the action may reach; a port of
    None is a scan, which reaches any port of the peer."""
    paths: frozenset[str] | None
    """The request paths the action's parameters allow; None when it fixes none."""
    many: bool
    """Whether one invocation opens many connections (a scan), which the labelling folds
    into one action when they come within a second of each other."""


@dataclass(frozen=True, slots=True)
class Vocabulary:
    """Candidates by originating address, and the address of each instance."""

    by_address: dict[str, tuple[Candidate, ...]]
    instance_of: dict[str, str]

    def match(self, conn: ConnEvent, apps: Iterable[AppEvent]) -> Candidate | str:
        """The candidate the connection is, or the reason it is none: ``unknown originator``,
        ``no action``, ``ambiguous``."""
        found = self.by_address.get(conn.five_tuple.orig_addr)
        if found is None:
            return "unknown originator"
        key = (conn.five_tuple.resp_addr, conn.five_tuple.resp_port, conn.five_tuple.proto)
        hits = [c for c in found if key in c.endpoints]
        if not hits:  # a scan reaches any port of its peers; a named port wins over it
            wildcard = (conn.five_tuple.resp_addr, None, conn.five_tuple.proto)
            hits = [c for c in found if wildcard in c.endpoints]
        if len(hits) > 1:
            paths = {str(a.fields["uri"]) for a in apps if "uri" in a.fields}
            narrowed = [c for c in hits if c.paths is None or paths & c.paths]
            if paths and len(narrowed) == 1:
                return narrowed[0]
            hits = narrowed if narrowed else hits
        if not hits:
            return "no action"
        if len(hits) > 1:
            return "ambiguous"
        return hits[0]


def _paths(params: Mapping[str, ParamScalar | Choice]) -> frozenset[str] | None:
    value = params.get("path", params.get("start_path"))
    if value is None:
        return None
    if isinstance(value, Choice):
        return frozenset(str(o) for o in value.options)
    return frozenset({str(value)})


def vocabulary(
    programs: Iterable[Program], addresses: Mapping[str, Mapping[str, str]]
) -> Vocabulary:
    """``addresses`` is the plan's: instance to segment to address."""
    by_address: dict[str, list[Candidate]] = {}
    instance_of: dict[str, str] = {}
    for program in programs:
        mine = list(addresses.get(program.instance, {}).values())
        for address in mine:
            instance_of[address] = program.instance
        candidates: list[Candidate] = []
        for behaviour in program.behaviours:
            for state, action in behaviour.action_map.items():
                if action is None:
                    continue
                signature = SIGNATURES[action.signature]
                endpoints: set[tuple[str, int | None, str]] = set()
                for peer in program.peers.get(action.tie, ()):
                    for endpoint in peer.served:
                        if endpoint.protocol in signature.endpoints:
                            endpoints.add((peer.address, endpoint.port, endpoint.transport))
                    if signature.shape.port is not None:
                        endpoints.add(
                            (peer.address, signature.shape.port, signature.shape.transport)
                        )
                    if not signature.endpoints and signature.shape.port is None:
                        endpoints.add((peer.address, None, signature.shape.transport))
                candidates.append(
                    Candidate(
                        program.instance,
                        program.kind,
                        behaviour.name,
                        state,
                        action.signature,
                        action.tie,
                        frozenset(endpoints),
                        _paths(action.params),
                        signature.shape.connections == "many",
                    )
                )
        for address in mine:
            by_address.setdefault(address, []).extend(candidates)
    return Vocabulary({a: tuple(c) for a, c in by_address.items()}, instance_of)


def as_json(v: Vocabulary) -> JsonValue:
    return {
        address: [f"{c.instance}:{c.behaviour}:{c.state}" for c in candidates]
        for address, candidates in sorted(v.by_address.items())
    }
