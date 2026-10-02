from dataclasses import replace

from hypothesis import given, settings
from hypothesis import strategies as st

from tiergen.core import ir
from tiergen.core.addressing import hostname, mac_address, plan_addresses
from tiergen.core.codec import from_json, to_json
from tiergen.core.dsl import binding, group, host, kind, scenario, segment, topology
from tiergen.core.routing import Route, RoutePlan, forwarders, plan_routes, reachable

Core = segment("core", "10.0.0.0/24")
Eng = segment("eng", "10.1.0.0/24")
Far = segment("far", "10.2.0.0/24")
Mgmt = segment("mgmt", "10.9.0.0/24", "management")
Ws = kind("ws", platforms=["linux"])
Dc = kind("dc", platforms=["linux"])
Rt = kind("rt", platforms=["linux"], forwards=True)


def _scenario(*groups: object, bindings: dict[object, object] | None = None) -> ir.Scenario:
    return scenario(
        "r",
        groups=groups,  # pyright: ignore[reportArgumentType]
        bindings=bindings or {},  # pyright: ignore[reportArgumentType]
        topology=topology([Core, Eng, Far, Mgmt]),
        egress="none",
        start="2026-10-05T08:00:00+02:00",
        duration_s=1,
        capture_points=[],
        sensors=[],
        seed=0,
    )


TWO_HOPS = _scenario(
    group("corp", instances={Dc: 1, Rt: 1}, attachments={Dc: [Core], Rt: [Core, Eng]}),
    group("eng", instances={Ws: 2, Rt: 1}, attachments={Ws: [Eng], Rt: [Eng, Far]}, parent="corp"),
    group("far", instances={Ws: 1}, attachments={Ws: [Far]}, parent="corp"),
)


def _plans(s: ir.Scenario) -> tuple[RoutePlan, list[str]]:
    assert isinstance(s.topology, ir.Topology)
    plan, problems = plan_addresses(s, s.topology)
    assert problems == []
    routes, route_problems = plan_routes(s, s.topology, plan)
    return routes, [p.message for p in route_problems]


def test_routes_follow_forwarders_hop_by_hop() -> None:
    routes, problems = _plans(TWO_HOPS)
    assert problems == []
    assert routes.forwarders == ("corp/rt[0]", "corp/eng/rt[0]")
    # Kinds are ordered by first mention, so routers come before workstations in each group:
    # corp/rt is 10.0.0.3 on core and 10.1.0.2 on eng; corp/eng/rt is 10.1.0.3 on eng and
    # 10.2.0.2 on far.
    assert routes.routes["corp/dc[0]"] == (
        Route("eng", "10.1.0.0/24", "10.0.0.3", "core"),
        Route("far", "10.2.0.0/24", "10.0.0.3", "core"),
    )
    assert routes.routes["corp/eng/ws[0]"] == (
        Route("core", "10.0.0.0/24", "10.1.0.2", "eng"),
        Route("far", "10.2.0.0/24", "10.1.0.3", "eng"),
    )
    assert routes.routes["corp/rt[0]"] == (Route("far", "10.2.0.0/24", "10.1.0.3", "eng"),)
    assert routes.routes["corp/far/ws[0]"] == (
        Route("core", "10.0.0.0/24", "10.2.0.2", "far"),
        Route("eng", "10.1.0.0/24", "10.2.0.2", "far"),
    )


def test_reachable_is_shared_segment_or_route() -> None:
    assert isinstance(TWO_HOPS.topology, ir.Topology)
    plan, _ = plan_addresses(TWO_HOPS, TWO_HOPS.topology)
    routes, _ = plan_routes(TWO_HOPS, TWO_HOPS.topology, plan)
    data = {"core", "eng", "far"}
    assert reachable(plan, routes, "corp/eng/ws[0]", "corp/eng/ws[1]", data)  # on-link
    assert reachable(plan, routes, "corp/far/ws[0]", "corp/dc[0]", data)  # two hops
    island = _scenario(
        group("a", instances={Ws: 1}, attachments={Ws: [Core]}),
        group("b", instances={Ws: 1}, attachments={Ws: [Eng]}),
    )
    assert isinstance(island.topology, ir.Topology)
    plan2, _ = plan_addresses(island, island.topology)
    routes2, _ = plan_routes(island, island.topology, plan2)
    assert routes2.routes == {"a/ws[0]": (), "b/ws[0]": ()}
    assert not reachable(plan2, routes2, "a/ws[0]", "b/ws[0]", data)
    assert reachable(plan2, routes2, "a/ws[0]", "a/ws[0]", data)


