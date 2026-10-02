from dataclasses import replace

from support import good, only, run, with_group

from tiergen.core import ir

LAN = ir.Segment("lan", "10.0.0.0/24", "data")
MGMT = ir.Segment("mgmt", "10.9.0.0/24", "management")
SPAN = ir.CapturePoint("span0", ("lan",))


def _with(topology: ir.Topology, **changes: object) -> ir.Scenario:
    return replace(good(), topology=topology, **changes)  # pyright: ignore[reportArgumentType]


def test_planner_problems_become_errors_under_the_topology() -> None:
    topology = ir.Topology(
        (ir.Segment("lan", "10.0.0.0/30", "data"), MGMT), (SPAN,), {"lan/cli[9]": "10.0.0.2"}
    )
    found = {d.path: d.message for d in only("C10", _with(topology))}
    assert "not an instance" in found["topology.addresses['lan/cli[9]']"]
    assert "room for 1 hosts; 4 are attached" in found["topology.segments"]


def test_a_malformed_cidr() -> None:
    found = only(
        "C10", _with(ir.Topology((ir.Segment("lan", "10.0.0.300/24", "data"), MGMT), (SPAN,)))
    )
    assert [d.path for d in found] == ["topology.segments[0].cidr", "groups[0].wiring['cli.web']"]
    # With no usable segment nothing is reachable either, which is the second line.


def test_overlapping_data_plane_networks() -> None:
    dmz = ir.Segment("dmz", "10.0.0.128/25", "data")
    [d] = only("C10", _with(ir.Topology((LAN, dmz, MGMT), (SPAN,))))
    assert "'lan' (10.0.0.0/24) and 'dmz' (10.0.0.128/25) overlap" in d.message


def test_attachments_name_real_kinds_and_data_plane_networks() -> None:
    attachments = {"cli": ("lan", "wan"), "srv": ("lan", "mgmt"), "ghost": ("lan",)}
    found = {
        (d.path, d.message.split(";")[0])
        for d in only("C10", with_group(good(), 0, attachments=attachments))
    }
    assert found == {
        ("groups[0].attachments['cli']", "'wan' is not a segment of this topology"),
        ("groups[0].attachments['srv']", "'mgmt' is the management segment"),
        ("groups[0].attachments['ghost']", "'ghost' is not a kind of this scenario"),
    }


def test_a_kind_a_group_holds_joins_the_data_plane_there() -> None:
    found = only("C10", with_group(good(), 0, attachments={"cli": ("lan",)}))
    assert [d.path for d in found] == ["groups[0].instances['srv']", "groups[0].wiring['cli.web']"]
    assert "'lan' holds 'srv' but attaches it to no data-plane network" in found[0].message
    # With no instances there is nobody to attach. Check 1 objects to the client's single tie.
    quiet = with_group(good(), 0, attachments={"cli": ("lan",)}, instances={"cli": 3, "srv": 0})
    assert [d for d in run(quiet) if d.check == "C10"] == []


def test_egress_clauses_wait_for_fitted_destinations() -> None:
    [d] = only("C10", replace(good(), egress="stub"))
    assert (d.severity, d.path) == ("not_computed", "egress")
    assert only("C10", good()) == []


def test_a_wired_tie_across_segments_needs_a_forwarder() -> None:
    dmz = ir.Segment("dmz", "10.0.1.0/24", "data")
    s = _with(ir.Topology((LAN, dmz, MGMT), (SPAN,)))
    s = with_group(s, 0, attachments={"cli": ("lan",), "srv": ("dmz",)})
    [d] = only("C10", s)
    assert d.path == "groups[0].wiring['cli.web']"
    assert "lan/cli[0] cannot reach lan/srv[0]" in d.message
    assert "3 such pair(s)" in d.message


def test_a_forwarder_makes_the_tie_reachable_and_two_make_it_ambiguous() -> None:
    dmz = ir.Segment("dmz", "10.0.1.0/24", "data")
    rt = ir.ActorKind("rt", (), (), (), ("linux",), forwards=True)
    s = _with(ir.Topology((LAN, dmz, MGMT), (SPAN,)))
    s = replace(s, kinds=(*s.kinds, rt))
    s = with_group(
        s,
        0,
        instances={"cli": 3, "srv": 1, "rt": 1},
        attachments={"cli": ("lan",), "srv": ("dmz",), "rt": ("lan", "dmz")},
    )
    binding = ir.Binding(
        "rt", ir.Host("linux", "container", "docker", "default", None), (), "3c:ec:ef"
    )
    s = replace(s, bindings=(*s.bindings, binding))
    assert only("C10", s) == []
    found = only("C10", with_group(s, 0, instances={"cli": 3, "srv": 1, "rt": 2}))
    assert all("equally short next hops" in d.message for d in found[:-1])
    assert "cannot reach" in found[-1].message  # and so the tie has no route
