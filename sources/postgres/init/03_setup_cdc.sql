-- Setup CDC for Airbyte: Create publication and set replication identities
-- This script runs after tables are created (01_init.sql) and replication slot is created (02_create_replication_slot.sql)
-- This script is idempotent and can be run multiple times safely

-- Set replica identity to PRIMARY KEY for tables (required for UPDATE/DELETE operations in CDC)
-- Since both tables have primary keys, this ensures CDC can track changes properly
ALTER TABLE users REPLICA IDENTITY DEFAULT;
ALTER TABLE merchants REPLICA IDENTITY DEFAULT;

-- Create publication for all tables (Airbyte will use this for CDC)
-- Using 'FOR ALL TABLES' to automatically include all current and future tables
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_publication WHERE pubname = 'airbyte_publication') THEN
        CREATE PUBLICATION airbyte_publication FOR ALL TABLES;
        RAISE NOTICE 'Publication airbyte_publication created successfully';
    ELSE
        RAISE NOTICE 'Publication airbyte_publication already exists';
    END IF;
END $$;

-- Grant usage on schema to replication role (if needed)
GRANT USAGE ON SCHEMA public TO postgres;

-- Grant SELECT on all tables to replication role
GRANT SELECT ON ALL TABLES IN SCHEMA public TO postgres;

ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO postgres;
