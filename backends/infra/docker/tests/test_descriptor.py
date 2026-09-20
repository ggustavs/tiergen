from tiergen.interfaces.registry import load_infra


def test_docker_offers_linux_containers_and_can_grant_net_raw() -> None:
    docker = load_infra()["docker"]
    offer = docker.offer("linux", "container")
    assert offer is not None
    assert offer.grantable is not None
    assert "net_raw" in offer.grantable
    assert docker.offer("windows", "container") is None
    assert docker.offer("linux", "vm") is None
