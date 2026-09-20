from support import IMPLS, INFRA, RESOURCES, SENSORS, good, only, run, surf, with_binding

from tiergen.check import run_checks
from tiergen.core import dsl, ir
from tiergen.core.resources import DictResources
from tiergen.interfaces import HostOffer, InfraDescriptor

# The server kind allows linux only, and its service implementation runs on linux only.
WINDOWS_VM = dsl.host("windows", "vm", "template:w", backend="libvirt")


def _scanning(host: ir.Host) -> ir.Scenario:
    """The baseline client running a raw-socket scan, which needs net_raw, from ``host``."""
    actions = {"idle": None, "get": dsl.action("scan.tcp_syn", "web", {"ports": "1-1024"})}
    selection = ir.ImplSelection("scan.tcp_syn", {"scan.raw": 1.0})
    return with_binding(good(surf(action_map=actions)), 0, host=host, impls=(selection,))


def test_binding_platform_the_kind_does_not_allow() -> None:
    found = [d for d in run(with_binding(good(), 1, host=WINDOWS_VM)) if d.check == "C07"]
    assert found[0].path == "bindings[1].host.platform"
    assert "allows linux, not windows" in found[0].message


def test_implementation_that_does_not_run_on_the_bound_platform() -> None:
    found = [d for d in run(with_binding(good(), 1, host=WINDOWS_VM)) if d.check == "C07"]
    assert [d.path for d in found][1:] == ["bindings[1].impls[0].choices['http.srv']"]
    assert "does not run on windows" in found[1].message


def test_backend_that_is_not_installed() -> None:
    [d] = only("C07", with_binding(good(), 0, host=dsl.host("linux", "container", backend="nomad")))
    assert d.path == "bindings[0].host.backend"
    assert "'nomad' is not installed" in d.message


def test_host_the_backend_does_not_offer() -> None:
    [d] = only(
        "C07", with_binding(good(), 0, host=dsl.host("windows", "container", backend="docker"))
    )
    assert d.path == "bindings[0].host"
    assert "docker offers no windows container; it offers: linux container" in d.message


def test_host_capability_the_backend_can_grant() -> None:
    assert only("C07", _scanning(dsl.host("linux", "container", backend="docker"))) == []


def test_host_capability_the_backend_cannot_grant() -> None:
    strict = {
        **INFRA,
        "docker": InfraDescriptor("docker", (HostOffer("linux", "container", frozenset()),)),
    }
    store = DictResources(RESOURCES, frozenset({"lan.rich", "lan.poor"}))
    s = _scanning(dsl.host("linux", "container", backend="docker"))
    [d] = [d for d in run_checks(s, store, IMPLS, SENSORS, strict) if d.check == "C07"]
    assert d.severity == "error"
    assert (
        "needs host capability 'net_raw', which docker cannot grant a linux container" in d.message
    )


def test_a_vm_owns_its_kernel_so_there_is_nothing_to_grant() -> None:
    assert only("C07", _scanning(dsl.host("linux", "vm", "template:kali", backend="libvirt"))) == []
