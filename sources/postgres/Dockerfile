# Use official Postgres image
FROM postgres:15

# Set default database, user, password
ENV POSTGRES_DB=all_users
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

# Copy initialization SQL and CSVs into container
COPY init/ /docker-entrypoint-initdb.d/
