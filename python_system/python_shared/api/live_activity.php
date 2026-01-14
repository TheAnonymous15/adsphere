<?php
/********************************************
 * Live Activity Feed API
 * Real-time updates on platform activity
 ********************************************/
session_start();
header("Content-Type: application/json");

if (!isset($_SESSION['company'])) {
    http_response_code(401);
    echo json_encode(['success' => false, 'message' => 'Unauthorized']);
    exit;
}

$companySlug = $_SESSION['company'];
$analyticsBase = __DIR__ . "/../companies/analytics/";
$dataBase = __DIR__ . "/../companies/data/";

$activities = [];

// Get all company ads
$companyAds = [];
foreach (scandir($dataBase) as $category) {
    if ($category === '.' || $category === '..') continue;

    $categoryPath = "$dataBase/$category";
    if (!is_dir($categoryPath)) continue;

    $companyPath = "$categoryPath/$companySlug";
    if (!is_dir($companyPath)) continue;

    foreach (scandir($companyPath) as $adFolder) {
        if ($adFolder === '.' || $adFolder === '..') continue;

        $metaFile = "$companyPath/$adFolder/meta.json";
        if (!file_exists($metaFile)) continue;

        $meta = json_decode(file_get_contents($metaFile), true);
        if (!$meta) continue;

        // Use folder name as ad_id if not present
        $adId = $meta['ad_id'] ?? $adFolder;
        $companyAds[] = $adId;

        // Get analytics events
        $analyticsFile = "$analyticsBase/$adId.json";
        if (file_exists($analyticsFile)) {
            $analytics = json_decode(file_get_contents($analyticsFile), true);

            // Get recent events (last 50)
            if (isset($analytics['events']) && is_array($analytics['events'])) {
                $recentEvents = array_slice($analytics['events'], -50);

                foreach ($recentEvents as $event) {
                    // Only include events from last 24 hours
                    if ((time() - $event['timestamp']) < 86400) {
                        $activities[] = [
                            'ad_id' => $adId,
                            'ad_title' => $meta['title'] ?? 'Untitled',
                            'type' => $event['type'],
                            'action' => $event['action'] ?? $event['type'],
                            'timestamp' => $event['timestamp'],
                            'location' => isset($event['ip']) ? geolocateIP($event['ip']) : 'Unknown',
                            'time_ago' => timeAgo($event['timestamp'])
                        ];
                    }
                }
            }
        }
    }
}

// Sort by timestamp (most recent first)
usort($activities, function($a, $b) {
    return $b['timestamp'] - $a['timestamp'];
});

// Limit to 30 most recent
$activities = array_slice($activities, 0, 30);

echo json_encode([
    'success' => true,
    'activities' => $activities,
    'total' => count($activities),
    'generated_at' => time()
]);

function geolocateIP($ip) {
    // Simple city detection based on IP (can be enhanced with actual geolocation service)
    // For demo, return random Kenyan cities
    $cities = ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Thika'];
    return $cities[array_rand($cities)];
}

function timeAgo($timestamp) {
    $diff = time() - $timestamp;

    if ($diff < 60) return 'Just now';
    if ($diff < 3600) return floor($diff / 60) . ' mins ago';
    if ($diff < 86400) return floor($diff / 3600) . ' hours ago';
    return floor($diff / 86400) . ' days ago';
}

