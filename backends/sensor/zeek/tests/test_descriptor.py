from tiergen.interfaces import Capability
from tiergen.interfaces.registry import load_sensors


def test_zeek_is_registered_with_the_richer_capability_set() -> None:
    sensors = load_sensors()
    zeek = sensors["zeek"]
    assert Capability.APP_EVENTS in zeek.capabilities
    assert Capability.SMB_DIALECT in zeek.capabilities
    assert "offline" in zeek.modes
