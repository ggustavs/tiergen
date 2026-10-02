from pathlib import Path

from tiergen.backends.infra._base import build_manifests
from tiergen.backends.infra._base.manifest import DEFAULT_IMAGE, IDLE
from tiergen.check.context import Context
from tiergen.core.addressing import plan_addresses
from tiergen.core.codec import from_json, to_json
from tiergen.core.loader import load_scenario
from tiergen.core.resources import DirResources
from tiergen.impls._base import load_impls
from tiergen.interfaces import Attachment, RunManifest
from tiergen.interfaces.registry import load_infra, load_sensors
from tiergen.protocols import SIGNATURES

EXAMPLES = Path(__file__).parents[4] / "examples"


def _manifests(name: str) -> dict[str, RunManifest]:
    scenario = load_scenario(EXAMPLES / name / "scenario.py")
    resources = DirResources(EXAMPLES / name / "models")
    impls = load_impls()
    ctx = Context(scenario, resources, impls, load_sensors(), load_infra(), SIGNATURES)
    topology = ctx.topology()
    assert topology is not None
    plan, problems = plan_addresses(scenario, topology)
    assert problems == []
    return build_manifests(scenario, topology, plan, impls, resources)


def test_linux_slice_is_one_docker_manifest() -> None:
    manifests = _manifests("linux_slice")
    assert list(manifests) == ["docker"]
    m = manifests["docker"]
    assert (m.run, m.backend) == ("linux_slice", "docker")
    assert [(n.name, n.gateway, n.internal) for n in m.networks] == [
        ("lan", "10.20.0.1", True),
        ("mgmt", "10.98.0.1", False),
    ]
    assert [h.instance for h in m.hosts] == [
        "lab/workstation[0]",
        "lab/web_server[0]",
        "lab/attacker[0]",
    ]
    web = m.hosts[1]
    assert (web.image, web.command) == (DEFAULT_IMAGE["linux"], IDLE)
    assert web.attachments == (Attachment("lan", "10.20.0.80"), Attachment("mgmt", "10.98.0.3"))
    assert web.cap_add == ()
    attacker = m.hosts[2]
    assert attacker.cap_add == ("NET_RAW",)  # nmap's manifest asks for it


def test_two_backends_split_the_hosts_and_share_the_networks_they_touch() -> None:
    manifests = _manifests("hq_lan")
    assert sorted(manifests) == ["docker", "libvirt"]
    libvirt = manifests["libvirt"]
    assert {h.kind for h in libvirt.hosts} == {"domain_controller", "workstation"}
    dc = next(h for h in libvirt.hosts if h.kind == "domain_controller")
    assert (dc.image, dc.command) == ("win2022-dc", ())
    assert dc.attachments[0] == Attachment("lan", "10.10.0.10")  # pinned in the topology
    assert [n.name for n in libvirt.networks] == ["lan", "mgmt"]
    docker = manifests["docker"]
    assert {h.kind for h in docker.hosts} == {"file_server", "intranet_web", "attacker"}
    web = next(h for h in docker.hosts if h.kind == "intranet_web")
    assert web.image == DEFAULT_IMAGE["linux"]


def test_manifests_are_data() -> None:
    for m in _manifests("linux_slice").values():
        assert from_json(RunManifest, to_json(m)) == m
