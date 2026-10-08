from tiergen.core.codec import from_json, to_json
from tiergen.core.events import FiveTuple, SensorFlowId
from tiergen.core.labels import Flag, Label
from tiergen.core.records import AttributionKey, LabelKey

FLOW = SensorFlowId("zeek", "lan-span", "CHhAvVGS1DHFjwGM9")
FIVE = FiveTuple("10.20.0.2", 40112, "10.20.0.80", 80, "tcp")
KEY = LabelKey(
    "linux_slice",
    "lab/workstation[0]",
    "browse",
    "web_get",
    "lab/workstation[0]/browse#1",
    "http.httpx",
    None,
    ("lab/web_server[0]",),
)


def test_a_label_round_trips() -> None:
    label = Label(FLOW, KEY, "http.get", "succeeded", AttributionKey("linux", "cgroup:4242"), 1.5)
    data = to_json(label)
    assert isinstance(data, dict)
    assert data["signature"] == "http.get"
    assert data["flow"] == {"sensor": "zeek", "capture_point": "lan-span", "native": FLOW.native}
    assert from_json(Label, data) == label


def test_a_flag_round_trips_with_only_the_fields_its_kind_has() -> None:
    unattributed = Flag("unattributed", "no_attribution", 2.0, flow=FLOW, five_tuple=FIVE)
    failed = Flag("failed", "no_connection", 3.0, invocation=KEY.invocation)
    for flag in (unattributed, failed):
        assert from_json(Flag, to_json(flag)) == flag
    data = to_json(failed)
    assert isinstance(data, dict)
    assert data["flow"] is None
    assert data["invocation"] == "lab/workstation[0]/browse#1"
