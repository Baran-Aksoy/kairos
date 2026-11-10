"""CycloneDX SBOM built from a collected snapshot (story 004, prototype).

The SBOM is what Kairos hands to a vulnerability scanner (Trivy) so that nothing has to be
installed on the VMs. Package URLs follow the purl spec for Debian/Ubuntu packages.
"""

from dataclasses import dataclass
from urllib.parse import quote

from sqlalchemy import select
from sqlalchemy.orm import Session

from kairos.models import Client, Host, Installation, Snapshot


@dataclass(frozen=True)
class SourcePackage:
    """Source package of a binary package: what distro security trackers are keyed on."""

    name: str
    version: str


def split_epoch(version: str) -> tuple[str | None, str]:
    epoch, sep, rest = version.partition(":")
    return (epoch, rest) if sep and epoch.isdigit() else (None, version)


def deb_purl(distro: str, distro_version: str, name: str, version: str, arch: str | None = None,
             source: SourcePackage | None = None) -> str:  # fmt: skip
    epoch, bare = split_epoch(version)
    qualifiers = []
    if arch:
        qualifiers.append(f"arch={arch}")
    qualifiers.append(f"distro={distro}-{distro_version}")
    if epoch:
        qualifiers.append(f"epoch={epoch}")
    if source and source.name != name:
        qualifiers.append(f"upstream={quote(source.name, safe='')}")
    return f"pkg:deb/{distro}/{quote(name, safe='')}@{quote(bare, safe='.+~-')}?" + "&".join(
        qualifiers
    )


def build_sbom(
    hostname: str,
    distribution: str,
    distro_version: str,
    packages: list[tuple[str, str]],
    sources: dict[str, SourcePackage] | None = None,
) -> dict:
    """Return a CycloneDX 1.5 document for one host.

    ``sources`` maps binary package names to their source package. Without it, scanners can
    only match on binary names, which misses advisories published per source package.
    """
    distro = distribution.lower()
    sources = sources or {}
    components = []
    for name, version in sorted(packages):
        source = sources.get(name)
        purl = deb_purl(distro, distro_version, name, version, source=source)
        component = {"type": "library", "bom-ref": purl, "name": name, "version": version,
                     "purl": purl}  # fmt: skip
        if source:
            # Trivy reads these properties to match the distro advisory of the source package.
            component["properties"] = [
                {"name": "aquasecurity:trivy:SrcName", "value": source.name},
                {"name": "aquasecurity:trivy:SrcVersion", "value": source.version},
            ]
        components.append(component)

    os_ref = f"os:{distro}-{distro_version}"
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "tools": {"components": [{"type": "application", "name": "kairos"}]},
            # Trivy rejects "device"; "application" is what it uses for filesystem scans.
            "component": {"type": "application", "bom-ref": "host", "name": hostname},
        },
        "components": [
            {
                "type": "operating-system",
                "bom-ref": os_ref,
                "name": distro,
                "version": distro_version,
            },  # fmt: skip
            *components,
        ],
        "dependencies": [
            {"ref": "host", "dependsOn": [os_ref]},
            {"ref": os_ref, "dependsOn": [c["bom-ref"] for c in components]},
        ],
    }


def sbom_for_host(session: Session, slug: str, hostname: str) -> dict | None:
    """SBOM of the latest snapshot of ``hostname``, strictly within client ``slug``."""
    row = session.execute(
        select(Snapshot)
        .join(Host, Host.id == Snapshot.host_id)
        .join(Client, Client.id == Snapshot.client_id)
        .where(Client.slug == slug, Host.hostname == hostname, Host.client_id == Client.id)
        .order_by(Snapshot.id.desc())
        .limit(1)
    ).scalar_one_or_none()
    if row is None or not row.os_distribution or not row.os_version:
        return None
    packages = session.execute(
        select(Installation.name, Installation.version).where(
            Installation.client_id == row.client_id, Installation.snapshot_id == row.id
        )
    ).all()
    return build_sbom(hostname, row.os_distribution, row.os_version, [tuple(p) for p in packages])
