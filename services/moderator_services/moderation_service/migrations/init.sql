-- AdSphere Moderation Service - Database Schema
-- SQLite3 initialization script
-- Version: 1.0.0
-- Date: December 21, 2025

-- ===========================================
-- Moderation Jobs Table
-- Tracks all moderation requests and their status
-- ===========================================
CREATE TABLE IF NOT EXISTS moderation_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,
    job_type TEXT NOT NULL DEFAULT 'text',  -- text, image, video, realtime
    status TEXT NOT NULL DEFAULT 'pending',  -- pending, processing, completed, failed, cancelled
    priority INTEGER DEFAULT 0,  -- Higher = more priority

    -- Request data
    title TEXT,
    description TEXT,
    category TEXT DEFAULT 'general',

    -- User context
    user_id TEXT,
    company_slug TEXT,
    ad_id TEXT,
    ip_address TEXT,
    source TEXT DEFAULT 'api',

    -- Processing metadata
    processing_time_ms REAL DEFAULT 0,
    worker_id TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Error tracking
    error_message TEXT,
    error_stack TEXT
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_jobs_status ON moderation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON moderation_jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON moderation_jobs(company_slug);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON moderation_jobs(created_at);

-- ===========================================
-- Assets Table
-- Stores media references and fingerprints
-- ===========================================
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    asset_type TEXT NOT NULL,  -- image, video, audio

    -- File info
    file_path TEXT,
    file_url TEXT,
    file_size INTEGER,
    file_hash TEXT,  -- SHA-256 hash

    -- Perceptual hashes for deduplication
    phash TEXT,      -- Perceptual hash (images)
    dhash TEXT,      -- Difference hash (images)

    -- Processing status
    status TEXT DEFAULT 'pending',

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,

    FOREIGN KEY (job_id) REFERENCES moderation_jobs(job_id)
);

CREATE INDEX IF NOT EXISTS idx_assets_job ON assets(job_id);
CREATE INDEX IF NOT EXISTS idx_assets_hash ON assets(file_hash);
CREATE INDEX IF NOT EXISTS idx_assets_phash ON assets(phash);

-- ===========================================
-- Moderation Decisions Table
-- Stores all moderation outcomes
-- ===========================================
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT UNIQUE NOT NULL,
    job_id TEXT,

    -- Decision outcome
    decision TEXT NOT NULL,  -- approve, review, block
    risk_level TEXT NOT NULL,  -- low, medium, high, critical
    global_score REAL,  -- 0.0 to 1.0 safety score

    -- Category scores (JSON)
    category_scores TEXT,  -- JSON object with all scores

    -- Flags and reasons
    flags TEXT,  -- JSON array of flags
    reasons TEXT,  -- JSON array of human-readable reasons

    -- AI model results
    ai_sources TEXT,  -- JSON object with model results

    -- Fingerprint
    content_fingerprint TEXT,

    -- User context
    user_id TEXT,
    company_slug TEXT,
    ad_id TEXT,

    -- Metadata
    content_type TEXT DEFAULT 'text',
    processing_time_ms REAL,

    -- Review tracking (for manual review decisions)
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    review_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (job_id) REFERENCES moderation_jobs(job_id)
);

CREATE INDEX IF NOT EXISTS idx_decisions_audit ON decisions(audit_id);
CREATE INDEX IF NOT EXISTS idx_decisions_decision ON decisions(decision);
CREATE INDEX IF NOT EXISTS idx_decisions_company ON decisions(company_slug);
CREATE INDEX IF NOT EXISTS idx_decisions_ad ON decisions(ad_id);
CREATE INDEX IF NOT EXISTS idx_decisions_created ON decisions(created_at);

-- ===========================================
-- Audit Logs Table
-- Immutable audit trail for compliance
-- ===========================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT NOT NULL,
    event_type TEXT NOT NULL,  -- moderation, review, action, error

    -- Event data (JSON)
    event_data TEXT,

    -- Actor
    actor_type TEXT,  -- system, user, admin
    actor_id TEXT,

    -- Request context
    ip_address TEXT,
    user_agent TEXT,

    -- Immutable timestamp
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Tamper detection
    checksum TEXT  -- SHA-256 of previous row + event_data
);

CREATE INDEX IF NOT EXISTS idx_audit_audit_id ON audit_logs(audit_id);
CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);

-- ===========================================
-- Rate Limit Table
-- Tracks API usage for rate limiting
-- ===========================================
CREATE TABLE IF NOT EXISTS rate_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,  -- user_id, ip, api_key
    key_type TEXT NOT NULL,  -- user, ip, api_key

    -- Counters
    minute_count INTEGER DEFAULT 0,
    minute_window INTEGER,  -- Unix timestamp / 60
    hour_count INTEGER DEFAULT 0,
    hour_window INTEGER,  -- Unix timestamp / 3600
    day_count INTEGER DEFAULT 0,
    day_window INTEGER,  -- Unix timestamp / 86400

    -- Timestamps
    first_request TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_request TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(key, key_type)
);

CREATE INDEX IF NOT EXISTS idx_rate_key ON rate_limits(key, key_type);

