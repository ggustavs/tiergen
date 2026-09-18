from tiergen.interfaces import Capability
from tiergen.interfaces.registry import load_sensors


def test_suricata_is_registered_and_lacks_smb_dialect() -> None:
    suricata = load_sensors()["suricata"]
    assert Capability.APP_EVENTS in suricata.capabilities
    # The gap check 14 exists to catch when fit ran on Zeek.
    assert Capability.SMB_DIALECT not in suricata.capabilities
