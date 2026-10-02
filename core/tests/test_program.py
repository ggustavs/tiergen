from pathlib import Path

import pytest

from tiergen.core import ir
from tiergen.core.addressing import plan_addresses
from tiergen.core.codec import from_json, to_json
from tiergen.core.loader import load_scenario
from tiergen.core.program import Program, UnresolvedError, build_programs, flat_id
from tiergen.core.resolve import Resolver
from tiergen.core.resources import DirResources
from tiergen.core.routing import plan_routes

EXAMPLES = Path(__file__).parents[2] / "examples"
SERVERS = frozenset({"http.serve", "dns.serve", "smb.serve", "kerberos.serve", "ssh.serve"})


def _programs(name: str) -> dict[str, Program]:
    scenario = load_scenario(EXAMPLES / name / "scenario.py")
    resolver = Resolver(DirResources(EXAMPLES / name / "models"))
    topology = resolver.topology(scenario)
    assert topology is not None
    plan, _ = plan_addresses(scenario, topology)
    routes, _ = plan_routes(scenario, topology, plan)
    return build_programs(scenario, topology, plan, routes, resolver, SERVERS)


def test_hq_lan_programs_have_every_resource_inlined() -> None:
    programs = _programs("hq_lan")
    ws = programs["hq/workstation[0]"]
    [office] = ws.behaviours
    assert office.states == ("idle", "web_get", "smb_read", "krb_tgs")
    assert office.rate is not None
    assert len(office.rate) == 168
    web_get = office.action_map["web_get"]
    assert web_get is not None
    assert isinstance(web_get.params["path"], ir.Choice)  # from ws_office.http_paths
    assert web_get.select == "one"
    assert ws.impls["http.get"] == {"http.httpx": 1.0}
    assert [p.instance for p in ws.peers["dc"]] == ["hq/domain_controller[0]"]
    assert ws.peers["dc"][0].address == "10.10.0.10"
    assert {e.protocol for e in ws.peers["dc"][0].served} == {"kerberos", "ldap", "smb", "dns"}
    assert len(ws.peers["fs"]) == 2
    assert (ws.group, ws.kind, ws.platform) == ("hq", "workstation", "windows")
    assert ws.credentials is None
    assert ws.services == ()
    assert [(e.at_s, e.op, e.arg) for e in ws.schedule] == [(0.0, "start", "office")]
    web = programs["hq/intranet_web[0]"]
    assert web.services == ("http.serve",)
    assert web.schedule == ()


def test_two_teams_peers_are_reached_on_the_routed_segment() -> None:
    programs = _programs("two_teams")
    ws = programs["corp/eng/workstation[0]"]
    [dc] = ws.peers["dc"]
    assert dc.instance == "corp/domain_controller[0]"
    assert dc.address.startswith("10.30.0.")  # on core, reached through the router
    [fs] = ws.peers["fs"]
    assert fs.address.startswith("10.31.0.")  # on-link
    assert [r.segment for r in ws.routes] == ["core", "sales"]
    router = programs["corp/core_router[0]"]
    assert router.forwards is True
    assert router.behaviours == ()


def test_programs_are_data_and_file_names_are_flat() -> None:
    for instance, program in _programs("linux_slice").items():
        assert from_json(Program, to_json(program)) == program
        assert "/" not in flat_id(instance)
    assert flat_id("corp/eng/workstation[3]") == "corp-eng-workstation-3"


def test_a_missing_resource_is_an_error_not_a_default() -> None:
    scenario = load_scenario(EXAMPLES / "hq_lan_broken" / "scenario.py")
    resolver = Resolver(DirResources(EXAMPLES / "hq_lan_broken" / "models"))
    topology = resolver.topology(scenario)
    assert topology is not None
    plan, _ = plan_addresses(scenario, topology)
    routes, _ = plan_routes(scenario, topology, plan)
    with pytest.raises(UnresolvedError, match="office"):
        build_programs(scenario, topology, plan, routes, resolver, SERVERS)
