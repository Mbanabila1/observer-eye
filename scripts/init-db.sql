-- Observer Eye Platform Database Initialization Script

-- Create additional databases if needed
-- CREATE DATABASE observer_eye_test;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create indexes for performance (will be created by Django migrations)
-- These are just examples of what Django will create

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE observer_eye TO observer_user;

-- Set timezone
SET timezone = 'UTC';