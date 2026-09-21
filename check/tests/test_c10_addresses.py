from dataclasses import replace

from support import good, only, run

from tiergen.core import ir

LAN = ir.Network("lan", "10.0.0.0/24", "data")
MGMT = ir.Network("mgmt", "10.9.0.0/24", "management")
SPAN = ir.CapturePoint("span0", "lan")
ATTACHED = {"cli": ("lan",), "srv": ("lan",)}


def _with(topology: ir.Topology, **changes: object) -> ir.Scenario:
    return replace(good(), topology=topology, **changes)  # pyright: ignore[reportArgumentType]


def test_planner_problems_become_errors_under_the_topology() -> None:
    topology = ir.Topology(
        (ir.Network("lan", "10.0.0.0/30", "data"), MGMT), ATTACHED, (SPAN,), {"cli[9]": "10.0.0.2"}
    )
    found = {d.path: d.message for d in only("C10", _with(topology))}
    assert "not an instance" in found["topology.addresses['cli[9]']"]
    assert "room for 1 hosts; 4 are attached" in found["topology.networks"]


def test_a_malformed_cidr() -> None:
    [d] = only(
        "C10",
        _with(ir.Topology((ir.Network("lan", "10.0.0.300/24", "data"), MGMT), ATTACHED, (SPAN,))),
    )
    assert d.path == "topology.networks[0].cidr"


def test_overlapping_data_plane_networks() -> None:
    dmz = ir.Network("dmz", "10.0.0.128/25", "data")
    [d] = only("C10", _with(ir.Topology((LAN, dmz, MGMT), ATTACHED, (SPAN,))))
    assert "'lan' (10.0.0.0/24) and 'dmz' (10.0.0.128/25) overlap" in d.message


def test_attachments_name_real_kinds_and_data_plane_networks() -> None:
    attachments = {"cli": ("lan", "wan"), "srv": ("lan", "mgmt"), "ghost": ("lan",)}
    found = {
        (d.path, d.message.split(";")[0])
        for d in only("C10", _with(ir.Topology((LAN, MGMT), attachments, (SPAN,))))
    }
    assert found == {
        ("topology.attachments['cli']", "'wan' is not a network of this topology"),
        ("topology.attachments['srv']", "'mgmt' is the management network"),
        ("topology.attachments['ghost']", "'ghost' is not a kind of this scenario"),
    }


def test_a_kind_with_instances_joins_the_data_plane() -> None:
    [d] = only("C10", _with(ir.Topology((LAN, MGMT), {"cli": ("lan",)}, (SPAN,))))
    assert d.path == "kinds[1]"
    # With no instances there is nobody to attach. Check 1 objects to the client's single tie.
    quiet = _with(
        ir.Topology((LAN, MGMT), {"cli": ("lan",)}, (SPAN,)), instances={"cli": 3, "srv": 0}
    )
    assert [d for d in run(quiet) if d.check == "C10"] == []


def test_egress_clauses_wait_for_fitted_destinations() -> None:
    [d] = only("C10", replace(good(), egress="stub"))
    assert (d.severity, d.path) == ("not_computed", "egress")
    assert only("C10", good()) == []
