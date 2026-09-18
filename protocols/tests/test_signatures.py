from tiergen.core.codec import from_json, to_json
from tiergen.protocols import SIGNATURES, Signature, dns, http, kerberos, scan, smb, ssh

MODULES = (http, dns, smb, kerberos, ssh, scan)


def test_ids_are_unique_across_modules() -> None:
    assert len(SIGNATURES) == sum(len(module.SIGNATURES) for module in MODULES)


def test_the_six_m0_protocols_are_present() -> None:
    assert {s.protocol for s in SIGNATURES.values()} == {
        "http",
        "dns",
        "smb",
        "kerberos",
        "ssh",
        "scan",
    }


def test_id_is_protocol_dot_name_and_lives_in_the_module_of_its_protocol() -> None:
    for module in MODULES:
        protocol = module.__name__.rsplit(".", 1)[1]
        for signature in module.SIGNATURES:
            assert signature.protocol == protocol
            assert signature.id.startswith(f"{protocol}.")


def test_follow_on_references_resolve_to_client_signatures() -> None:
    for signature in SIGNATURES.values():
        for other in signature.shape.follow_on:
            assert SIGNATURES[other].role == "client", (signature.id, other)


def test_server_signatures_open_no_connections_and_take_no_params() -> None:
    servers = [s for s in SIGNATURES.values() if s.role == "server"]
    assert {s.id for s in servers} == {
        f"{p}.serve" for p in ("http", "dns", "smb", "kerberos", "ssh")
    }
    for signature in servers:
        assert signature.shape.connections == 0
        assert signature.params == ()


def test_only_scans_need_no_served_endpoint() -> None:
    assert {s.protocol for s in SIGNATURES.values() if not s.endpoints} == {"scan"}


def test_signatures_are_data() -> None:
    for signature in SIGNATURES.values():
        assert from_json(Signature, to_json(signature)) == signature
