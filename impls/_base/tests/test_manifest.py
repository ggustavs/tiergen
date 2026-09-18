import pytest

from tiergen.core.ir import Endpoint
from tiergen.impls._base import ManifestError, parse_manifest

# The sample from section 6.1 of the design document.
PLAYWRIGHT = """
id = "http.playwright"
version = "0.1.0"
kind = "primitive"                 # primitive | service | adapter
provides = ["http.browse", "http.get", "http.post_form"]
variants = ["chromium", "firefox", "webkit"]
[host]
platforms = ["linux", "windows"]
binaries = []                      # resolved per platform by the package
capabilities = []                  # e.g. ["net_raw"] for scanners
image_base = { linux = "tiergen/base-desktop", windows = "tiergen/base-desktop-win" }
[fingerprint]
role = "client"
product = "playwright"
ja4 = { chromium = "auto", firefox = "auto", webkit = "auto" }   # measured by the conformance test
user_agent = "auto"
"""

SERVICE = """
id = "http.example"
version = "1"
kind = "service"
provides = ["http.serve"]
[host]
platforms = ["linux"]
[service]
served = [{ protocol = "http", port = 80, transport = "tcp" }]
"""


def test_the_design_document_sample_loads() -> None:
    d = parse_manifest(PLAYWRIGHT, "impl.toml")
    assert d.id == "http.playwright"
    assert d.variants == ("chromium", "firefox", "webkit")
    assert d.host.platforms == ("linux", "windows")
    assert d.host.image_base["windows"] == "tiergen/base-desktop-win"
    assert d.fingerprint is not None
    assert d.fingerprint.ja4["firefox"] == "auto"
    assert d.service is None


def test_a_service_declares_what_it_serves() -> None:
    d = parse_manifest(SERVICE, "impl.toml")
    assert d.service is not None
    assert d.service.served == (Endpoint("http", 80, "tcp"),)


@pytest.mark.parametrize(
    ("text", "fragment"),
    [
        (PLAYWRIGHT.replace('kind = "primitive"', 'kind = "plugin"'), "kind: expected one of"),
        (
            PLAYWRIGHT.replace('platforms = ["linux", "windows"]', 'platforms = ["linux", "beos"]'),
            "host.platforms[1]",
        ),
        (PLAYWRIGHT.replace('version = "0.1.0"', ""), "missing field 'version'"),
        (PLAYWRIGHT + 'colour = "red"\n', "fingerprint: unknown field"),
        (SERVICE.replace("port = 80", 'port = "80"'), "service.served[0].port"),
        (SERVICE.replace('kind = "service"', 'kind = "primitive"'), "[service] table"),
        (PLAYWRIGHT.replace('kind = "primitive"', 'kind = "service"'), "[service] table"),
        ("id = ", "impl.toml"),
    ],
)
def test_a_malformed_manifest_names_the_file_and_the_path(text: str, fragment: str) -> None:
    with pytest.raises(ManifestError) as info:
        parse_manifest(text, "pkg/impl.toml")
    assert "pkg/impl.toml" in str(info.value)
    assert fragment in str(info.value)
