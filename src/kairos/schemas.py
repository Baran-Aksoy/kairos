from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

NonEmpty = Annotated[str, Field(min_length=1, max_length=255)]


class OsIn(BaseModel):
    distribution: NonEmpty
    version: NonEmpty
    kernel: NonEmpty


class PackageIn(BaseModel):
    # package_facts also sends arch, source, category...: ignored for now.
    model_config = ConfigDict(extra="ignore")

    name: NonEmpty
    version: NonEmpty


class InventoryIn(BaseModel):
    """Inventory of one host, as sent by the kairos_collect Ansible role.

    Unknown top-level fields are rejected: in particular the body can never name a client,
    the client is always derived from the token.
    """

    model_config = ConfigDict(extra="forbid")

    hostname: NonEmpty
    machine_id: str | None = Field(default=None, max_length=64)
    collected_at: datetime
    os: OsIn
    packages: list[PackageIn]


class InventoryOut(BaseModel):
    hostname: str
    snapshot_id: int
    packages: int
