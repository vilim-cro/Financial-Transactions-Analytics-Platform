# Use official Postgres image
FROM postgres:15

# Copy initialization SQL and CSVs into container
COPY init/ /docker-entrypoint-initdb.d/
