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
    [d] = only(
        "C10",
        _with(ir.Topology((ir.Segment("lan", "10.0.0.300/24", "data"), MGMT), (SPAN,))),
    )
    assert d.path == "topology.segments[0].cidr"


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
    [d] = only("C10", with_group(good(), 0, attachments={"cli": ("lan",)}))
    assert d.path == "groups[0].instances['srv']"
    assert "'lan' holds 'srv' but attaches it to no data-plane network" in d.message
    # With no instances there is nobody to attach. Check 1 objects to the client's single tie.
    quiet = with_group(good(), 0, attachments={"cli": ("lan",)}, instances={"cli": 3, "srv": 0})
    assert [d for d in run(quiet) if d.check == "C10"] == []


def test_egress_clauses_wait_for_fitted_destinations() -> None:
    [d] = only("C10", replace(good(), egress="stub"))
    assert (d.severity, d.path) == ("not_computed", "egress")
    assert only("C10", good()) == []
