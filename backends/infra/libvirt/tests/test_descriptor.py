from tiergen.interfaces.registry import load_infra


def test_libvirt_offers_vms_of_both_platforms_with_nothing_to_grant() -> None:
    libvirt = load_infra()["libvirt"]
    for platform in ("linux", "windows"):
        offer = libvirt.offer(platform, "vm")
        assert offer is not None
        assert offer.grantable is None
    assert libvirt.offer("linux", "container") is None