def test_two_equally_short_next_hops_are_a_problem_not_a_guess() -> None:
    s = _scenario(group("g", instances={Ws: 1, Rt: 2}, attachments={Ws: [Core], Rt: [Core, Eng]}))
    routes, problems = _plans(s)
    [problem] = problems
    assert "g/ws[0] has 2 equally short next hops to 'eng'" in problem
    assert routes.routes["g/ws[0]"] == ()
    # The forwarders themselves are on both segments and need no route.
    assert routes.routes["g/rt[0]"] == ()


def test_management_is_never_routed_and_a_forwarder_does_not_route_to_itself() -> None:
    routes, _ = _plans(TWO_HOPS)
    assert all(r.segment != "mgmt" for rs in routes.routes.values() for r in rs)
    assert all(r.via != "10.9.0.3" for rs in routes.routes.values() for r in rs)


def test_route_plan_is_data() -> None:
    routes, _ = _plans(TWO_HOPS)
    assert from_json(RoutePlan, to_json(routes)) == routes


def test_hostnames_and_macs_are_functions_of_the_ir() -> None:
    assert hostname("corp/eng/file_server[3]") == "corp-eng-file-server-3"
    mac = mac_address("3C:EC:EF", "corp/eng/ws[0]", "eng")
    assert mac.startswith("3c:ec:ef:")
    assert len(mac) == 17
    assert mac == mac_address("3C:EC:EF", "corp/eng/ws[0]", "eng")
    assert mac != mac_address("3C:EC:EF", "corp/eng/ws[0]", "core")
    s = _scenario(
        group("g", instances={Ws: 1, Dc: 1}, attachments={Ws: [Core], Dc: [Core]}),
        bindings={
            Ws: binding(host("linux", "container", backend="docker"), mac_oui="3c:ec:ef"),
            Dc: binding(host("linux", "container", backend="docker")),
        },
    )
    assert isinstance(s.topology, ir.Topology)
    plan, _ = plan_addresses(s, s.topology)
    assert plan.hostnames == {"g/ws[0]": "g-ws-0", "g/dc[0]": "g-dc-0"}
    assert set(plan.macs) == {"g/ws[0]"}
    assert set(plan.macs["g/ws[0]"]) == {"core", "mgmt"}


@st.composite
def graphs(draw: st.DrawFn) -> ir.Scenario:
    """Up to four data segments and three forwarders attached to random pairs of them, with a
    workstation on every segment."""
    n = draw(st.integers(1, 4))
    segs = [segment(f"s{i}", f"10.{i}.0.0/24") for i in range(n)]
    kinds = [kind(f"ws{i}", platforms=["linux"]) for i in range(n)]
    rts = [
        kind(f"rt{i}", platforms=["linux"], forwards=True) for i in range(draw(st.integers(0, 3)))
    ]
    attachments: dict[object, list[ir.Segment]] = {k: [segs[i]] for i, k in enumerate(kinds)}
    for r in rts:
        pair = draw(st.lists(st.integers(0, n - 1), min_size=1, max_size=2, unique=True))
        attachments[r] = [segs[i] for i in pair]
    instances = dict.fromkeys([*kinds, *rts], 1)
    g = group("g", instances=instances, attachments=attachments)  # pyright: ignore[reportArgumentType]
    return scenario(
        "p",
        groups=[g],
        bindings={},
        topology=topology([*segs, Mgmt]),
        egress="none",
        start="2026-10-05T08:00:00+02:00",
        duration_s=1,
        capture_points=[],
        sensors=[],
        seed=0,
    )


@given(graphs())
@settings(max_examples=100, deadline=None)
def test_route_properties(s: ir.Scenario) -> None:
    assert isinstance(s.topology, ir.Topology)
    plan, problems = plan_addresses(s, s.topology)
    assert problems == []
    routes, route_problems = plan_routes(s, s.topology, plan)
    data = {x.name for x in s.topology.segments if x.plane == "data"}
    for instance, rs in routes.routes.items():
        mine = {x for x in plan.addresses[instance] if x in data}
        for r in rs:
            assert r.segment not in mine  # never a route to an on-link segment
            assert r.out in mine  # the next hop is on one of my own segments
            assert any(plan.addresses[f].get(r.out) == r.via for f in routes.forwarders)
        assert len({r.segment for r in rs}) == len(rs)  # one route per destination
    # A problem segment yields no routes through it; without problems, reachability is symmetric.
    if not route_problems:
        ids = list(routes.routes)
        for a in ids:
            for b in ids:
                assert reachable(plan, routes, a, b, data) == reachable(plan, routes, b, a, data)
    assert plan_routes(s, s.topology, plan) == (routes, route_problems)
    assert forwarders(replace(s, kinds=tuple(replace(k, forwards=False) for k in s.kinds))) == []
