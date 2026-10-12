from tiergen.backends.attrib._base import backends_for, uncovered
from tiergen.interfaces import Attachment, HostSpec, RunManifest


def _host(instance: str, platform: str) -> HostSpec:
    return HostSpec(
        instance,
        "k",
        platform,  # type: ignore[arg-type]
        instance.replace("/", "-"),
        "img",
        (),
        (),
        (Attachment("lan", "10.0.0.2"),),
        agent=True,
    )


def test_each_substrate_and_platform_names_its_collector_and_the_rest_is_uncovered() -> None:
    docker = RunManifest("r", "docker", (), (_host("lab/ws[0]", "linux"),))
    assert backends_for(docker) == {"linux_ebpf": {"linux"}}
    assert uncovered(docker) == set()
    mixed = RunManifest(
        "r", "libvirt", (), (_host("hq/ws[0]", "linux"), _host("hq/dc[0]", "windows"))
    )
    assert backends_for(mixed) == {"linux_ebpf_guest": {"linux"}}
    assert uncovered(mixed) == {"windows"}
    assert backends_for(RunManifest("r", "other", (), ())) == {}
