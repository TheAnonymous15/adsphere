<?php
/**
 * Admin Service Configuration
 * Uses SQLite database (matching system architecture)
 */

// Don't start session here - handled by index.php
// session_start();

// Paths
define('ADMIN_PATH', dirname(__DIR__));
define('APP_PATH', dirname(dirname(dirname(ADMIN_PATH))) . '/app');
define('DB_PATH', APP_PATH . '/database/adsphere.db');

// Get database connection
function getDatabase() {
    static $db = null;
    if ($db === null) {
        if (file_exists(DB_PATH)) {
            $db = new PDO('sqlite:' . DB_PATH);
            $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        }
    }
    return $db;
}

// Config values
$config = [
    'app_name' => 'AdSphere Admin',
    'session_timeout' => 3600, // 1 hour
    'max_login_attempts' => 5,
    'lockout_duration' => 900, // 15 minutes
    'require_2fa' => true,
];

