"""Initial inventory schema: clients, hosts, snapshots, installations.

Also creates the empty ``reporting`` schema that Grafana reads (views only).

Revision ID: 0001
Revises:
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS reporting")

    op.create_table(
        "clients",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )

    op.create_table(
        "hosts",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "client_id",
            sa.BigInteger(),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("hostname", sa.String(255), nullable=False),
        sa.Column("machine_id", sa.String(64), nullable=True),
        sa.Column(
            "first_seen", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "last_seen", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("client_id", "hostname"),
    )

    op.create_table(
        "snapshots",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "client_id",
            sa.BigInteger(),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "host_id",
            sa.BigInteger(),
            sa.ForeignKey("hosts.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("os_distribution", sa.String(64), nullable=True),
        sa.Column("os_version", sa.String(64), nullable=True),
        sa.Column("kernel_running", sa.String(128), nullable=True),
        sa.Column("raw", postgresql.JSONB(), nullable=False),
    )

    op.create_table(
        "installations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "client_id",
            sa.BigInteger(),
            sa.ForeignKey("clients.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "snapshot_id",
            sa.BigInteger(),
            sa.ForeignKey("snapshots.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.String(255), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("detection_method", sa.String(32), nullable=False),
        sa.Column("path", sa.String(1024), nullable=True),
        sa.Column("listening", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("installations")
    op.drop_table("snapshots")
    op.drop_table("hosts")
    op.drop_table("clients")
    op.execute("DROP SCHEMA IF EXISTS reporting")
