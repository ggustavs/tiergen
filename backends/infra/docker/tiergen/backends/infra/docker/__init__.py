"""Docker: Linux containers on the local Linux daemon.

The descriptor; the runtime is ``tiergen.backends.infra.docker.backend``. The Windows
daemon, and with it Windows containers, is the last task of M1 and adds a second offer here.
"""

from tiergen.interfaces import HostOffer, InfraDescriptor

DESCRIPTOR = InfraDescriptor(
    id="docker",
    offers=(
        # What `docker run --cap-add` can give a container that an implementation may need.
        HostOffer("linux", "container", frozenset({"net_raw", "net_admin"})),
    ),
)
