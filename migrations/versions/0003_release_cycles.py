"""Release cycles: public end-of-life reference data from endoflife.date.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "release_cycles",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("product", sa.String(64), nullable=False),
        sa.Column("cycle", sa.String(64), nullable=False),
        sa.Column("codename", sa.String(128), nullable=True),
        sa.Column("lts", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("release_date", sa.Date(), nullable=True),
        sa.Column("eol", sa.Date(), nullable=True),
        sa.Column("extended_support", sa.Date(), nullable=True),
        sa.Column("latest", sa.String(64), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("product", "cycle"),
    )


def downgrade() -> None:
    op.drop_table("release_cycles")
