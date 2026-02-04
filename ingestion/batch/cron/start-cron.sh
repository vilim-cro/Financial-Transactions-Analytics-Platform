#!/bin/bash

# Schedules (cron expressions)
INGEST_FX_SCHEDULE=${INGEST_FX_SCHEDULE:-"*/5 * * * *"}
UPDATE_USERS_SCHEDULE=${UPDATE_USERS_SCHEDULE:-"* * * * *"}

# Capture environment variable values at startup
API_KEY="${FREECURRENCYAPI_API_KEY}"
GCS_BUCKET="${GCS_BUCKET_NAME}"
GCS_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB}"
POSTGRES_USER="${POSTGRES_USER:}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
UPDATE_PERCENTAGE="${UPDATE_PERCENTAGE:-0.01}"

# Resolve credentials path for in-process run (/app/credentials is mounted in this container)
CONTAINER_CREDS_PATH=""
if [ -n "${GCS_BUCKET}" ]; then
    if [ -n "${GCS_CREDENTIALS}" ]; then
        if echo "${GCS_CREDENTIALS}" | grep -q "^credentials/"; then
            CONTAINER_CREDS_PATH="/app/${GCS_CREDENTIALS}"
        elif [ "$(basename "${GCS_CREDENTIALS}")" = "${GCS_CREDENTIALS}" ]; then
            CONTAINER_CREDS_PATH="/app/credentials/${GCS_CREDENTIALS}"
        elif [ "${GCS_CREDENTIALS#/}" != "${GCS_CREDENTIALS}" ]; then
            CONTAINER_CREDS_PATH="${GCS_CREDENTIALS}"
        else
            CONTAINER_CREDS_PATH="/app/credentials/${GCS_CREDENTIALS}"
        fi
    else
        CONTAINER_CREDS_PATH="/app/credentials/composite-rune-478908-j1-3abb9d5ebc37.json"
    fi
fi

echo "=== DEBUG: Environment Variables ==="
echo "GCS_CREDENTIALS=${GCS_CREDENTIALS}"
echo "CONTAINER_CREDS_PATH=${CONTAINER_CREDS_PATH}"
echo ""

# Check if credentials folder exists in batch-cron container
echo "=== DEBUG: Checking credentials in batch-cron container ==="
if [ -d "/app/credentials" ]; then
    echo "✓ /app/credentials directory exists"
    echo "Contents:"
    ls -la /app/credentials/ || echo "  (cannot list)"
else
    echo "✗ /app/credentials directory does NOT exist"
fi
echo ""

# Create wrapper script that runs ingest_fx in-process (no new container per run)
# Embed environment variable values at container startup
cat > /app/run-ingest-fx.sh << EOF
#!/bin/sh
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

TIMESTAMP=\$(date -Iseconds)
echo "[\${TIMESTAMP}] Starting ingest_fx (in-process)" >> /var/log/ingest-fx.log

export FREECURRENCYAPI_API_KEY="${API_KEY}"
if [ -n "${GCS_BUCKET}" ]; then
    export GCS_BUCKET_NAME="${GCS_BUCKET}"
fi
if [ -n "${CONTAINER_CREDS_PATH}" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="${CONTAINER_CREDS_PATH}"
fi

cd /app/ingest_fx && uv run python src/get_fx_rates.py >> /var/log/ingest-fx.log 2>&1
EXIT_CODE=\$?

TIMESTAMP=\$(date -Iseconds)
echo "[\${TIMESTAMP}] ingest_fx finished with exit code: \${EXIT_CODE}" >> /var/log/ingest-fx.log
if [ \${EXIT_CODE} -ne 0 ]; then
    echo "[\${TIMESTAMP}] ERROR: ingest_fx failed with exit code \${EXIT_CODE}" >> /var/log/ingest-fx.log
fi
EOF

chmod +x /app/run-ingest-fx.sh

# Create wrapper script that runs update_users in-process
cat > /app/run-update-users.sh << EOFU
#!/bin/sh
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

TIMESTAMP=\$(date -Iseconds)
echo "[\${TIMESTAMP}] Starting update_users (in-process)" >> /var/log/update-users.log

export POSTGRES_HOST="${POSTGRES_HOST}"
export POSTGRES_PORT="${POSTGRES_PORT}"
export POSTGRES_DB="${POSTGRES_DB}"
export POSTGRES_USER="${POSTGRES_USER}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD}"
export UPDATE_PERCENTAGE="${UPDATE_PERCENTAGE}"

cd /app/update_users && uv run python src/update_user_data.py >> /var/log/update-users.log 2>&1
EXIT_CODE=\$?

TIMESTAMP=\$(date -Iseconds)
echo "[\${TIMESTAMP}] update_users finished with exit code: \${EXIT_CODE}" >> /var/log/update-users.log
if [ \${EXIT_CODE} -ne 0 ]; then
    echo "[\${TIMESTAMP}] ERROR: update_users failed with exit code \${EXIT_CODE}" >> /var/log/update-users.log
fi
EOFU

chmod +x /app/run-update-users.sh

# Test the wrapper scripts
echo "Testing wrapper scripts..."
if [ -x /app/run-ingest-fx.sh ] && [ -x /app/run-update-users.sh ]; then
    echo "Wrapper scripts are executable"
else
    echo "ERROR: Wrapper script not executable!" >> /var/log/ingest-fx.log
fi

# Ensure log files exist and are writable
touch /var/log/ingest-fx.log /var/log/update-users.log
chmod 666 /var/log/ingest-fx.log /var/log/update-users.log
echo "[$(date)] Cron service started. ingest_fx: ${INGEST_FX_SCHEDULE}, update_users: ${UPDATE_USERS_SCHEDULE}" >> /var/log/ingest-fx.log

# Generate crontab: both jobs run in-process (no new container per run)
cat > /tmp/crontab.txt << EOF
${INGEST_FX_SCHEDULE} /app/run-ingest-fx.sh >> /var/log/ingest-fx.log 2>&1
${UPDATE_USERS_SCHEDULE} /app/run-update-users.sh >> /var/log/update-users.log 2>&1
EOF

# Install the crontab
crontab /tmp/crontab.txt

# Verify crontab was installed
echo "Installed crontab:"
crontab -l

# Optional: Run a test execution immediately to verify setup
echo ""
echo "Running test execution (ingest_fx)..."
/app/run-ingest-fx.sh
echo "Running test execution (update_users)..."
/app/run-update-users.sh
echo "Test executions completed."
echo ""

# Start cron daemon in foreground
echo "Starting cron daemon"
echo "  ingest_fx:    ${INGEST_FX_SCHEDULE}"
echo "  update_users: ${UPDATE_USERS_SCHEDULE}"
echo "Current time: $(date)"
echo ""
echo "=== Logging ==="
echo "  ingest_fx:    /var/log/ingest-fx.log"
echo "  update_users: /var/log/update-users.log"
echo "  View: docker exec batch-cron cat /var/log/ingest-fx.log"
echo "       docker exec batch-cron cat /var/log/update-users.log"
echo ""

# Start cron in foreground so the container stays up
exec cron -f
