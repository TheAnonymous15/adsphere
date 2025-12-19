-- AdSphere Database Schema
-- SQLite Database for Hybrid File + Database System
-- Created: 2024-12-19

-- ============================================
-- COMPANIES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS companies (
    company_slug TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    sms TEXT,
    whatsapp TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'suspended'))
);

CREATE INDEX idx_company_status ON companies(status);
CREATE INDEX idx_company_created ON companies(created_at);

-- ============================================
-- CATEGORIES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_slug TEXT UNIQUE NOT NULL,
    category_name TEXT NOT NULL,
    description TEXT,
    created_at INTEGER NOT NULL
);

CREATE INDEX idx_category_slug ON categories(category_slug);

-- ============================================
-- COMPANY_CATEGORIES (Many-to-Many)
-- ============================================
CREATE TABLE IF NOT EXISTS company_categories (
    company_slug TEXT NOT NULL,
    category_slug TEXT NOT NULL,
    assigned_at INTEGER NOT NULL,
    PRIMARY KEY (company_slug, category_slug),
    FOREIGN KEY (company_slug) REFERENCES companies(company_slug) ON DELETE CASCADE,
    FOREIGN KEY (category_slug) REFERENCES categories(category_slug) ON DELETE CASCADE
);

CREATE INDEX idx_cc_company ON company_categories(company_slug);
CREATE INDEX idx_cc_category ON company_categories(category_slug);

-- ============================================
-- ADS TABLE (Main Ad Metadata)
-- ============================================
CREATE TABLE IF NOT EXISTS ads (
    ad_id TEXT PRIMARY KEY,
    company_slug TEXT NOT NULL,
    category_slug TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    media_filename TEXT NOT NULL,
    media_type TEXT CHECK(media_type IN ('image', 'video', 'audio')),
    media_path TEXT NOT NULL, -- Relative path to media file

    -- Contact info (denormalized for performance)
    contact_phone TEXT,
    contact_sms TEXT,
    contact_email TEXT,
    contact_whatsapp TEXT,

    -- Timestamps
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,

    -- Status
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'scheduled', 'expired')),
    scheduled_at INTEGER,
    expires_at INTEGER,

    -- Counters (cached from analytics)
    views_count INTEGER DEFAULT 0,
    likes_count INTEGER DEFAULT 0,
    dislikes_count INTEGER DEFAULT 0,
    favorites_count INTEGER DEFAULT 0,
    contacts_count INTEGER DEFAULT 0,

    FOREIGN KEY (company_slug) REFERENCES companies(company_slug) ON DELETE CASCADE,
    FOREIGN KEY (category_slug) REFERENCES categories(category_slug) ON DELETE RESTRICT
);

-- Indexes for fast queries
CREATE INDEX idx_ads_company ON ads(company_slug);
CREATE INDEX idx_ads_category ON ads(category_slug);
CREATE INDEX idx_ads_status ON ads(status);
CREATE INDEX idx_ads_created ON ads(created_at DESC);
CREATE INDEX idx_ads_views ON ads(views_count DESC);
CREATE INDEX idx_ads_likes ON ads(likes_count DESC);
CREATE INDEX idx_ads_title ON ads(title);

