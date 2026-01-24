-- Observer-Eye Platform - TimescaleDB Initialization Script
-- Creates hypertables and optimizations for time-series observability data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create schemas for different time-series data types
CREATE SCHEMA IF NOT EXISTS metrics_ts;
CREATE SCHEMA IF NOT EXISTS events_ts;
CREATE SCHEMA IF NOT EXISTS traces_ts;
CREATE SCHEMA IF NOT EXISTS system_ts;

-- Grant permissions
GRANT USAGE ON SCHEMA metrics_ts TO observer;
GRANT USAGE ON SCHEMA events_ts TO observer;
GRANT USAGE ON SCHEMA traces_ts TO observer;
GRANT USAGE ON SCHEMA system_ts TO observer;

GRANT CREATE ON SCHEMA metrics_ts TO observer;
GRANT CREATE ON SCHEMA events_ts TO observer;
GRANT CREATE ON SCHEMA traces_ts TO observer;
GRANT CREATE ON SCHEMA system_ts TO observer;

-- Create time-series tables

-- 1. Real-time Metrics Hypertable
CREATE TABLE IF NOT EXISTS metrics_ts.real_time_metrics (
    time TIMESTAMPTZ NOT NULL,
    correlation_id UUID,
    service_name TEXT NOT NULL,
    environment TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value DOUBLE PRECISION,
    metric_type TEXT,
    labels JSONB,
    unit TEXT,
    source_host TEXT,
    ingestion_time TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable (partitioned by time)
SELECT create_hypertable(
    'metrics_ts.real_time_metrics', 
    'time',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- 2. Events Time Series
CREATE TABLE IF NOT EXISTS events_ts.real_time_events (
    time TIMESTAMPTZ NOT NULL,
    correlation_id UUID,
    service_name TEXT NOT NULL,
    environment TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data JSONB,
    severity TEXT,
    tags TEXT[],
    source_host TEXT,
    ingestion_time TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable(
    'events_ts.real_time_events', 
    'time',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- 3. Distributed Traces Time Series
CREATE TABLE IF NOT EXISTS traces_ts.real_time_traces (
    time TIMESTAMPTZ NOT NULL,
    correlation_id UUID,
    service_name TEXT NOT NULL,
    environment TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL,
    parent_span_id TEXT,
    operation_name TEXT,
    duration_microseconds BIGINT,
    tags JSONB,
    source_host TEXT,
    ingestion_time TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable(
    'traces_ts.real_time_traces', 
    'time',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- 4. System Performance Metrics
CREATE TABLE IF NOT EXISTS system_ts.system_performance (
    time TIMESTAMPTZ NOT NULL,
    host_name TEXT NOT NULL,
    cpu_usage_percent DOUBLE PRECISION,
    memory_usage_percent DOUBLE PRECISION,
    disk_usage_percent DOUBLE PRECISION,
    network_bytes_in BIGINT,
    network_bytes_out BIGINT,
    load_average_1m DOUBLE PRECISION,
    load_average_5m DOUBLE PRECISION,
    load_average_15m DOUBLE PRECISION,
    process_count INTEGER,
    thread_count INTEGER,
    ingestion_time TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable(
    'system_ts.system_performance', 
    'time',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- 5. Deep System Monitoring (eBPF data)
CREATE TABLE IF NOT EXISTS system_ts.kernel_metrics (
    time TIMESTAMPTZ NOT NULL,
    host_name TEXT NOT NULL,
    system_call_name TEXT,
    process_id INTEGER,
    thread_id INTEGER,
    cpu_id SMALLINT,
    execution_time_ns BIGINT,
    return_value BIGINT,
    kernel_module TEXT,
    additional_data JSONB,
    ingestion_time TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable(
    'system_ts.kernel_metrics', 
    'time',
    chunk_time_interval => INTERVAL '30 minutes',
    if_not_exists => TRUE
);

-- 6. Network Payload Analysis
CREATE TABLE IF NOT EXISTS system_ts.payload_analysis (
    time TIMESTAMPTZ NOT NULL,
    protocol_type TEXT,
    payload_size_bytes INTEGER,
    payload_hash_sha256 TEXT,
    source_address INET,
    destination_address INET,
    source_port INTEGER,
    destination_port INTEGER,
    inspection_results JSONB,
    threat_indicators TEXT[],
    ingestion_time TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable(
    'system_ts.payload_analysis', 
    'time',
    chunk_time_interval => INTERVAL '30 minutes',
    if_not_exists => TRUE
);

-- Create indexes for better query performance

-- Metrics indexes
CREATE INDEX IF NOT EXISTS idx_metrics_service_metric_time 
ON metrics_ts.real_time_metrics (service_name, metric_name, time DESC);

CREATE INDEX IF NOT EXISTS idx_metrics_correlation_id 
ON metrics_ts.real_time_metrics (correlation_id);

CREATE INDEX IF NOT EXISTS idx_metrics_labels_gin 
ON metrics_ts.real_time_metrics USING GIN (labels);

-- Events indexes
CREATE INDEX IF NOT EXISTS idx_events_service_type_time 
ON events_ts.real_time_events (service_name, event_type, time DESC);

CREATE INDEX IF NOT EXISTS idx_events_severity_time 
ON events_ts.real_time_events (severity, time DESC);

CREATE INDEX IF NOT EXISTS idx_events_correlation_id 
ON events_ts.real_time_events (correlation_id);

-- Traces indexes
CREATE INDEX IF NOT EXISTS idx_traces_trace_id 
ON traces_ts.real_time_traces (trace_id);

CREATE INDEX IF NOT EXISTS idx_traces_service_operation_time 
ON traces_ts.real_time_traces (service_name, operation_name, time DESC);

CREATE INDEX IF NOT EXISTS idx_traces_duration 
ON traces_ts.real_time_traces (duration_microseconds);

-- System performance indexes
CREATE INDEX IF NOT EXISTS idx_system_perf_host_time 
ON system_ts.system_performance (host_name, time DESC);

-- Kernel metrics indexes
CREATE INDEX IF NOT EXISTS idx_kernel_host_syscall_time 
ON system_ts.kernel_metrics (host_name, system_call_name, time DESC);

CREATE INDEX IF NOT EXISTS idx_kernel_process_time 
ON system_ts.kernel_metrics (process_id, time DESC);

-- Payload analysis indexes
CREATE INDEX IF NOT EXISTS idx_payload_protocol_time 
ON system_ts.payload_analysis (protocol_type, time DESC);

CREATE INDEX IF NOT EXISTS idx_payload_addresses 
ON system_ts.payload_analysis (source_address, destination_address);

-- Create continuous aggregates for common queries

-- 1. Hourly metrics aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS metrics_ts.metrics_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    service_name,
    environment,
    metric_name,
    AVG(metric_value) AS avg_value,
    MIN(metric_value) AS min_value,
    MAX(metric_value) AS max_value,
    COUNT(*) AS sample_count,
    STDDEV(metric_value) AS stddev_value
FROM metrics_ts.real_time_metrics
GROUP BY bucket, service_name, environment, metric_name
WITH NO DATA;

-- 2. Daily system performance aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS system_ts.system_performance_daily
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', time) AS bucket,
    host_name,
    AVG(cpu_usage_percent) AS avg_cpu_usage,
    MAX(cpu_usage_percent) AS max_cpu_usage,
    AVG(memory_usage_percent) AS avg_memory_usage,
    MAX(memory_usage_percent) AS max_memory_usage,
    AVG(disk_usage_percent) AS avg_disk_usage,
    MAX(disk_usage_percent) AS max_disk_usage,
    SUM(network_bytes_in) AS total_network_in,
    SUM(network_bytes_out) AS total_network_out
FROM system_ts.system_performance
GROUP BY bucket, host_name
WITH NO DATA;

-- 3. Error rate aggregation
CREATE MATERIALIZED VIEW IF NOT EXISTS events_ts.error_rates_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    service_name,
    environment,
    COUNT(*) FILTER (WHERE severity IN ('ERROR', 'CRITICAL')) AS error_count,
    COUNT(*) AS total_count,
    (COUNT(*) FILTER (WHERE severity IN ('ERROR', 'CRITICAL')) * 100.0) / COUNT(*) AS error_rate_percentage
FROM events_ts.real_time_events
GROUP BY bucket, service_name, environment
WITH NO DATA;

-- 4. Response time percentiles
CREATE MATERIALIZED VIEW IF NOT EXISTS traces_ts.response_time_percentiles_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', time) AS bucket,
    service_name,
    environment,
    operation_name,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY duration_microseconds) AS p50_duration,
    percentile_cont(0.95) WITHIN GROUP (ORDER BY duration_microseconds) AS p95_duration,
    percentile_cont(0.99) WITHIN GROUP (ORDER BY duration_microseconds) AS p99_duration,
    AVG(duration_microseconds) AS avg_duration,
    COUNT(*) AS request_count
FROM traces_ts.real_time_traces
GROUP BY bucket, service_name, environment, operation_name
WITH NO DATA;

-- Enable continuous aggregate policies for automatic refresh
SELECT add_continuous_aggregate_policy('metrics_ts.metrics_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('system_ts.system_performance_daily',
    start_offset => INTERVAL '2 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('events_ts.error_rates_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

SELECT add_continuous_aggregate_policy('traces_ts.response_time_percentiles_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- Set up data retention policies

-- Keep raw metrics for 30 days
SELECT add_retention_policy('metrics_ts.real_time_metrics', INTERVAL '30 days', if_not_exists => TRUE);

-- Keep raw events for 90 days
SELECT add_retention_policy('events_ts.real_time_events', INTERVAL '90 days', if_not_exists => TRUE);

-- Keep raw traces for 30 days
SELECT add_retention_policy('traces_ts.real_time_traces', INTERVAL '30 days', if_not_exists => TRUE);

-- Keep system performance for 180 days
SELECT add_retention_policy('system_ts.system_performance', INTERVAL '180 days', if_not_exists => TRUE);

-- Keep kernel metrics for 7 days (high volume)
SELECT add_retention_policy('system_ts.kernel_metrics', INTERVAL '7 days', if_not_exists => TRUE);

-- Keep payload analysis for 7 days (high volume)
SELECT add_retention_policy('system_ts.payload_analysis', INTERVAL '7 days', if_not_exists => TRUE);

-- Create functions for common operations

-- Function to get service health score
CREATE OR REPLACE FUNCTION get_service_health_score(
    p_service_name TEXT,
    p_environment TEXT,
    p_time_range INTERVAL DEFAULT INTERVAL '1 hour'
)
RETURNS NUMERIC AS $$
DECLARE
    error_rate NUMERIC;
    avg_response_time NUMERIC;
    health_score NUMERIC;
BEGIN
    -- Calculate error rate
    SELECT 
        COALESCE(
            (COUNT(*) FILTER (WHERE severity IN ('ERROR', 'CRITICAL')) * 100.0) / NULLIF(COUNT(*), 0),
            0
        )
    INTO error_rate
    FROM events_ts.real_time_events
    WHERE service_name = p_service_name 
        AND environment = p_environment
        AND time >= NOW() - p_time_range;
    
    -- Calculate average response time (in milliseconds)
    SELECT COALESCE(AVG(duration_microseconds) / 1000.0, 0)
    INTO avg_response_time
    FROM traces_ts.real_time_traces
    WHERE service_name = p_service_name 
        AND environment = p_environment
        AND time >= NOW() - p_time_range;
    
    -- Calculate health score (0-100)
    -- Lower error rate and response time = higher score
    health_score := 100 - (error_rate * 0.7) - (LEAST(avg_response_time / 10, 30) * 0.3);
    
    RETURN GREATEST(0, LEAST(100, health_score));
END;
$$ LANGUAGE plpgsql;

-- Function to detect anomalies in metrics
CREATE OR REPLACE FUNCTION detect_metric_anomaly(
    p_service_name TEXT,
    p_metric_name TEXT,
    p_current_value NUMERIC,
    p_lookback_hours INTEGER DEFAULT 24
)
RETURNS BOOLEAN AS $$
DECLARE
    avg_value NUMERIC;
    stddev_value NUMERIC;
    threshold_multiplier NUMERIC := 3.0; -- 3 standard deviations
BEGIN
    -- Calculate historical average and standard deviation
    SELECT 
        AVG(metric_value),
        STDDEV(metric_value)
    INTO avg_value, stddev_value
    FROM metrics_ts.real_time_metrics
    WHERE service_name = p_service_name 
        AND metric_name = p_metric_name
        AND time >= NOW() - (p_lookback_hours || ' hours')::INTERVAL;
    
    -- Return true if current value is anomalous
    IF stddev_value IS NULL OR stddev_value = 0 THEN
        RETURN FALSE;
    END IF;
    
    RETURN ABS(p_current_value - avg_value) > (threshold_multiplier * stddev_value);
END;
$$ LANGUAGE plpgsql;

-- Create triggers for real-time alerting (example)
CREATE OR REPLACE FUNCTION notify_high_error_rate()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.severity IN ('ERROR', 'CRITICAL') THEN
        -- This could trigger external alerting systems
        PERFORM pg_notify('high_error_rate', 
            json_build_object(
                'service', NEW.service_name,
                'environment', NEW.environment,
                'severity', NEW.severity,
                'time', NEW.time
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to events table
CREATE TRIGGER trigger_high_error_rate
    AFTER INSERT ON events_ts.real_time_events
    FOR EACH ROW
    EXECUTE FUNCTION notify_high_error_rate();

-- Create views for common queries

-- Service overview view
CREATE OR REPLACE VIEW metrics_ts.service_overview AS
SELECT 
    service_name,
    environment,
    COUNT(DISTINCT metric_name) as metric_count,
    MAX(time) as last_seen,
    get_service_health_score(service_name, environment) as health_score
FROM metrics_ts.real_time_metrics
WHERE time >= NOW() - INTERVAL '1 hour'
GROUP BY service_name, environment;

-- Real-time dashboard view
CREATE OR REPLACE VIEW metrics_ts.realtime_dashboard AS
SELECT 
    m.service_name,
    m.environment,
    m.metric_name,
    m.metric_value,
    m.time,
    CASE 
        WHEN detect_metric_anomaly(m.service_name, m.metric_name, m.metric_value) 
        THEN 'ANOMALY' 
        ELSE 'NORMAL' 
    END as status
FROM metrics_ts.real_time_metrics m
WHERE m.time >= NOW() - INTERVAL '5 minutes'
ORDER BY m.time DESC;

-- Notify completion
DO $$
BEGIN
    RAISE NOTICE 'Observer-Eye TimescaleDB initialization completed successfully';
    RAISE NOTICE 'Created hypertables for: metrics, events, traces, system performance, kernel metrics, payload analysis';
    RAISE NOTICE 'Created continuous aggregates for: hourly metrics, daily system performance, error rates, response time percentiles';
    RAISE NOTICE 'Configured data retention policies and real-time functions';
END $$;