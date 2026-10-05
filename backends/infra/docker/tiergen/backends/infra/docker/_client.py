# pyright: basic
# The Docker SDK stubs leave several signatures partially typed; this is the one module that
# touches them, so it is checked at basic strictness like the z3 facade was.
"""The one module that touches the Docker SDK.

``Client`` is what the backend needs of a daemon, as a Protocol, so the backend's logic is
tested against a fake and only this module is tested against a daemon. Resource names are
daemon-wide, so every name is prefixed with the run.
"""

import contextlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, Protocol

import docker
import docker.errors
import docker.types
from tiergen.interfaces.infra import BackendError

CgroupNs = Literal["private", "host"]


class Client(Protocol):
    """What the backend asks of a daemon. Names are the backend's, already prefixed."""

    def ensure_image(self, image: str) -> None:
        """Make ``image`` available locally, pulling it if need be."""
        ...

    def userns(self) -> tuple[int, int] | None:
        """The host uid and gid the daemon's user-namespace remap gives a container's root,
        or None when the daemon runs without one."""
        ...

    def image_id(self, tag: str) -> str | None:
        """The id of the local image tagged ``tag``, or None if there is none."""
        ...

    def build_image(self, tag: str, context: Path) -> str:
        """Build ``context/Dockerfile`` as ``tag``. Returns the image id."""
        ...

    def create_network(
        self,
        name: str,
        cidr: str,
        gateway: str,
        internal: bool,
        bridge: str,
        labels: Mapping[str, str],
    ) -> None:
        """Create a bridge network whose Linux bridge is called ``bridge``."""
        ...

    def create_container(
        self,
        name: str,
        image: str,
        command: Sequence[str],
        cap_add: Sequence[str],
        labels: Mapping[str, str],
        network: str,
        address: str,
        mac: str | None,
        hostname: str,
        sysctls: Mapping[str, str],
        mounts: Sequence[tuple[Path, str, bool]],
        cgroupns: CgroupNs | None,
    ) -> str:
        """Create, attached to ``network`` at ``address``, not started. Returns the id.

        ``mounts`` are bind mounts, (host path, container path, read-only); ``cgroupns`` is
        the container's cgroup namespace mode, "private" or "host", or the daemon's default.
        """
        ...

    def connect(self, container: str, network: str, address: str, mac: str | None) -> None: ...

    def start(self, container: str) -> None: ...

    def exec(self, container: str, command: Sequence[str]) -> None:
        """Run ``command`` in the running container; a non-zero exit is a ``BackendError``."""
        ...

    def containers(self, labels: Mapping[str, str]) -> list[str]:
        """Names of all containers, running or not, carrying every label."""
        ...

    def networks(self, labels: Mapping[str, str]) -> list[str]: ...

    def remove_container(self, name: str) -> None: ...

    def remove_network(self, name: str) -> None: ...

    def addresses(self, container: str) -> dict[str, str]:
        """``network name -> IPv4 address`` of a container, as the daemon reports them."""
        ...

    def run_helper(
        self, image: str, command: Sequence[str], network: str, cap_add: Sequence[str]
    ) -> str:
        """Run ``command`` to completion in a throwaway container as the daemon's own root
        (no user-namespace remap), on ``network`` ("host", or "container:<name>" to join a
        container's network namespace), with ``cap_add``. Returns its output; a non-zero
        exit is a ``BackendError``."""
        ...


def _selector(labels: Mapping[str, str]) -> dict[str, str | list[str] | bool]:
    return {"label": [f"{k}={v}" for k, v in labels.items()]}


