from dataclasses import replace

import pytest
from support import RESOURCES, good, only

from tiergen.core import ir

LAN = ir.Segment("lan", "10.0.0.0/24", "data")
MGMT = ir.Segment("mgmt", "10.9.0.0/24", "management")
SPAN = ir.CapturePoint("span0", ("lan",))


def _with(topology: ir.Topology, **changes: object) -> ir.Scenario:
    return replace(good(), topology=topology, **changes)  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize(
    ("networks", "fragment"),
    [
        ((LAN,), "there are 0"),
        ((LAN, MGMT, ir.Segment("mgmt2", "10.8.0.0/24", "management")), "there are 2"),
        (
            (LAN, ir.Segment("mgmt", "10.0.0.128/25", "management")),
            "overlaps data-plane network 'lan'",
        ),
    ],
)
def test_management_plane(networks: tuple[ir.Segment, ...], fragment: str) -> None:
    found = only("C09", _with(ir.Topology(networks, (SPAN,))))
    assert any(fragment in d.message and d.path == "topology.segments" for d in found)


def test_a_capture_point_on_the_management_network_records_the_tool() -> None:
    topology = ir.Topology((LAN, MGMT), (SPAN, ir.CapturePoint("tap", ("mgmt",))))
    [d] = only("C09", _with(topology))
    assert d.path == "topology.capture_points[1].segments[0]"
    assert "records the tool" in d.message


def test_capture_points_are_defined_once_on_a_real_network_and_active_ones_exist() -> None:
    topology = ir.Topology((LAN, MGMT), (SPAN, SPAN, ir.CapturePoint("far", ("wan",))))
    found = {d.path for d in only("C09", _with(topology, capture_points=("span0", "ghost")))}
    assert found == {
        "topology.capture_points[1]",
        "topology.capture_points[2].segments[0]",
        "capture_points[1]",
    }


def test_a_run_needs_an_active_capture_point() -> None:
    [d] = only("C09", replace(good(), capture_points=()))
    assert d.path == "capture_points"


def test_a_live_sensors_interface_cannot_be_checked_yet() -> None:
    s = good()
    [d] = only("C09", replace(s, sensors=(replace(s.sensors[0], mode="live"), s.sensors[1])))
    assert (d.severity, d.path) == ("not_computed", "sensors[0].mode")


def test_an_unresolved_topology_is_left_to_check_5() -> None:
    assert only("C05", good(), {k: v for k, v in RESOURCES.items() if k != "lan.topology"})
