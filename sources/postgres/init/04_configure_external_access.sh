#!/bin/bash
set -e

# Configure PostgreSQL for external access
# This script modifies pg_hba.conf to allow connections from outside Docker network

echo "Configuring PostgreSQL for external access..."

# Append rules to pg_hba.conf to allow external connections
cat >> "$PGDATA/pg_hba.conf" <<'EOFMARKER'

# Allow connections from external hosts (for Kubernetes/Airbyte)
host    all             all             0.0.0.0/0               md5
host    all             all             ::/0                    md5

# Allow replication from external hosts
host    replication     all             0.0.0.0/0               md5
host    replication     all             ::/0                    md5
EOFMARKER

echo "External access configuration complete."
