"""The Zeek adapter over canned logs from a real run; the image runs in the daemon test."""

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import cast

import pytest

from tiergen.backends.infra.docker._client import Client
from tiergen.backends.sensor._base import SensorError
from tiergen.backends.sensor.zeek.runtime import Zeek
from tiergen.core.events import AppEvent, ConnEvent, SensorFlowId
from tiergen.core.ir import SensorSpec
from tiergen.interfaces import Capability, CapabilityInfo

SAMPLES = Path(__file__).with_name("samples")
SPEC = SensorSpec(
    "zeek",
    "zeek",
    "7.0.11",
    "linux_slice.zeek",
    "offline",
    ("APP_EVENTS", "HTTP_USER_AGENT"),
    "label",
)


def test_conn_log_is_the_core_and_http_log_the_app_events() -> None:
    sensor = Zeek(SPEC, "lan-span")
    events = list(sensor.ingest(SAMPLES))
    conns = [e for e in events if isinstance(e, ConnEvent)]
    apps = [e for e in events if isinstance(e, AppEvent)]
    assert len(conns) == 6
    web = next(c for c in conns if c.five_tuple.resp_port == 80 and c.state == "closed")
    assert web.flow == SensorFlowId("zeek", "lan-span", "C5ooLq3YdyDdtp0Zl1")
    assert web.five_tuple.orig_addr == "10.20.0.2"
    assert web.five_tuple.proto == "tcp"
    assert (web.orig_bytes, web.resp_bytes, web.orig_pkts, web.resp_pkts) == (142, 325, 6, 4)
    assert web.duration == 0.000905
    assert {c.state for c in conns} == {"closed", "rejected", "other", "reset"}
    quiet = next(c for c in conns if c.state == "other")
    assert quiet.duration is None
    assert quiet.orig_bytes is None
    [http] = apps
    assert http.flow == web.flow
    assert (http.protocol, http.index) == ("http", 0)
    assert http.fields["user_agent"] == "python-httpx/0.28.1"
    assert http.fields["uri"] == "/news"
    assert http.fields["status_code"] == 200
    assert http.raw["method"] == "GET"
    assert sensor.flow_key(http) == web.flow
    assert sensor.capabilities() == {
        Capability.APP_EVENTS: CapabilityInfo("app_events", 1.0),
        Capability.HTTP_USER_AGENT: CapabilityInfo("http_user_agent", 1.0),
    }


def test_the_json_form_gives_the_same_connections(tmp_path: Path) -> None:
    (tmp_path / "conn.log").write_bytes((SAMPLES / "conn.json.log").read_bytes())
    from_json = [e for e in Zeek(SPEC, "p").ingest(tmp_path) if isinstance(e, ConnEvent)]
    from_tsv = [e for e in Zeek(SPEC, "p").ingest(SAMPLES) if isinstance(e, ConnEvent)]
    assert from_json == from_tsv


def test_no_conn_log_is_an_error_naming_the_sensor(tmp_path: Path) -> None:
    with pytest.raises(SensorError, match=r"conn\.log"):
        list(Zeek(SPEC, "p").ingest(tmp_path))


class FakeDaemon:
    def __init__(self) -> None:
        self.calls: list[tuple[object, ...]] = []

    def userns(self) -> tuple[int, int] | None:
        return (100000, 100000)

    def ensure_image(self, image: str) -> None:
        self.calls.append(("pull", image))

    def run_helper(
        self,
        image: str,
        command: Sequence[str],
        network: str,
        cap_add: Sequence[str],
        mounts: Sequence[tuple[Path, str, bool]] = (),
        userns_host: bool = True,
    ) -> str:
        self.calls.append(("run", image, tuple(command)))
        return ""

    def image_digest(self, tag: str) -> str:
        return "zeek/zeek@sha256:abc"


@pytest.mark.skipif(sys.platform != "linux", reason="run sets ACLs with setfacl, a Linux call")
def test_run_reads_the_pcap_with_the_configuration_in_the_pinned_image(tmp_path: Path) -> None:
    fake = FakeDaemon()
    sensor = Zeek(SPEC, "lan-span", client=lambda: cast(Client, fake))
    pcap = tmp_path / "lan-span.pcapng"
    pcap.write_bytes(b"")
    config = tmp_path / "linux_slice.zeek"
    config.write_text("")
    digest = sensor.run(pcap, config, tmp_path / "out")
    assert digest == "zeek/zeek@sha256:abc"
    assert sensor.image == "zeek/zeek:7.0.11"
    assert fake.calls[0] == ("pull", "zeek/zeek:7.0.11")
    assert fake.calls[1][2] == (
        "sh",
        "-c",
        "cd /out && exec zeek -C -D -r /pcap/lan-span.pcapng /config/linux_slice.zeek",
    )