-- Full-text search index
CREATE VIRTUAL TABLE IF NOT EXISTS ads_fts USING fts5(
    ad_id UNINDEXED,
    title,
    description,
    content='ads',
    content_rowid='rowid'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER IF NOT EXISTS ads_fts_insert AFTER INSERT ON ads BEGIN
    INSERT INTO ads_fts(rowid, ad_id, title, description)
    VALUES (new.rowid, new.ad_id, new.title, new.description);
END;

CREATE TRIGGER IF NOT EXISTS ads_fts_update AFTER UPDATE ON ads BEGIN
    UPDATE ads_fts SET title = new.title, description = new.description
    WHERE rowid = old.rowid;
END;

CREATE TRIGGER IF NOT EXISTS ads_fts_delete AFTER DELETE ON ads BEGIN
    DELETE FROM ads_fts WHERE rowid = old.rowid;
END;

-- ============================================
-- ANALYTICS TABLES
-- ============================================

-- Page Views
CREATE TABLE IF NOT EXISTS ad_views (
    view_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_id TEXT NOT NULL,
    device_fingerprint TEXT,
    ip_address TEXT,
    user_agent TEXT,
    viewed_at INTEGER NOT NULL,
    time_on_page INTEGER DEFAULT 0, -- seconds
    FOREIGN KEY (ad_id) REFERENCES ads(ad_id) ON DELETE CASCADE
);

CREATE INDEX idx_views_ad ON ad_views(ad_id);
CREATE INDEX idx_views_date ON ad_views(viewed_at);
CREATE INDEX idx_views_device ON ad_views(device_fingerprint);

-- Likes/Dislikes
CREATE TABLE IF NOT EXISTS ad_reactions (
    reaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_id TEXT NOT NULL,
    device_fingerprint TEXT NOT NULL,
    reaction_type TEXT NOT NULL CHECK(reaction_type IN ('like', 'dislike', 'favorite')),
    created_at INTEGER NOT NULL,
    UNIQUE(ad_id, device_fingerprint, reaction_type),
    FOREIGN KEY (ad_id) REFERENCES ads(ad_id) ON DELETE CASCADE
);

CREATE INDEX idx_reactions_ad ON ad_reactions(ad_id);
CREATE INDEX idx_reactions_device ON ad_reactions(device_fingerprint);
CREATE INDEX idx_reactions_type ON ad_reactions(reaction_type);

-- Contact Methods (Call, SMS, Email, WhatsApp)
CREATE TABLE IF NOT EXISTS ad_contacts (
    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_id TEXT NOT NULL,
    contact_method TEXT NOT NULL CHECK(contact_method IN ('call', 'sms', 'email', 'whatsapp')),
    device_fingerprint TEXT,
    ip_address TEXT,
    contacted_at INTEGER NOT NULL,
    FOREIGN KEY (ad_id) REFERENCES ads(ad_id) ON DELETE CASCADE
);

CREATE INDEX idx_contacts_ad ON ad_contacts(ad_id);
CREATE INDEX idx_contacts_method ON ad_contacts(contact_method);
CREATE INDEX idx_contacts_date ON ad_contacts(contacted_at);

-- Device Tracking & Profiling
CREATE TABLE IF NOT EXISTS devices (
    device_fingerprint TEXT PRIMARY KEY,
    ip_address TEXT,
    user_agent TEXT,
    browser TEXT,
    os TEXT,
    device_type TEXT CHECK(device_type IN ('mobile', 'tablet', 'desktop')),
    first_seen INTEGER NOT NULL,
    last_seen INTEGER NOT NULL,
    total_views INTEGER DEFAULT 0,
    preferences TEXT -- JSON: favorite categories, interaction patterns
);

CREATE INDEX idx_devices_last_seen ON devices(last_seen);
CREATE INDEX idx_devices_type ON devices(device_type);

-- User Preferences (AI-driven)
CREATE TABLE IF NOT EXISTS user_preferences (
    device_fingerprint TEXT PRIMARY KEY,
    preferred_categories TEXT, -- JSON array
    liked_ads TEXT, -- JSON array of ad_ids
    disliked_ads TEXT, -- JSON array of ad_ids
    favorite_ads TEXT, -- JSON array of ad_ids
    last_updated INTEGER NOT NULL,
    FOREIGN KEY (device_fingerprint) REFERENCES devices(device_fingerprint) ON DELETE CASCADE
);

-- ============================================
-- CACHE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS cache (
    cache_key TEXT PRIMARY KEY,
    cache_value TEXT NOT NULL,
    expires_at INTEGER NOT NULL
);

CREATE INDEX idx_cache_expires ON cache(expires_at);

-- Cleanup expired cache entries
CREATE TRIGGER IF NOT EXISTS cache_cleanup AFTER INSERT ON cache BEGIN
    DELETE FROM cache WHERE expires_at < strftime('%s', 'now');
END;

-- ============================================
-- ACTIVITY LOG
-- ============================================
CREATE TABLE IF NOT EXISTS activity_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_slug TEXT,
    ad_id TEXT,
    action TEXT NOT NULL, -- 'upload', 'edit', 'delete', 'view', 'contact', etc.
    details TEXT, -- JSON
    ip_address TEXT,
    created_at INTEGER NOT NULL
);

CREATE INDEX idx_activity_company ON activity_log(company_slug);
CREATE INDEX idx_activity_ad ON activity_log(ad_id);
CREATE INDEX idx_activity_action ON activity_log(action);
CREATE INDEX idx_activity_date ON activity_log(created_at);

-- ============================================
-- STATISTICS TABLE (Pre-aggregated)
-- ============================================
CREATE TABLE IF NOT EXISTS daily_stats (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL, -- YYYY-MM-DD
    ad_id TEXT,
    company_slug TEXT,
    category_slug TEXT,

    views INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    dislikes INTEGER DEFAULT 0,
    favorites INTEGER DEFAULT 0,
    contacts_call INTEGER DEFAULT 0,
    contacts_sms INTEGER DEFAULT 0,
    contacts_email INTEGER DEFAULT 0,
    contacts_whatsapp INTEGER DEFAULT 0,

    unique_visitors INTEGER DEFAULT 0,
    avg_time_on_page INTEGER DEFAULT 0,

    created_at INTEGER NOT NULL,

    UNIQUE(date, ad_id)
);

CREATE INDEX idx_stats_date ON daily_stats(date);
CREATE INDEX idx_stats_ad ON daily_stats(ad_id);
CREATE INDEX idx_stats_company ON daily_stats(company_slug);

-- ============================================
-- VERSION TRACKING
-- ============================================
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at INTEGER NOT NULL,
    description TEXT
);

INSERT INTO schema_version (version, applied_at, description)
VALUES (1, strftime('%s', 'now'), 'Initial schema creation');

