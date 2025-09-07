-- PostgreSQL initialization script for Generalized Voting Platform
-- This script sets up the database with proper roles and security for multi-tenant architecture

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Create application role for the voting platform
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles
        WHERE rolname = 'voting_app_role'
    ) THEN
        CREATE ROLE voting_app_role;
    END IF;
END
$$;

-- Grant necessary permissions to application role
GRANT CONNECT ON DATABASE voting_platform TO voting_app_role;
GRANT USAGE ON SCHEMA public TO voting_app_role;
GRANT CREATE ON SCHEMA public TO voting_app_role;

-- Grant the application role to the voting user
GRANT voting_app_role TO voting_user;

-- Set up Row Level Security (RLS) functions for multi-tenant isolation
-- Function to get current user ID from session
CREATE OR REPLACE FUNCTION current_user_id() RETURNS UUID AS $$
BEGIN
    RETURN COALESCE(
        nullif(current_setting('app.current_user_id', true), ''),
        '00000000-0000-0000-0000-000000000000'
    )::UUID;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if current user is super admin
CREATE OR REPLACE FUNCTION is_super_admin() RETURNS BOOLEAN AS $$
BEGIN
    RETURN COALESCE(
        current_setting('app.is_super_admin', true)::boolean,
        false
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user can access vote (owns it or is super admin)
CREATE OR REPLACE FUNCTION can_access_vote(vote_creator_id UUID) RETURNS BOOLEAN AS $$
BEGIN
    RETURN vote_creator_id = current_user_id() OR is_super_admin();
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant execute permissions on utility functions
GRANT EXECUTE ON FUNCTION current_user_id() TO voting_app_role;
GRANT EXECUTE ON FUNCTION is_super_admin() TO voting_app_role;
GRANT EXECUTE ON FUNCTION can_access_vote(UUID) TO voting_app_role;

-- Create initial super admin user function (will be called by application startup)
CREATE OR REPLACE FUNCTION create_initial_super_admin(
    admin_email TEXT,
    admin_password_hash TEXT
) RETURNS VOID AS $$
BEGIN
    -- This will be called by the application during startup
    -- The actual table creation will be handled by Alembic migrations
    NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION create_initial_super_admin(TEXT, TEXT) TO voting_app_role;

-- Create function for setting session context (used by application)
CREATE OR REPLACE FUNCTION set_session_context(
    user_id_param UUID,
    is_super_admin_param BOOLEAN DEFAULT FALSE
) RETURNS VOID AS $$
BEGIN
    PERFORM set_config('app.current_user_id', user_id_param::text, false);
    PERFORM set_config('app.is_super_admin', is_super_admin_param::text, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

GRANT EXECUTE ON FUNCTION set_session_context(UUID, BOOLEAN) TO voting_app_role;

-- Set default transaction isolation level for consistency
ALTER DATABASE voting_platform SET default_transaction_isolation TO 'read committed';

-- Set recommended PostgreSQL settings for web applications
ALTER DATABASE voting_platform SET log_statement TO 'none';
ALTER DATABASE voting_platform SET log_duration TO off;
ALTER DATABASE voting_platform SET log_min_duration_statement TO 1000;

-- Create tenant role for Row-Level Security
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles
        WHERE rolname = 'tenant_user'
    ) THEN
        CREATE ROLE tenant_user;
    END IF;
END
$$;

-- Grant basic permissions to tenant role
GRANT CONNECT ON DATABASE voting_platform TO tenant_user;
GRANT USAGE ON SCHEMA public TO tenant_user;

-- Grant the tenant role to the application user
GRANT tenant_user TO voting_user;

-- Grant all table permissions to tenant_user (will be applied to future tables via Alembic)
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO tenant_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO tenant_user;

COMMIT;
