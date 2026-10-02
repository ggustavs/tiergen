from pathlib import Path

from tiergen.backends.infra._base import build_manifests
from tiergen.backends.infra._base.manifest import DEFAULT_IMAGE, IDLE
from tiergen.check.context import Context
from tiergen.core.addressing import plan_addresses
from tiergen.core.codec import from_json, to_json
from tiergen.core.loader import load_scenario
from tiergen.core.resources import DirResources
from tiergen.core.routing import plan_routes
from tiergen.impls._base import load_impls
from tiergen.interfaces import RunManifest
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
    routes, _ = plan_routes(scenario, topology, plan)
    return build_manifests(scenario, topology, plan, routes, impls, resources)


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
    assert [(a.network, a.address) for a in web.attachments] == [
        ("lan", "10.20.0.80"),
        ("mgmt", "10.98.0.3"),
    ]
    assert all(a.mac is not None and a.mac.startswith("3c:ec:ef:") for a in web.attachments)
    assert (web.platform, web.hostname, web.forwards, web.routes) == (
        "linux",
        "lab-web-server-0",
        False,
        (),
    )
    assert web.cap_add == ()
    assert [(n.name, n.bridge[:3], len(n.bridge)) for n in m.networks] == [
        ("lan", "tg-", 15),
        ("mgmt", "tg-", 15),
    ]
    attacker = m.hosts[2]
    assert attacker.cap_add == ("NET_RAW",)  # nmap's manifest asks for it


def test_two_backends_split_the_hosts_and_share_the_networks_they_touch() -> None:
    manifests = _manifests("hq_lan")
    assert sorted(manifests) == ["docker", "libvirt"]
    libvirt = manifests["libvirt"]
    assert {h.kind for h in libvirt.hosts} == {"domain_controller", "workstation"}
    dc = next(h for h in libvirt.hosts if h.kind == "domain_controller")
    assert (dc.image, dc.command) == ("win2022-dc", ())
    assert (dc.attachments[0].network, dc.attachments[0].address) == ("lan", "10.10.0.10")  # pinned
    assert dc.attachments[0].mac is not None
    assert dc.attachments[0].mac.startswith("00:15:5d:")
    assert [n.name for n in libvirt.networks] == ["lan", "mgmt"]
    docker = manifests["docker"]
    assert {h.kind for h in docker.hosts} == {"file_server", "intranet_web", "attacker"}
    web = next(h for h in docker.hosts if h.kind == "intranet_web")
    assert web.image == DEFAULT_IMAGE["linux"]


def test_manifests_are_data() -> None:
    for m in _manifests("linux_slice").values():
        assert from_json(RunManifest, to_json(m)) == m


def test_two_teams_routes_go_through_the_core_router() -> None:
    docker = _manifests("two_teams")["docker"]
    router = next(h for h in docker.hosts if h.kind == "core_router")
    assert router.forwards is True
    assert router.routes == ()  # on every segment already
    assert [a.network for a in router.attachments] == ["core", "eng", "sales", "mgmt"]
    eng_fs = next(h for h in docker.hosts if h.instance == "corp/eng/file_server[0]")
    via = next(a.address for a in router.attachments if a.network == "eng")
    assert {(r.cidr, r.via) for r in eng_fs.routes} == {
        ("10.30.0.0/24", via),
        ("10.32.0.0/24", via),
    }
