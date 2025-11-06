#!/bin/bash
set -e

# Initialize the database with additional schemas or extensions if needed
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_trgm";

    -- Create schemas
    CREATE SCHEMA IF NOT EXISTS public;

    GRANT ALL ON SCHEMA public TO $POSTGRES_USER;

    -- Log initialization
    SELECT 'Database initialized successfully' AS status;
EOSQL

echo "DeepAgent database initialization complete!"
