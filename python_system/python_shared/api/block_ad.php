<?php
/**
 * Block Ad API Endpoint
 * Records when a user blocks an ad from appearing in their feed
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['success' => false, 'error' => 'Method not allowed']);
    exit;
}

// Get JSON input
$input = json_decode(file_get_contents('php://input'), true);

if (!$input || empty($input['ad_id'])) {
    http_response_code(400);
    echo json_encode(['success' => false, 'error' => 'Missing ad_id']);
    exit;
}

$adId = $input['ad_id'];
$reason = $input['reason'] ?? 'not_specified';
$comment = $input['comment'] ?? '';
$deviceId = $input['device_id'] ?? 'unknown';
$timestamp = $input['timestamp'] ?? time() * 1000;

// Sanitize inputs
$adId = preg_replace('/[^a-zA-Z0-9\-_]/', '', $adId);
$reason = preg_replace('/[^a-zA-Z0-9_]/', '', $reason);
$comment = substr(strip_tags($comment), 0, 500);
$deviceId = preg_replace('/[^a-zA-Z0-9\-_]/', '', $deviceId);

// Define storage paths
$basePath = dirname(__DIR__) . '/data/blocked_ads';
$dbPath = dirname(__DIR__) . '/shared/database/adsphere.db';

// Create directory if not exists
if (!is_dir($basePath)) {
    mkdir($basePath, 0755, true);
}

// Create block record
$blockRecord = [
    'ad_id' => $adId,
    'reason' => $reason,
    'comment' => $comment,
    'device_id' => $deviceId,
    'ip_address' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
    'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? 'unknown',
    'timestamp' => $timestamp,
    'created_at' => date('c')
];

// Save to file system (for quick access)
$filePath = $basePath . '/' . date('Y-m-d') . '.json';
$dailyBlocks = [];

if (file_exists($filePath)) {
    $dailyBlocks = json_decode(file_get_contents($filePath), true) ?? [];
}

$dailyBlocks[] = $blockRecord;
file_put_contents($filePath, json_encode($dailyBlocks, JSON_PRETTY_PRINT), LOCK_EX);

// Also save to SQLite database if available
try {
    if (file_exists($dbPath)) {
        $db = new PDO('sqlite:' . $dbPath);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        // Create blocked_ads table if not exists
        $db->exec("CREATE TABLE IF NOT EXISTS blocked_ads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad_id TEXT NOT NULL,
            reason TEXT,
            comment TEXT,
            device_id TEXT,
            ip_address TEXT,
            user_agent TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )");

        // Insert record
        $stmt = $db->prepare("INSERT INTO blocked_ads (ad_id, reason, comment, device_id, ip_address, user_agent) VALUES (?, ?, ?, ?, ?, ?)");
        $stmt->execute([
            $adId,
            $reason,
            $comment,
            $deviceId,
            $_SERVER['REMOTE_ADDR'] ?? '',
            $_SERVER['HTTP_USER_AGENT'] ?? ''
        ]);

        // Update ad block count
        $db->exec("UPDATE ads SET blocks_count = COALESCE(blocks_count, 0) + 1 WHERE ad_id = " . $db->quote($adId));
    }
} catch (PDOException $e) {
    error_log('Block ad database error: ' . $e->getMessage());
}

// Return success
echo json_encode([
    'success' => true,
    'message' => 'Ad blocked successfully',
    'ad_id' => $adId
]);

