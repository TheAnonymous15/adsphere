-- ================================================
-- AdSphere Moderation Service Database Schema
-- SQLite initialization script
-- ================================================

-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- ================================================
-- TABLE: moderation_jobs
-- Tracks all moderation requests
-- ================================================
CREATE TABLE IF NOT EXISTS moderation_jobs (
    job_id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL CHECK(job_type IN ('text', 'image', 'video', 'realtime')),
    status TEXT NOT NULL DEFAULT 'queued' CHECK(status IN ('queued', 'processing', 'completed', 'failed')),

    -- Request metadata
    submitted_at REAL NOT NULL,
    started_at REAL,
    completed_at REAL,
    processing_time REAL,

    -- Client info
    ip_address TEXT,
    api_key_hash TEXT,
    user_agent TEXT,

    -- Content reference
    asset_id INTEGER,
    content_hash TEXT,

    -- Results
    decision TEXT CHECK(decision IN ('approve', 'review', 'block', NULL)),
    risk_level TEXT CHECK(risk_level IN ('safe', 'low', 'medium', 'high', 'critical', NULL)),
    confidence REAL,

    -- Scores (JSON)
    category_scores TEXT,  -- JSON: {"nudity": 0.05, "violence": 0.02, ...}
    flags TEXT,            -- JSON: ["keyword_match", "weapon_detected"]

    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,

    -- Worker info
    worker_id TEXT,

    -- Audit
    created_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),

    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE SET NULL
);

-- Indexes for moderation_jobs
CREATE INDEX IF NOT EXISTS idx_jobs_status ON moderation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_submitted ON moderation_jobs(submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON moderation_jobs(job_type);
CREATE INDEX IF NOT EXISTS idx_jobs_decision ON moderation_jobs(decision);
CREATE INDEX IF NOT EXISTS idx_jobs_risk ON moderation_jobs(risk_level);
CREATE INDEX IF NOT EXISTS idx_jobs_api_key ON moderation_jobs(api_key_hash);
CREATE INDEX IF NOT EXISTS idx_jobs_content_hash ON moderation_jobs(content_hash);


-- ================================================
-- TABLE: assets
-- Media files and their fingerprints
-- ================================================
CREATE TABLE IF NOT EXISTS assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset_type TEXT NOT NULL CHECK(asset_type IN ('text', 'image', 'video', 'audio')),

    -- File info
    file_path TEXT,
    file_size INTEGER,
    mime_type TEXT,
    duration REAL,  -- For video/audio

    -- Fingerprints for deduplication
    file_hash TEXT UNIQUE NOT NULL,  -- SHA256 of file
    perceptual_hash TEXT,            -- pHash for images/video frames
    scene_signature TEXT,            -- Video scene fingerprint

    -- Metadata (JSON)
    metadata TEXT,  -- {"width": 1920, "height": 1080, "fps": 30, ...}

    -- First seen
    first_seen_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),

    -- Usage tracking
    moderation_count INTEGER DEFAULT 0,
    last_moderated_at REAL,

    -- Audit
    created_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at REAL NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- Indexes for assets
CREATE INDEX IF NOT EXISTS idx_assets_file_hash ON assets(file_hash);
CREATE INDEX IF NOT EXISTS idx_assets_perceptual_hash ON assets(perceptual_hash);
CREATE INDEX IF NOT EXISTS idx_assets_type ON assets(asset_type);
CREATE INDEX IF NOT EXISTS idx_assets_first_seen ON assets(first_seen_at DESC);


