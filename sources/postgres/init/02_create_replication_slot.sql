-- Create replication slot for Airbyte CDC if it doesn't exist
-- This script is idempotent and can be run multiple times safely

DO $$
BEGIN
    -- Check if the replication slot already exists
    IF NOT EXISTS (
        SELECT 1 FROM pg_replication_slots WHERE slot_name = 'airbyte_slot'
    ) THEN
        -- Create the logical replication slot using pgoutput plugin
        PERFORM pg_create_logical_replication_slot('airbyte_slot', 'pgoutput');
        RAISE NOTICE 'Replication slot airbyte_slot created successfully';
    ELSE
        RAISE NOTICE 'Replication slot airbyte_slot already exists';
    END IF;
END $$;
