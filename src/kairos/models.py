"""Core inventory model.

Tenant rule: every table except ``clients`` carries a ``client_id`` column, even when it
could be derived through a parent, so every query can filter by tenant directly and
PostgreSQL row-level security can be added later. Enforced by tests/test_models.py.

Catalog (products, release cycles), vulnerabilities and findings will be added by the
stories that need them.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

JSONType = JSON().with_variant(JSONB(), "postgresql")
# SQLite (tests) only auto-increments INTEGER primary keys.
BigIntPK = BigInteger().with_variant(Integer(), "sqlite")


class Base(DeclarativeBase):
    pass


class Client(Base):
    """A managed customer (tenant)."""

    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    hosts: Mapped[list["Host"]] = relationship(back_populates="client")


class CollectToken(Base):
    """Write-only token used by AWX to send a client's inventory. Only its SHA-256 is stored."""

    __tablename__ = "collect_tokens"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Host(Base):
    """A machine belonging to a client, identified by hostname within that client."""

    __tablename__ = "hosts"
    __table_args__ = (UniqueConstraint("client_id", "hostname"),)

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    hostname: Mapped[str] = mapped_column(String(255))
    machine_id: Mapped[str | None] = mapped_column(String(64))
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    client: Mapped[Client] = relationship(back_populates="hosts")
    snapshots: Mapped[list["Snapshot"]] = relationship(back_populates="host")


class Snapshot(Base):
    """One collection run on one host: OS details plus the raw facts as received."""

    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id", ondelete="CASCADE"), index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    os_distribution: Mapped[str | None] = mapped_column(String(64))
    os_version: Mapped[str | None] = mapped_column(String(64))
    kernel_running: Mapped[str | None] = mapped_column(String(128))
    raw: Mapped[dict] = mapped_column(JSONType, default=dict)

    host: Mapped[Host] = relationship(back_populates="snapshots")
    installations: Mapped[list["Installation"]] = relationship(back_populates="snapshot")


class Installation(Base):
    """A piece of software found on a host during a snapshot."""

    __tablename__ = "installations"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    snapshot_id: Mapped[int] = mapped_column(
        ForeignKey("snapshots.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    version: Mapped[str] = mapped_column(String(255))
    # apt | rpm | snap | docker | binary | pip | ...
    source: Mapped[str] = mapped_column(String(32))
    # package | binary_version | docker_ps | port | ...
    detection_method: Mapped[str] = mapped_column(String(32))
    path: Mapped[str | None] = mapped_column(String(1024))
    listening: Mapped[bool | None]

    snapshot: Mapped[Snapshot] = relationship(back_populates="installations")
