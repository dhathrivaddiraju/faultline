-- PostgreSQL Production Schema with Range Partitioning on `events`
-- Designed for 100K+ daily events with sub-5ms write latency and no table-locking.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Projects Table
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    api_key VARCHAR(100) UNIQUE NOT NULL,
    api_secret VARCHAR(100) NOT NULL,
    platform VARCHAR(50) DEFAULT 'python',
    environment VARCHAR(50) DEFAULT 'production',
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_projects_api_key ON projects (api_key);

-- 2. Incidents Table (Clustered error groups)
CREATE TABLE IF NOT EXISTS incidents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    fingerprint VARCHAR(64) NOT NULL,
    title VARCHAR(500) NOT NULL,
    culprit VARCHAR(500),
    exception_type VARCHAR(200) NOT NULL,
    status VARCHAR(50) DEFAULT 'unresolved',
    severity VARCHAR(50) DEFAULT 'error',
    first_seen TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    events_count INTEGER DEFAULT 1,
    users_impacted INTEGER DEFAULT 1,
    ai_analysis JSONB,
    assigned_to VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_project_fingerprint UNIQUE (project_id, fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_incidents_proj_status_last_seen ON incidents (project_id, status, last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_incidents_fingerprint ON incidents (fingerprint);
CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents (severity);

-- 3. Partitioned Events Table (Range partitioned by created_at)
CREATE TABLE IF NOT EXISTS events (
    id UUID DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    incident_id UUID REFERENCES incidents(id) ON DELETE CASCADE,
    fingerprint VARCHAR(64) NOT NULL,
    exception_type VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    stack_trace JSONB NOT NULL DEFAULT '[]'::jsonb,
    environment VARCHAR(50) DEFAULT 'production',
    handled BOOLEAN DEFAULT FALSE,
    level VARCHAR(20) DEFAULT 'error',
    release VARCHAR(100),
    server_name VARCHAR(255),
    tags JSONB DEFAULT '{}'::jsonb,
    breadcrumbs JSONB DEFAULT '[]'::jsonb,
    user_context JSONB DEFAULT '{}'::jsonb,
    request_context JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Example Monthly / Daily Partitions (can be auto-provisioned by pg_partman or cron)
CREATE TABLE IF NOT EXISTS events_2026_q1 PARTITION OF events
    FOR VALUES FROM ('2026-01-01 00:00:00+00') TO ('2026-04-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS events_2026_q2 PARTITION OF events
    FOR VALUES FROM ('2026-04-01 00:00:00+00') TO ('2026-07-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS events_2026_q3 PARTITION OF events
    FOR VALUES FROM ('2026-07-01 00:00:00+00') TO ('2026-10-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS events_2026_q4 PARTITION OF events
    FOR VALUES FROM ('2026-10-01 00:00:00+00') TO ('2027-01-01 00:00:00+00');

-- BRIN index on created_at for fast time-range scanning on massive event volume
CREATE INDEX IF NOT EXISTS idx_events_created_at_brin ON events USING BRIN (created_at);
CREATE INDEX IF NOT EXISTS idx_events_proj_fingerprint ON events (project_id, fingerprint);
CREATE INDEX IF NOT EXISTS idx_events_incident_id ON events (incident_id);

-- 4. Hourly Aggregated Metrics Table
CREATE TABLE IF NOT EXISTS hourly_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL,
    incident_id UUID,
    environment VARCHAR(50) DEFAULT 'production',
    severity VARCHAR(50) DEFAULT 'error',
    bucket_time TIMESTAMPTZ NOT NULL,
    count INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_hourly_metrics_proj_bucket ON hourly_metrics (project_id, bucket_time);
