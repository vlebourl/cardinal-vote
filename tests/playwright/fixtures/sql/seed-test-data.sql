-- Playwright Test Data Seeding
-- This script populates the test database with known test data for consistent E2E testing

-- Note: This script assumes the Cardinal Vote database schema exists
-- The actual schema creation will be handled by the application's migration system

-- Create test data tracking table
CREATE TABLE IF NOT EXISTS test_data.seeded_data (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL,
    record_count INTEGER NOT NULL,
    seed_version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    seeded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    description TEXT
);

-- Create test users data (this will be inserted by the application)
-- We're just setting up the tracking for now

-- Track that we've prepared for user seeding
INSERT INTO test_data.seeded_data (table_name, record_count, description) VALUES
('users', 0, 'Prepared for user data seeding via application'),
('votes', 0, 'Prepared for vote data seeding via application'),
('vote_options', 0, 'Prepared for vote option data seeding via application'),
('vote_submissions', 0, 'Prepared for vote submission data seeding via application');

-- Create test configuration for known test users
INSERT INTO test_data.test_config (key, value, description) VALUES
-- Test admin user
('test_admin_email', 'admin.test@cardinalvote.local', 'Primary test admin user email'),
('test_admin_password', 'AdminTest123!', 'Primary test admin user password'),
('test_admin_display_name', 'Admin Test User', 'Primary test admin display name'),

-- Test regular users
('test_user1_email', 'user1.test@cardinalvote.local', 'Test user 1 email'),
('test_user1_password', 'UserTest123!', 'Test user 1 password'),
('test_user1_display_name', 'User Test 1', 'Test user 1 display name'),

('test_user2_email', 'user2.test@cardinalvote.local', 'Test user 2 email'),
('test_user2_password', 'UserTest123!', 'Test user 2 password'),
('test_user2_display_name', 'User Test 2', 'Test user 2 display name'),

-- Invalid test user (for error testing)
('test_invalid_email', 'invalid@example.com', 'Invalid test user email'),
('test_invalid_password', 'WrongPassword123!', 'Invalid test user password'),

-- Test vote configurations
('test_basic_vote_title', 'Basic Test Vote - Sprint 1', 'Basic test vote title'),
('test_basic_vote_description', 'A simple test vote for validation testing', 'Basic test vote description'),
('test_basic_vote_options', '["Option A", "Option B"]', 'Basic test vote options as JSON array'),

('test_detailed_vote_title', 'Detailed Test Vote - Sprint 2', 'Detailed test vote title'),
('test_detailed_vote_description', 'A comprehensive test vote with multiple options for Sprint 2 validation', 'Detailed test vote description'),
('test_detailed_vote_options', '["First Choice", "Second Choice", "Third Choice", "Fourth Choice"]', 'Detailed test vote options as JSON array'),

('test_complex_vote_title', 'Complex Multi-Option Vote', 'Complex test vote title'),
('test_complex_vote_description', 'Testing maximum option limits and dynamic form behavior', 'Complex test vote description'),

-- API endpoint configurations for testing
('api_base_path', '/api', 'Base API path'),
('auth_login_endpoint', '/auth/login', 'Authentication login endpoint'),
('auth_register_endpoint', '/auth/register', 'Authentication registration endpoint'),
('auth_logout_endpoint', '/auth/logout', 'Authentication logout endpoint'),
('votes_create_endpoint', '/api/votes', 'Vote creation endpoint'),
('votes_list_endpoint', '/api/votes', 'Vote listing endpoint'),

-- Performance testing configurations
('performance_page_load_threshold', '5000', 'Page load time threshold in milliseconds'),
('performance_api_response_threshold', '2000', 'API response time threshold in milliseconds'),
('performance_authentication_threshold', '3000', 'Authentication time threshold in milliseconds'),

-- Material Design validation configurations
('material_primary_color', '#1976d2', 'Material Design primary color'),
('material_secondary_color', '#dc004e', 'Material Design secondary color'),
('material_surface_color', '#ffffff', 'Material Design surface color'),
('material_background_color', '#fafafa', 'Material Design background color'),

