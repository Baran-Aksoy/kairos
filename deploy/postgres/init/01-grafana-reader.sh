#!/bin/bash
# Runs once, on first start of an empty PostgreSQL volume.
# Creates a read-only role for Grafana that can only read views in the "reporting" schema.
set -euo pipefail

psql -v ON_ERROR_STOP=1 \
     -v reader_password="$GRAFANA_DB_PASSWORD" \
     --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'EOSQL'
CREATE ROLE grafana_reader LOGIN PASSWORD :'reader_password';
CREATE SCHEMA IF NOT EXISTS reporting AUTHORIZATION CURRENT_USER;
REVOKE ALL ON SCHEMA public FROM grafana_reader;
GRANT CONNECT ON DATABASE kairos TO grafana_reader;
GRANT USAGE ON SCHEMA reporting TO grafana_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA reporting GRANT SELECT ON TABLES TO grafana_reader;
EOSQL
