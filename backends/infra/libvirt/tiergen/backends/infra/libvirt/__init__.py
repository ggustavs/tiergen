"""libvirt: Linux and Windows virtual machines under KVM.

Descriptor only. The backend arrives with the Windows guests of M1.
"""

from tiergen.interfaces import HostOffer, InfraDescriptor

DESCRIPTOR = InfraDescriptor(
    id="libvirt",
    offers=(
        # A VM owns its kernel, so there is nothing for the backend to grant.
        HostOffer("linux", "vm", None),
        HostOffer("windows", "vm", None),
    ),
)
