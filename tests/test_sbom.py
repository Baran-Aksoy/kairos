"""Story 004: CycloneDX SBOM generation (the Trivy comparison itself is documented in ADR 0005)."""

import json

from kairos.cli import main
from kairos.sbom import SourcePackage, build_sbom, deb_purl


def test_purl_moves_epoch_to_qualifier_and_names_upstream():
    purl = deb_purl("ubuntu", "24.04", "libssl3t64", "3.0.13-0ubuntu3.5",
                    source=SourcePackage("openssl", "3.0.13-0ubuntu3.5"))  # fmt: skip
    assert purl == (
        "pkg:deb/ubuntu/libssl3t64@3.0.13-0ubuntu3.5?distro=ubuntu-24.04&upstream=openssl"
    )
    assert deb_purl("ubuntu", "24.04", "openssh-server", "1:9.6p1-3ubuntu13.5") == (
        "pkg:deb/ubuntu/openssh-server@9.6p1-3ubuntu13.5?distro=ubuntu-24.04&epoch=1"
    )


def test_sbom_has_os_component_and_source_properties():
    sbom = build_sbom(
        "vm-01",
        "Ubuntu",
        "24.04",
        [("libssl3t64", "3.0.13-0ubuntu3.5"), ("bash", "5.2.21-2ubuntu4")],
        {"libssl3t64": SourcePackage("openssl", "3.0.13-0ubuntu3.5")},
    )

    os_component, *packages = sbom["components"]
    assert os_component == {"type": "operating-system", "bom-ref": "os:ubuntu-24.04",
                            "name": "ubuntu", "version": "24.04"}  # fmt: skip
    libssl = next(p for p in packages if p["name"] == "libssl3t64")
    assert {"name": "aquasecurity:trivy:SrcName", "value": "openssl"} in libssl["properties"]
    assert "properties" not in next(p for p in packages if p["name"] == "bash")
    assert sbom["dependencies"][1]["dependsOn"] == [p["bom-ref"] for p in packages]


def test_cli_sbom_is_scoped_to_the_client(api, make_client, session_factory, capsys):
    _, token = make_client("client-a")
    make_client("client-b")
    body = {
        "hostname": "vm-01",
        "collected_at": "2026-11-10T08:00:00Z",
        "os": {"distribution": "Ubuntu", "version": "24.04", "kernel": "6.8.0-48-generic"},
        "packages": [{"name": "bash", "version": "5.2.21-2ubuntu4"}],
    }
    api.post("/api/v1/inventory", json=body, headers={"Authorization": f"Bearer {token}"})

    assert main(["sbom", "client-a", "vm-01"], session_factory) == 0
    document = json.loads(capsys.readouterr().out)
    assert [c["name"] for c in document["components"]] == ["ubuntu", "bash"]

    assert main(["sbom", "client-b", "vm-01"], session_factory) == 1