-- ================================================
-- TABLE: decisions
-- Moderation decision history
-- ================================================
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    asset_id INTEGER,

    -- Decision
    decision TEXT NOT NULL CHECK(decision IN ('approve', 'review', 'block')),
    risk_level TEXT NOT NULL CHECK(risk_level IN ('safe', 'low', 'medium', 'high', 'critical')),
    confidence REAL NOT NULL,

    -- Reasoning
    primary_reason TEXT,  -- "nudity_detected", "violence", "keyword_match", etc.
    flags TEXT,           -- JSON array of all flags

    -- Scores (JSON)
    category_scores TEXT,  -- Full scores object
    detector_results TEXT, -- Individual detector outputs

    -- Policy applied
    policy_version TEXT,
    category TEXT,  -- Ad category (electronics, housing, etc.)

    -- Human review (if applicable)
    reviewed_by TEXT,
    reviewed_at REAL,
    review_decision TEXT CHECK(review_decision IN ('confirmed', 'overturned', NULL)),
    review_notes TEXT,

    -- Audit
    created_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),

    FOREIGN KEY (job_id) REFERENCES moderation_jobs(job_id) ON DELETE CASCADE,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE SET NULL
);

-- Indexes for decisions
CREATE INDEX IF NOT EXISTS idx_decisions_job ON decisions(job_id);
CREATE INDEX IF NOT EXISTS idx_decisions_asset ON decisions(asset_id);
CREATE INDEX IF NOT EXISTS idx_decisions_decision ON decisions(decision);
CREATE INDEX IF NOT EXISTS idx_decisions_risk ON decisions(risk_level);
CREATE INDEX IF NOT EXISTS idx_decisions_created ON decisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_reviewed ON decisions(reviewed_at);


-- ================================================
-- TABLE: audit_logs
-- Comprehensive audit trail
-- ================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_id TEXT UNIQUE NOT NULL,

    -- Event type
    event_type TEXT NOT NULL,  -- 'moderation', 'api_key_created', 'worker_started', etc.
    severity TEXT CHECK(severity IN ('debug', 'info', 'warning', 'error', 'critical')),

    -- Job reference
    job_id TEXT,

    -- Actor
    actor_type TEXT,  -- 'system', 'worker', 'admin', 'api_client'
    actor_id TEXT,    -- worker_id, admin_email, api_key_hash, etc.

    -- Action details (JSON)
    action TEXT NOT NULL,
    details TEXT,  -- JSON with full context

    -- Request context
    ip_address TEXT,
    user_agent TEXT,

    -- Timestamp
    timestamp REAL NOT NULL DEFAULT (strftime('%s', 'now')),

    -- Tamper detection
    prev_log_hash TEXT,
    log_hash TEXT NOT NULL,

    FOREIGN KEY (job_id) REFERENCES moderation_jobs(job_id) ON DELETE SET NULL
);

-- Indexes for audit_logs
CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_logs(severity);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON audit_logs(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_job ON audit_logs(job_id);


-- ================================================
-- TABLE: worker_stats
-- Worker performance tracking
-- ================================================
CREATE TABLE IF NOT EXISTS worker_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    worker_id TEXT NOT NULL,

    -- Status
    status TEXT NOT NULL CHECK(status IN ('active', 'idle', 'crashed', 'stopped')),

    -- Timing
    started_at REAL NOT NULL,
    last_heartbeat REAL,
    stopped_at REAL,
    uptime REAL,

    -- Performance
    jobs_processed INTEGER DEFAULT 0,
    jobs_failed INTEGER DEFAULT 0,
    avg_processing_time REAL,

    -- Resources
    cpu_percent REAL,
    memory_mb REAL,

    -- Current job
    current_job_id TEXT,
    current_job_started REAL,

    -- Metadata
    hostname TEXT,
    pid INTEGER,
    version TEXT,

    -- Audit
    created_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),

    FOREIGN KEY (current_job_id) REFERENCES moderation_jobs(job_id) ON DELETE SET NULL
);

-- Indexes for worker_stats
CREATE INDEX IF NOT EXISTS idx_worker_id ON worker_stats(worker_id);
CREATE INDEX IF NOT EXISTS idx_worker_status ON worker_stats(status);
CREATE INDEX IF NOT EXISTS idx_worker_heartbeat ON worker_stats(last_heartbeat DESC);


