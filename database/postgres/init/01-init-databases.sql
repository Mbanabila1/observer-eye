-- Observer-Eye Platform - PostgreSQL Initialization Script
-- Creates databases, users, and basic schema for the observability platform

-- Create additional databases if they don't exist
SELECT 'CREATE DATABASE observability_test'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'observability_test')\gexec

-- Create extensions for the main database
\c observability;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Create schemas for different domains
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS apm;
CREATE SCHEMA IF NOT EXISTS metrics;
CREATE SCHEMA IF NOT EXISTS security;
CREATE SCHEMA IF NOT EXISTS audit;

-- Grant permissions
GRANT USAGE ON SCHEMA analytics TO observer;
GRANT USAGE ON SCHEMA apm TO observer;
GRANT USAGE ON SCHEMA metrics TO observer;
GRANT USAGE ON SCHEMA security TO observer;
GRANT USAGE ON SCHEMA audit TO observer;

GRANT CREATE ON SCHEMA analytics TO observer;
GRANT CREATE ON SCHEMA apm TO observer;
GRANT CREATE ON SCHEMA metrics TO observer;
GRANT CREATE ON SCHEMA security TO observer;
GRANT CREATE ON SCHEMA audit TO observer;

-- Create audit function for tracking changes
CREATE OR REPLACE FUNCTION audit.audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit.audit_log (
            table_name,
            operation,
            old_values,
            changed_by,
            changed_at
        ) VALUES (
            TG_TABLE_NAME,
            TG_OP,
            row_to_json(OLD),
            current_user,
            now()
        );
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit.audit_log (
            table_name,
            operation,
            old_values,
            new_values,
            changed_by,
            changed_at
        ) VALUES (
            TG_TABLE_NAME,
            TG_OP,
            row_to_json(OLD),
            row_to_json(NEW),
            current_user,
            now()
        );
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit.audit_log (
            table_name,
            operation,
            new_values,
            changed_by,
            changed_at
        ) VALUES (
            TG_TABLE_NAME,
            TG_OP,
            row_to_json(NEW),
            current_user,
            now()
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit.audit_log (
    id SERIAL PRIMARY KEY,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    old_values JSONB,
    new_values JSONB,
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create indexes for audit log
CREATE INDEX IF NOT EXISTS idx_audit_log_table_name ON audit.audit_log(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_log_changed_at ON audit.audit_log(changed_at);
CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit.audit_log(operation);

-- Performance optimization settings
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET track_activity_query_size = 2048;
ALTER SYSTEM SET pg_stat_statements.track = 'all';
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Create function for generating correlation IDs
CREATE OR REPLACE FUNCTION generate_correlation_id()
RETURNS UUID AS $$
BEGIN
    RETURN uuid_generate_v4();
END;
$$ LANGUAGE plpgsql;

-- Create function for microsecond precision timestamps
CREATE OR REPLACE FUNCTION microsecond_timestamp()
RETURNS TIMESTAMP(6) WITH TIME ZONE AS $$
BEGIN
    RETURN clock_timestamp();
END;
$$ LANGUAGE plpgsql;

-- Notify completion
DO $$
BEGIN
    RAISE NOTICE 'Observer-Eye PostgreSQL initialization completed successfully';
    RAISE NOTICE 'Created schemas: analytics, apm, metrics, security, audit';
    RAISE NOTICE 'Enabled extensions: uuid-ossp, pg_stat_statements, pg_trgm, btree_gin, btree_gist';
END $$;