-- ============================================================
-- MediScan Enterprise — TimescaleDB Telemetry Schema (Section 5.2)
-- High-frequency wearable & ICU vital signs time-series
-- ============================================================

-- Enable TimescaleDB extension (pre-installed in the image)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Raw telemetry ingestion table
CREATE TABLE patient_vital_telemetry (
    recorded_at             TIMESTAMPTZ      NOT NULL,
    tenant_id               UUID             NOT NULL,
    clinical_subject_id     UUID             NOT NULL,
    device_id               UUID             NOT NULL,
    loinc_code              VARCHAR(32)      NOT NULL,
    metric_value            DOUBLE PRECISION NOT NULL,
    ucum_unit               VARCHAR(32)      NOT NULL,
    signal_quality_index    REAL CHECK (signal_quality_index BETWEEN 0.0 AND 1.0),
    patient_activity_state  VARCHAR(32),
    ewma_z_score            DOUBLE PRECISION
);

-- Convert to hypertable partitioned by time (1-day chunks) and clinical_subject_id
SELECT create_hypertable(
    'patient_vital_telemetry',
    'recorded_at',
    'clinical_subject_id',
    number_partitions => 16,
    chunk_time_interval => INTERVAL '1 day'
);

COMMENT ON TABLE patient_vital_telemetry IS 'High-frequency wearable/ICU vital telemetry hypertable (1-day chunks, 16 space partitions)';

-- Automated 5-Minute Continuous Aggregate for Clinical RPM Trends
CREATE MATERIALIZED VIEW vital_telemetry_5m_rollup
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', recorded_at) AS bucket_5m,
    tenant_id,
    clinical_subject_id,
    loinc_code,
    AVG(metric_value)            AS avg_val,
    MIN(metric_value)            AS min_val,
    MAX(metric_value)            AS max_val,
    STDDEV(metric_value)         AS std_val,
    AVG(signal_quality_index)    AS avg_sqi
FROM patient_vital_telemetry
WHERE signal_quality_index >= 0.70
GROUP BY bucket_5m, tenant_id, clinical_subject_id, loinc_code;

-- Continuous aggregate refresh policy: refresh the last 1 hour every 5 minutes
SELECT add_continuous_aggregate_policy('vital_telemetry_5m_rollup',
    start_offset    => INTERVAL '1 hour',
    end_offset      => INTERVAL '5 minutes',
    schedule_interval => INTERVAL '5 minutes'
);

-- Compression policy: compress chunks older than 7 days
ALTER TABLE patient_vital_telemetry SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'tenant_id, clinical_subject_id, loinc_code',
    timescaledb.compress_orderby = 'recorded_at DESC'
);

SELECT add_compression_policy('patient_vital_telemetry', INTERVAL '7 days');

-- Retention policy: drop raw data older than 90 days (aggregates retained longer)
SELECT add_retention_policy('patient_vital_telemetry', INTERVAL '90 days');