-- ================================================
-- TABLE: api_keys (optional - can use JSON file instead)
-- ================================================
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_hash TEXT UNIQUE NOT NULL,

    -- Owner info
    owner TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'user', 'readonly')),

    -- Permissions (JSON array)
    permissions TEXT NOT NULL,

    -- Status
    active INTEGER DEFAULT 1,

    -- Expiration
    created_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),
    expires_at REAL,
    revoked_at REAL,

    -- Usage stats
    usage_count INTEGER DEFAULT 0,
    last_used_at REAL,

    -- Rate limiting
    daily_quota INTEGER DEFAULT 10000,
    hourly_quota INTEGER DEFAULT 1000
);

-- Indexes for api_keys
CREATE INDEX IF NOT EXISTS idx_api_key_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_api_key_owner ON api_keys(owner);
CREATE INDEX IF NOT EXISTS idx_api_key_active ON api_keys(active);


-- ================================================
-- TABLE: fingerprint_cache
-- Cached video/image fingerprints
-- ================================================
CREATE TABLE IF NOT EXISTS fingerprint_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content_hash TEXT UNIQUE NOT NULL,

    -- Fingerprint data (JSON)
    fingerprint TEXT NOT NULL,

    -- Cached result (JSON)
    moderation_result TEXT,

    -- Stats
    cache_hits INTEGER DEFAULT 0,

    -- Expiration
    cached_at REAL NOT NULL DEFAULT (strftime('%s', 'now')),
    expires_at REAL,
    last_hit_at REAL
);

-- Indexes for fingerprint_cache
CREATE INDEX IF NOT EXISTS idx_fingerprint_hash ON fingerprint_cache(content_hash);
CREATE INDEX IF NOT EXISTS idx_fingerprint_expires ON fingerprint_cache(expires_at);


-- ================================================
-- TRIGGERS: Auto-update timestamps
-- ================================================

CREATE TRIGGER IF NOT EXISTS update_jobs_timestamp
AFTER UPDATE ON moderation_jobs
FOR EACH ROW
BEGIN
    UPDATE moderation_jobs SET updated_at = strftime('%s', 'now') WHERE job_id = NEW.job_id;
END;

CREATE TRIGGER IF NOT EXISTS update_assets_timestamp
AFTER UPDATE ON assets
FOR EACH ROW
BEGIN
    UPDATE assets SET updated_at = strftime('%s', 'now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_worker_stats_timestamp
AFTER UPDATE ON worker_stats
FOR EACH ROW
BEGIN
    UPDATE worker_stats SET updated_at = strftime('%s', 'now') WHERE id = NEW.id;
END;


-- ================================================
-- VIEWS: Analytics & Reporting
-- ================================================

-- Daily moderation summary
CREATE VIEW IF NOT EXISTS daily_moderation_summary AS
SELECT
    DATE(submitted_at, 'unixepoch') as date,
    job_type,
    decision,
    COUNT(*) as count,
    AVG(processing_time) as avg_time,
    AVG(confidence) as avg_confidence
FROM moderation_jobs
WHERE status = 'completed'
GROUP BY date, job_type, decision
ORDER BY date DESC;

-- Worker performance
CREATE VIEW IF NOT EXISTS worker_performance AS
SELECT
    worker_id,
    status,
    jobs_processed,
    jobs_failed,
    ROUND(100.0 * jobs_failed / NULLIF(jobs_processed, 0), 2) as failure_rate,
    avg_processing_time,
    last_heartbeat,
    ROUND((strftime('%s', 'now') - last_heartbeat), 0) as seconds_since_heartbeat
FROM worker_stats
ORDER BY last_heartbeat DESC;

-- Top violation categories
CREATE VIEW IF NOT EXISTS top_violations AS
SELECT
    json_extract(flags, '$[0]') as violation_type,
    COUNT(*) as count,
    decision
FROM decisions
WHERE flags IS NOT NULL
GROUP BY violation_type, decision
ORDER BY count DESC
LIMIT 20;


-- ================================================
-- END OF SCHEMA
-- ================================================

-- Verify tables created
SELECT 'Schema initialized successfully!' as status;
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

