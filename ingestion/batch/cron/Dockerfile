# Single image: Python + ingest_fx + update_users + cron (all batch jobs run in-process)
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install ingest_fx
COPY ingest_fx/pyproject.toml ingest_fx/uv.lock ingest_fx/.python-version ingest_fx/
RUN pip install uv && cd ingest_fx && uv sync --frozen
COPY ingest_fx/src ingest_fx/src

# Copy and install update_users
COPY update_users/pyproject.toml update_users/uv.lock update_users/.python-version update_users/
RUN cd update_users && uv sync --frozen
COPY update_users/src update_users/src

# Cron startup script
COPY cron/start-cron.sh /app/start-cron.sh
RUN sed -i 's/\r$//' /app/start-cron.sh && chmod +x /app/start-cron.sh

RUN mkdir -p /var/log && touch /var/log/ingest-fx.log /var/log/update-users.log && chmod 666 /var/log/ingest-fx.log /var/log/update-users.log

ENTRYPOINT []
CMD ["/bin/bash", "/app/start-cron.sh"]
