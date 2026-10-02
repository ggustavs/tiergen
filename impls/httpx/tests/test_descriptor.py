from tiergen.impls._base import load_impls, load_runtime
from tiergen.protocols import SIGNATURES


def test_registered_and_provides_known_signatures() -> None:
    descriptor = load_impls()["http.httpx"]
    assert descriptor.provides
    for signature in descriptor.provides:
        wanted = "server" if descriptor.kind == "service" else "client"
        assert SIGNATURES[signature].role == wanted


def test_the_runtime_is_registered_under_the_same_id() -> None:
    assert type(load_runtime("http.httpx")).__name__ == "HttpxRuntime"