-- ===========================================
-- Content Cache Table
-- Caches moderation results for identical content
-- ===========================================
CREATE TABLE IF NOT EXISTS content_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT UNIQUE NOT NULL,  -- SHA-256 of content

    -- Cached result
    decision TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    category_scores TEXT,  -- JSON

    -- Hit statistics
    hit_count INTEGER DEFAULT 0,
    last_hit TIMESTAMP,

    -- TTL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_cache_hash ON content_cache(content_hash);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON content_cache(expires_at);

-- ===========================================
-- API Keys Table
-- For external API authentication
-- ===========================================
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash TEXT UNIQUE NOT NULL,  -- SHA-256 of API key
    key_prefix TEXT NOT NULL,  -- First 8 chars for identification

    -- Owner
    owner_type TEXT NOT NULL,  -- company, admin, service
    owner_id TEXT NOT NULL,

    -- Permissions
    permissions TEXT DEFAULT '["read", "write"]',  -- JSON array

    -- Rate limits
    rate_limit_minute INTEGER DEFAULT 60,
    rate_limit_hour INTEGER DEFAULT 1000,

    -- Status
    is_active INTEGER DEFAULT 1,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    expires_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_owner ON api_keys(owner_type, owner_id);

-- ===========================================
-- Blocked Content Patterns Table
-- Quick lookup for known bad content
-- ===========================================
CREATE TABLE IF NOT EXISTS blocked_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL,  -- text_hash, image_phash, keyword
    pattern_value TEXT NOT NULL,

    -- Classification
    category TEXT NOT NULL,  -- violence, nsfw, spam, etc.
    severity TEXT NOT NULL,  -- low, medium, high, critical

    -- Metadata
    description TEXT,
    added_by TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(pattern_type, pattern_value)
);

CREATE INDEX IF NOT EXISTS idx_blocked_type ON blocked_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_blocked_value ON blocked_patterns(pattern_value);

-- ===========================================
-- Statistics Table
-- Aggregated stats for monitoring
-- ===========================================
CREATE TABLE IF NOT EXISTS statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_date DATE NOT NULL,
    stat_hour INTEGER,  -- 0-23, NULL for daily aggregates

    -- Counts
    total_requests INTEGER DEFAULT 0,
    approved_count INTEGER DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    blocked_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,

    -- By content type
    text_count INTEGER DEFAULT 0,
    image_count INTEGER DEFAULT 0,
    video_count INTEGER DEFAULT 0,

    -- Performance
    avg_processing_ms REAL DEFAULT 0,
    max_processing_ms REAL DEFAULT 0,
    p95_processing_ms REAL DEFAULT 0,

    -- Unique key
    UNIQUE(stat_date, stat_hour)
);

CREATE INDEX IF NOT EXISTS idx_stats_date ON statistics(stat_date);

-- ===========================================
-- Initial Data
-- ===========================================

-- Insert default blocked keywords
INSERT OR IGNORE INTO blocked_patterns (pattern_type, pattern_value, category, severity, description)
VALUES
    ('keyword', 'csam', 'csam', 'critical', 'Child exploitation content'),
    ('keyword', 'child porn', 'csam', 'critical', 'Child exploitation content'),
    ('keyword', 'suicide bomber', 'terrorism', 'critical', 'Terrorism content'),
    ('keyword', 'join isis', 'terrorism', 'critical', 'Terrorism recruitment');

-- Create initial statistics row for today
INSERT OR IGNORE INTO statistics (stat_date, stat_hour)
VALUES (DATE('now'), NULL);

-- ===========================================
-- Views for common queries
-- ===========================================

-- Recent decisions view
CREATE VIEW IF NOT EXISTS v_recent_decisions AS
SELECT
    d.audit_id,
    d.decision,
    d.risk_level,
    d.global_score,
    d.company_slug,
    d.ad_id,
    d.content_type,
    d.processing_time_ms,
    d.created_at
FROM decisions d
ORDER BY d.created_at DESC
LIMIT 1000;

-- Company moderation stats view
CREATE VIEW IF NOT EXISTS v_company_stats AS
SELECT
    company_slug,
    COUNT(*) as total_moderations,
    SUM(CASE WHEN decision = 'approve' THEN 1 ELSE 0 END) as approved,
    SUM(CASE WHEN decision = 'review' THEN 1 ELSE 0 END) as reviewed,
    SUM(CASE WHEN decision = 'block' THEN 1 ELSE 0 END) as blocked,
    AVG(global_score) as avg_score,
    AVG(processing_time_ms) as avg_processing_time
FROM decisions
WHERE company_slug IS NOT NULL
GROUP BY company_slug;

-- Daily statistics view
CREATE VIEW IF NOT EXISTS v_daily_stats AS
SELECT
    DATE(created_at) as date,
    COUNT(*) as total,
    SUM(CASE WHEN decision = 'approve' THEN 1 ELSE 0 END) as approved,
    SUM(CASE WHEN decision = 'review' THEN 1 ELSE 0 END) as reviewed,
    SUM(CASE WHEN decision = 'block' THEN 1 ELSE 0 END) as blocked,
    AVG(processing_time_ms) as avg_time_ms
FROM decisions
GROUP BY DATE(created_at)
ORDER BY date DESC;

