<?php
/********************************************
 * Database Migration - Moderation Tables
 * Creates tables for storing scan results
 ********************************************/

require_once __DIR__ . '/../database/Database.php';

$db = Database::getInstance();

echo "Creating moderation tables...\n";

try {
    // 1. Moderation Violations Table
    $db->execute("
        CREATE TABLE IF NOT EXISTS moderation_violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_id TEXT NOT NULL,
            company_slug TEXT NOT NULL,
            severity INTEGER NOT NULL,
            ai_score INTEGER NOT NULL,
            violations TEXT NOT NULL,
            action_taken TEXT,
            created_at INTEGER NOT NULL,
            resolved_at INTEGER,
            resolved_by TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (ad_id) REFERENCES ads(ad_id),
            FOREIGN KEY (company_slug) REFERENCES companies(company_slug)
        )
    ");
    echo "✓ Created moderation_violations table\n";

    // 2. Moderation Actions Table
    $db->execute("
        CREATE TABLE IF NOT EXISTS moderation_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            violation_id INTEGER NOT NULL,
            ad_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            admin_user TEXT,
            reason TEXT,
            created_at INTEGER NOT NULL,
            FOREIGN KEY (violation_id) REFERENCES moderation_violations(id)
        )
    ");
    echo "✓ Created moderation_actions table\n";

    // 3. Scan History Table
    $db->execute("
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_type TEXT NOT NULL,
            total_scanned INTEGER NOT NULL,
            flagged_count INTEGER NOT NULL,
            clean_count INTEGER NOT NULL,
            critical_count INTEGER DEFAULT 0,
            high_count INTEGER DEFAULT 0,
            medium_count INTEGER DEFAULT 0,
            low_count INTEGER DEFAULT 0,
            processing_time REAL,
            created_at INTEGER NOT NULL
        )
    ");
    echo "✓ Created scan_history table\n";

    // 4. Create indexes for performance
    $db->execute("CREATE INDEX IF NOT EXISTS idx_violations_status ON moderation_violations(status)");
    $db->execute("CREATE INDEX IF NOT EXISTS idx_violations_company ON moderation_violations(company_slug)");
    $db->execute("CREATE INDEX IF NOT EXISTS idx_violations_created ON moderation_violations(created_at)");
    echo "✓ Created indexes\n";

    echo "\n✅ All moderation tables created successfully!\n";

} catch (Exception $e) {
    echo "\n❌ Error: " . $e->getMessage() . "\n";
    exit(1);
}