class DaemonClient:
    """``Client`` over the local daemon."""

    def __init__(self) -> None:
        try:
            self._d = docker.from_env()
            self._info = self._d.info()
        except docker.errors.DockerException as err:
            raise BackendError(f"docker daemon is not reachable: {err}") from err
        os_type = self._info.get("OSType")
        if os_type != "linux":
            # The Windows daemon runs Windows containers; that backend is a later task of M1.
            raise BackendError(
                f"docker daemon runs {os_type!r} containers; this backend needs linux"
            )

    def ensure_image(self, image: str) -> None:
        try:
            self._d.images.get(image)
            return
        except docker.errors.ImageNotFound:
            pass
        try:
            self._d.images.pull(image)
        except docker.errors.APIError as err:
            raise BackendError(f"image {image!r} is not available: {err}") from err

    def userns(self) -> tuple[int, int] | None:
        # With a remap the daemon lists "name=userns" and keeps its data under a directory
        # named "<uid>.<gid>" of the remapped root; that is the only place the ids appear.
        if "name=userns" not in self._info.get("SecurityOptions", []):
            return None
        uid, _, gid = Path(self._info["DockerRootDir"]).name.partition(".")
        return int(uid), int(gid)

    def image_id(self, tag: str) -> str | None:
        try:
            return self._d.images.get(tag).id
        except docker.errors.ImageNotFound:
            return None

    def build_image(self, tag: str, context: Path) -> str:
        try:
            image, _ = self._d.images.build(path=str(context), tag=tag, rm=True)
        except docker.errors.BuildError as err:
            raise BackendError(f"cannot build {tag!r}: {err}") from err
        except docker.errors.APIError as err:
            raise BackendError(f"cannot build {tag!r}: {err}") from err
        return image.id or tag

    def create_network(
        self,
        name: str,
        cidr: str,
        gateway: str,
        internal: bool,
        bridge: str,
        labels: Mapping[str, str],
    ) -> None:
        pool = docker.types.IPAMPool(subnet=cidr, gateway=gateway)
        self._d.networks.create(
            name,
            driver="bridge",
            internal=internal,
            ipam=docker.types.IPAMConfig(pool_configs=[pool]),
            options={"com.docker.network.bridge.name": bridge},
            labels=dict(labels),
        )

    def create_container(
        self,
        name: str,
        image: str,
        command: Sequence[str],
        cap_add: Sequence[str],
        labels: Mapping[str, str],
        network: str,
        address: str,
        mac: str | None,
        hostname: str,
        sysctls: Mapping[str, str],
        mounts: Sequence[tuple[Path, str, bool]],
        cgroupns: CgroupNs | None,
    ) -> str:
        endpoint = self._d.api.create_endpoint_config(ipv4_address=address, mac_address=mac)
        binds = [
            docker.types.Mount(target, str(source), type="bind", read_only=read_only)
            for source, target, read_only in mounts
        ]
        try:
            created = self._d.containers.create(
                image,
                command=list(command) or None,
                name=name,
                hostname=hostname,
                labels=dict(labels),
                cap_add=list(cap_add) or None,
                sysctls=dict(sysctls) or None,
                mounts=binds or None,
                cgroupns=cgroupns,
                network=network,
                networking_config={network: endpoint},
                detach=True,
            )
        except docker.errors.ImageNotFound as err:
            raise BackendError(f"image {image!r} is not available: {err}") from err
        except docker.errors.APIError as err:
            raise BackendError(f"cannot create {name!r}: {err}") from err
        return created.id or name

    def connect(self, container: str, network: str, address: str, mac: str | None) -> None:
        try:
            self._d.networks.get(network).connect(container, ipv4_address=address, mac_address=mac)
        except docker.errors.APIError as err:
            raise BackendError(f"cannot attach {container!r} to {network!r}: {err}") from err

    def exec(self, container: str, command: Sequence[str]) -> None:
        result = self._d.containers.get(container).exec_run(list(command))
        if result.exit_code != 0:
            raw = result.output if isinstance(result.output, bytes) else b"".join(result.output)
            text = raw.decode(errors="replace").strip()
            raise BackendError(
                f"{' '.join(command)!r} in {container!r} failed ({result.exit_code}): {text}"
            )

    def start(self, container: str) -> None:
        try:
            self._d.containers.get(container).start()
        except docker.errors.APIError as err:
            raise BackendError(f"cannot start {container!r}: {err}") from err

    def containers(self, labels: Mapping[str, str]) -> list[str]:
        found = self._d.containers.list(all=True, filters=_selector(labels))
        return [c.name for c in found if c.name is not None]

    def networks(self, labels: Mapping[str, str]) -> list[str]:
        found = self._d.networks.list(filters=_selector(labels))
        return [n.name for n in found if n.name is not None]

    def remove_container(self, name: str) -> None:
        with contextlib.suppress(docker.errors.NotFound):
            self._d.containers.get(name).remove(force=True)

    def remove_network(self, name: str) -> None:
        with contextlib.suppress(docker.errors.NotFound):
            self._d.networks.get(name).remove()

    def run_helper(
        self, image: str, command: Sequence[str], network: str, cap_add: Sequence[str]
    ) -> str:
        try:
            output = self._d.containers.run(
                image,
                command=list(command),
                remove=True,
                network_mode=network,
                userns_mode="host",
                cap_add=list(cap_add),
                stderr=True,
            )
        except docker.errors.ContainerError as err:
            raise BackendError(f"helper {' '.join(command)!r} failed: {err}") from err
        except docker.errors.APIError as err:
            raise BackendError(f"cannot run helper {' '.join(command)!r}: {err}") from err
        return output.decode(errors="replace") if isinstance(output, bytes) else str(output)

    def addresses(self, container: str) -> dict[str, str]:
        attrs = self._d.containers.get(container).attrs
        networks: dict[str, dict[str, str]] = attrs["NetworkSettings"]["Networks"]
        return {name: settings["IPAddress"] for name, settings in networks.items()}
