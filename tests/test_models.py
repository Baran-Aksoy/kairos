"""Tenant isolation invariant (ADR 0003)."""

import pytest

from kairos.models import Base

TENANT_ROOT = "clients"
# Public reference data shared by all clients (ADR 0003, exception). Never client data.
GLOBAL_TABLES = {"release_cycles"}


@pytest.mark.parametrize(
    "table",
    [t for name, t in Base.metadata.tables.items() if name not in {TENANT_ROOT, *GLOBAL_TABLES}],
    ids=str,
)
def test_every_table_carries_client_id(table):
    assert "client_id" in table.columns, f"{table.name} must have a client_id column"
    assert not table.columns["client_id"].nullable
