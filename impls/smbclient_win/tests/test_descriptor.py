from tiergen.impls._base import load_impls
from tiergen.protocols import SIGNATURES


def test_registered_and_provides_known_signatures() -> None:
    descriptor = load_impls()["smb.windows_native"]
    assert descriptor.provides
    for signature in descriptor.provides:
        wanted = "server" if descriptor.kind == "service" else "client"
        assert SIGNATURES[signature].role == wanted
