"""Tenant isolation invariant (ADR 0003)."""

import pytest

from kairos.models import Base

TENANT_ROOT = "clients"


@pytest.mark.parametrize(
    "table", [t for name, t in Base.metadata.tables.items() if name != TENANT_ROOT], ids=str
)
def test_every_table_carries_client_id(table):
    assert "client_id" in table.columns, f"{table.name} must have a client_id column"
    assert not table.columns["client_id"].nullable
