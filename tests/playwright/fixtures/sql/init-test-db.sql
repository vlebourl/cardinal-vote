-- Playwright Test Database Initialization
-- This script initializes the test database with necessary extensions and configurations

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone for consistent testing
SET timezone = 'UTC';

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS test_data;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE playwright_test_db TO playwright_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO playwright_user;
GRANT ALL PRIVILEGES ON SCHEMA test_data TO playwright_user;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO playwright_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO playwright_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO playwright_user;

ALTER DEFAULT PRIVILEGES IN SCHEMA test_data GRANT ALL ON TABLES TO playwright_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA test_data GRANT ALL ON SEQUENCES TO playwright_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA test_data GRANT ALL ON FUNCTIONS TO playwright_user;

-- Create test-specific configurations
CREATE TABLE IF NOT EXISTS test_data.test_config (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) UNIQUE NOT NULL,
    value TEXT,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert test configuration
INSERT INTO test_data.test_config (key, value, description) VALUES
('test_environment', 'playwright', 'Current test environment'),
('test_run_id', '', 'Current test run identifier'),
('test_data_version', '1.0.0', 'Version of test data schema'),
('created_by', 'playwright-init', 'Created by Playwright initialization script'),
('last_reset', NOW()::text, 'Last time test data was reset')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = NOW();

-- Create function to reset test data
CREATE OR REPLACE FUNCTION test_data.reset_test_data()
RETURNS void AS $$
BEGIN
    -- This function will be used to reset test data between test runs
    UPDATE test_data.test_config
    SET value = NOW()::text, updated_at = NOW()
    WHERE key = 'last_reset';

    RAISE NOTICE 'Test data reset completed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Create function to get test configuration
CREATE OR REPLACE FUNCTION test_data.get_test_config(config_key VARCHAR)
RETURNS TEXT AS $$
BEGIN
    RETURN (SELECT value FROM test_data.test_config WHERE key = config_key);
END;
$$ LANGUAGE plpgsql;

-- Create function to set test configuration
CREATE OR REPLACE FUNCTION test_data.set_test_config(config_key VARCHAR, config_value TEXT)
RETURNS void AS $$
BEGIN
    INSERT INTO test_data.test_config (key, value, updated_at)
    VALUES (config_key, config_value, NOW())
    ON CONFLICT (key) DO UPDATE SET
        value = EXCLUDED.value,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Log initialization completion
INSERT INTO test_data.test_config (key, value, description) VALUES
('initialization_completed', NOW()::text, 'Database initialization completed')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = NOW();