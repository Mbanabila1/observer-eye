-- Observer-Eye Platform - ClickHouse Warehouse Initialization
-- Creates the data warehouse schema for BI analytics and observability data

-- Create the main warehouse database
CREATE DATABASE IF NOT EXISTS warehouse;

-- Use the warehouse database
USE warehouse;

-- Create tables for the Four Pillars of Observability

-- 1. Metrics Table (Optimized for time-series data)
CREATE TABLE IF NOT EXISTS metrics (
    timestamp DateTime64(6) CODEC(Delta, LZ4),
    correlation_id UUID,
    service_name LowCardinality(String),
    environment LowCardinality(String),
    metric_name LowCardinality(String),
    metric_value Float64 CODEC(Gorilla, LZ4),
    metric_type LowCardinality(String),
    labels Map(String, String),
    unit LowCardinality(String),
    source_host LowCardinality(String),
    ingestion_time DateTime64(6) DEFAULT now64(6)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (service_name, metric_name, timestamp)
TTL timestamp + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- 2. Events Table (For discrete events and alerts)
CREATE TABLE IF NOT EXISTS events (
    timestamp DateTime64(6) CODEC(Delta, LZ4),
    correlation_id UUID,
    service_name LowCardinality(String),
    environment LowCardinality(String),
    event_type LowCardinality(String),
    event_data String CODEC(ZSTD),
    severity LowCardinality(String),
    tags Array(String),
    source_host LowCardinality(String),
    ingestion_time DateTime64(6) DEFAULT now64(6)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (service_name, event_type, timestamp)
TTL timestamp + INTERVAL 90 DAY
SETTINGS index_granularity = 8192;

-- 3. Logs Table (For structured and unstructured log data)
CREATE TABLE IF NOT EXISTS logs (
    timestamp DateTime64(6) CODEC(Delta, LZ4),
    correlation_id UUID,
    service_name LowCardinality(String),
    environment LowCardinality(String),
    log_level LowCardinality(String),
    message String CODEC(ZSTD),
    structured_data String CODEC(ZSTD),
    source_file String,
    line_number UInt32,
    source_host LowCardinality(String),
    ingestion_time DateTime64(6) DEFAULT now64(6)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (service_name, log_level, timestamp)
TTL timestamp + INTERVAL 30 DAY
SETTINGS index_granularity = 8192;

-- 4. Traces Table (For distributed tracing data)
CREATE TABLE IF NOT EXISTS traces (
    timestamp DateTime64(6) CODEC(Delta, LZ4),
    correlation_id UUID,
    service_name LowCardinality(String),
    environment LowCardinality(String),
    trace_id String,
    span_id String,
    parent_span_id String,
    operation_name LowCardinality(String),
    duration_microseconds UInt64 CODEC(Gorilla, LZ4),
    tags Map(String, String),
    source_host LowCardinality(String),
    ingestion_time DateTime64(6) DEFAULT now64(6)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (service_name, trace_id, timestamp)
TTL timestamp + INTERVAL 30 DAY
SETTINGS index_granularity = 8192;

-- Deep System Monitoring Tables

-- 5. Kernel Metrics Table (For eBPF and system-level data)
CREATE TABLE IF NOT EXISTS kernel_metrics (
    timestamp DateTime64(6) CODEC(Delta, LZ4),
    correlation_id UUID,
    host_name LowCardinality(String),
    system_call_name LowCardinality(String),
    process_id UInt32,
    thread_id UInt32,
    cpu_id UInt16,
    execution_time_ns UInt64 CODEC(Gorilla, LZ4),
    return_value Int64,
    kernel_module LowCardinality(String),
    additional_data String CODEC(ZSTD),
    ingestion_time DateTime64(6) DEFAULT now64(6)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (host_name, system_call_name, timestamp)
TTL timestamp + INTERVAL 7 DAY
SETTINGS index_granularity = 8192;

-- 6. Payload Inspection Table (For network payload analysis)
CREATE TABLE IF NOT EXISTS payload_inspection (
    timestamp DateTime64(6) CODEC(Delta, LZ4),
    correlation_id UUID,
    protocol_type LowCardinality(String),
    payload_size_bytes UInt32,
    payload_hash_sha256 String,
    source_address IPv6,
    destination_address IPv6,
    source_port UInt16,
    destination_port UInt16,
    inspection_results String CODEC(ZSTD),
    threat_indicators Array(String),
    ingestion_time DateTime64(6) DEFAULT now64(6)
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(timestamp)
ORDER BY (protocol_type, source_address, timestamp)
TTL timestamp + INTERVAL 7 DAY
SETTINGS index_granularity = 8192;

-- BI Analytics Tables (Star Schema for Business Intelligence)

-- 7. BI Fact Table (Pre-aggregated metrics for fast reporting)
CREATE TABLE IF NOT EXISTS bi_observability_facts (
    date_key UInt32,
    time_key UInt32,
    service_key UInt32,
    environment_key UInt16,
    metric_value Decimal64(6),
    event_count UInt64,
    error_count UInt64,
    response_time_ms Decimal64(3),
    throughput_per_second Decimal64(3),
    availability_percentage Decimal64(3),
    cpu_utilization_avg Decimal64(2),
    memory_utilization_avg Decimal64(2),
    ingestion_time DateTime64(6) DEFAULT now64(6)
) ENGINE = MergeTree()
PARTITION BY date_key
ORDER BY (date_key, service_key, environment_key)
TTL toDate(date_key) + INTERVAL 365 DAY
SETTINGS index_granularity = 8192;

-- 8. Service Dimension Table
CREATE TABLE IF NOT EXISTS bi_dim_service (
    service_key UInt32,
    service_name String,
    service_type LowCardinality(String),
    team_owner LowCardinality(String),
    technology_stack LowCardinality(String),
    criticality_level LowCardinality(String),
    created_at DateTime64(6) DEFAULT now64(6),
    updated_at DateTime64(6) DEFAULT now64(6)
) ENGINE = MergeTree()
ORDER BY service_key
SETTINGS index_granularity = 8192;

-- 9. Date Dimension Table
CREATE TABLE IF NOT EXISTS bi_dim_date (
    date_key UInt32,
    full_date Date,
    year UInt16,
    quarter UInt8,
    month UInt8,
    week UInt8,
    day_of_year UInt16,
    day_of_month UInt8,
    day_of_week UInt8,
    is_weekend UInt8,
    is_holiday UInt8
) ENGINE = MergeTree()
ORDER BY date_key
SETTINGS index_granularity = 8192;

-- 10. Time Dimension Table
CREATE TABLE IF NOT EXISTS bi_dim_time (
    time_key UInt32,
    hour UInt8,
    minute UInt8,
    second UInt8,
    time_of_day_bucket LowCardinality(String),
    business_hours UInt8
) ENGINE = MergeTree()
ORDER BY time_key
SETTINGS index_granularity = 8192;

-- 11. Environment Dimension Table
CREATE TABLE IF NOT EXISTS bi_dim_environment (
    environment_key UInt16,
    environment_name LowCardinality(String),
    environment_type LowCardinality(String),
    region LowCardinality(String),
    cloud_provider LowCardinality(String)
) ENGINE = MergeTree()
ORDER BY environment_key
SETTINGS index_granularity = 8192;

-- Create Materialized Views for Real-time Aggregations

-- Real-time metrics aggregation by service and hour
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_metrics_hourly
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour_timestamp)
ORDER BY (service_name, environment, metric_name, hour_timestamp)
AS SELECT
    service_name,
    environment,
    metric_name,
    toStartOfHour(timestamp) as hour_timestamp,
    avg(metric_value) as avg_value,
    min(metric_value) as min_value,
    max(metric_value) as max_value,
    count() as sample_count
FROM metrics
GROUP BY service_name, environment, metric_name, hour_timestamp;

-- Real-time error rate calculation
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_error_rates
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(minute_timestamp)
ORDER BY (service_name, environment, minute_timestamp)
AS SELECT
    service_name,
    environment,
    toStartOfMinute(timestamp) as minute_timestamp,
    countIf(severity IN ('ERROR', 'CRITICAL')) as error_count,
    count() as total_count,
    (error_count * 100.0) / total_count as error_rate_percentage
FROM events
GROUP BY service_name, environment, minute_timestamp;

-- Create indexes for better query performance
-- Full-text search index for logs
ALTER TABLE logs ADD INDEX idx_message_fulltext message TYPE tokenbf_v1(32768, 3, 0) GRANULARITY 1;

-- Bloom filter indexes for high-cardinality fields
ALTER TABLE traces ADD INDEX idx_trace_id_bloom trace_id TYPE bloom_filter() GRANULARITY 1;
ALTER TABLE payload_inspection ADD INDEX idx_payload_hash_bloom payload_hash_sha256 TYPE bloom_filter() GRANULARITY 1;

-- Create functions for common calculations

-- Function to calculate percentiles
CREATE OR REPLACE FUNCTION calculate_percentile(values Array(Float64), percentile Float64)
RETURNS Float64
AS 'quantile(percentile)(values)';

-- Function to detect anomalies using statistical methods
CREATE OR REPLACE FUNCTION detect_anomaly(current_value Float64, historical_values Array(Float64), threshold Float64)
RETURNS UInt8
AS 'if(abs(current_value - avg(historical_values)) > threshold * stddevPop(historical_values), 1, 0)';

-- Insert sample dimension data

-- Sample environments
INSERT INTO bi_dim_environment VALUES
(1, 'production', 'prod', 'us-west-2', 'aws'),
(2, 'staging', 'staging', 'us-west-2', 'aws'),
(3, 'development', 'dev', 'local', 'local'),
(4, 'testing', 'test', 'us-east-1', 'aws');

-- Sample time dimension (populate for 24 hours)
INSERT INTO bi_dim_time
SELECT
    hour * 3600 + minute * 60 + second as time_key,
    hour,
    minute,
    second,
    CASE
        WHEN hour BETWEEN 6 AND 11 THEN 'morning'
        WHEN hour BETWEEN 12 AND 17 THEN 'afternoon'
        WHEN hour BETWEEN 18 AND 21 THEN 'evening'
        ELSE 'night'
    END as time_of_day_bucket,
    CASE WHEN hour BETWEEN 9 AND 17 THEN 1 ELSE 0 END as business_hours
FROM (
    SELECT number % 24 as hour
    FROM numbers(24)
) h
CROSS JOIN (
    SELECT number as minute
    FROM numbers(60)
) m
CROSS JOIN (
    SELECT number as second
    FROM numbers(60)
) s;

-- Sample date dimension (populate for 2 years)
INSERT INTO bi_dim_date
SELECT
    toUInt32(formatDateTime(date_value, '%Y%m%d')) as date_key,
    date_value as full_date,
    toYear(date_value) as year,
    toQuarter(date_value) as quarter,
    toMonth(date_value) as month,
    toWeek(date_value) as week,
    toDayOfYear(date_value) as day_of_year,
    toDayOfMonth(date_value) as day_of_month,
    toDayOfWeek(date_value) as day_of_week,
    CASE WHEN toDayOfWeek(date_value) IN (6, 7) THEN 1 ELSE 0 END as is_weekend,
    0 as is_holiday  -- Can be updated with actual holiday data
FROM (
    SELECT today() - number as date_value
    FROM numbers(730)  -- 2 years of data
);

-- Create system for automatic data retention and cleanup
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS String
AS $$
BEGIN
    -- This function can be called periodically to clean up old data
    -- Implementation would go here for production use
    RETURN 'Cleanup completed';
END;
$$;