-- Viewport configurations for responsive testing
('viewport_mobile_width', '375', 'Mobile viewport width'),
('viewport_mobile_height', '667', 'Mobile viewport height'),
('viewport_tablet_width', '768', 'Tablet viewport width'),
('viewport_tablet_height', '1024', 'Tablet viewport height'),
('viewport_desktop_width', '1200', 'Desktop viewport width'),
('viewport_desktop_height', '800', 'Desktop viewport height'),

-- Error message configurations
('error_invalid_credentials', 'Invalid email or password', 'Invalid credentials error message'),
('error_required_field', 'This field is required', 'Required field error message'),
('error_invalid_email', 'Please enter a valid email address', 'Invalid email error message'),
('error_password_too_short', 'Password must be at least 8 characters', 'Password too short error message'),

-- Feature flags for testing
('feature_registration_enabled', 'true', 'Registration feature enabled'),
('feature_email_verification_enabled', 'false', 'Email verification feature enabled'),
('feature_captcha_enabled', 'false', 'CAPTCHA feature enabled'),
('feature_analytics_enabled', 'false', 'Analytics feature enabled')

ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Create helper functions for test data
CREATE OR REPLACE FUNCTION test_data.get_test_user(user_type VARCHAR DEFAULT 'user1')
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    CASE user_type
        WHEN 'admin' THEN
            SELECT json_build_object(
                'email', get_test_config('test_admin_email'),
                'password', get_test_config('test_admin_password'),
                'displayName', get_test_config('test_admin_display_name'),
                'role', 'admin'
            ) INTO result;
        WHEN 'user2' THEN
            SELECT json_build_object(
                'email', get_test_config('test_user2_email'),
                'password', get_test_config('test_user2_password'),
                'displayName', get_test_config('test_user2_display_name'),
                'role', 'user'
            ) INTO result;
        WHEN 'invalid' THEN
            SELECT json_build_object(
                'email', get_test_config('test_invalid_email'),
                'password', get_test_config('test_invalid_password'),
                'displayName', 'Invalid User',
                'role', 'user'
            ) INTO result;
        ELSE -- default to user1
            SELECT json_build_object(
                'email', get_test_config('test_user1_email'),
                'password', get_test_config('test_user1_password'),
                'displayName', get_test_config('test_user1_display_name'),
                'role', 'user'
            ) INTO result;
    END CASE;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION test_data.get_test_vote(vote_type VARCHAR DEFAULT 'basic')
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    CASE vote_type
        WHEN 'detailed' THEN
            SELECT json_build_object(
                'title', get_test_config('test_detailed_vote_title'),
                'description', get_test_config('test_detailed_vote_description'),
                'options', get_test_config('test_detailed_vote_options')::JSON
            ) INTO result;
        WHEN 'complex' THEN
            SELECT json_build_object(
                'title', get_test_config('test_complex_vote_title'),
                'description', get_test_config('test_complex_vote_description'),
                'options', '[
                    "Option 1", "Option 2", "Option 3", "Option 4", "Option 5",
                    "Option 6", "Option 7", "Option 8", "Option 9", "Option 10",
                    "Option 11", "Option 12", "Option 13", "Option 14", "Option 15",
                    "Option 16", "Option 17", "Option 18", "Option 19", "Option 20"
                ]'::JSON
            ) INTO result;
        ELSE -- default to basic
            SELECT json_build_object(
                'title', get_test_config('test_basic_vote_title'),
                'description', get_test_config('test_basic_vote_description'),
                'options', get_test_config('test_basic_vote_options')::JSON
            ) INTO result;
    END CASE;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Mark seeding as completed
UPDATE test_data.test_config
SET value = NOW()::text, updated_at = NOW()
WHERE key = 'last_reset';

INSERT INTO test_data.test_config (key, value, description) VALUES
('seeding_completed', NOW()::text, 'Test data seeding SQL completed')
ON CONFLICT (key) DO UPDATE SET
    value = EXCLUDED.value,
    updated_at = NOW();
