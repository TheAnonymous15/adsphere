<?php
/********************************************
 * Ad Status Statistics API
 * Returns counts of ads by status
 ********************************************/

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

require_once __DIR__ . '/../shared/database/Database.php';

$db = Database::getInstance();

try {
    // Get counts for each status
    $stats = $db->queryOne("
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN status = 'inactive' THEN 1 ELSE 0 END) as inactive,
            SUM(CASE WHEN status = 'scheduled' THEN 1 ELSE 0 END) as scheduled,
            SUM(CASE WHEN status = 'expired' THEN 1 ELSE 0 END) as expired
        FROM ads
    ");

    // Convert to integers
    $result = [
        'total' => (int)($stats['total'] ?? 0),
        'active' => (int)($stats['active'] ?? 0),
        'inactive' => (int)($stats['inactive'] ?? 0),
        'scheduled' => (int)($stats['scheduled'] ?? 0),
        'expired' => (int)($stats['expired'] ?? 0)
    ];

    // Calculate percentages
    $total = $result['total'] ?: 1;
    $result['percentages'] = [
        'active' => round(($result['active'] / $total) * 100, 1),
        'inactive' => round(($result['inactive'] / $total) * 100, 1),
        'scheduled' => round(($result['scheduled'] / $total) * 100, 1),
        'expired' => round(($result['expired'] / $total) * 100, 1)
    ];

    // Get recent status changes
    $recentChanges = $db->query("
        SELECT
            ad_id,
            status,
            updated_at
        FROM ads
        ORDER BY updated_at DESC
        LIMIT 5
    ");

    echo json_encode([
        'success' => true,
        'stats' => $result,
        'recent_changes' => $recentChanges,
        'timestamp' => time()
    ], JSON_PRETTY_PRINT);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Failed to fetch ad status statistics',
        'message' => $e->getMessage()
    ], JSON_PRETTY_PRINT);
}

