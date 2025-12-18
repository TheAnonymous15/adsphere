<?php
/********************************************
 * Track Event API
 * Records ad views, clicks, and contacts
 ********************************************/
header("Content-Type: application/json");

// Get request data
$input = json_decode(file_get_contents('php://input'), true);
$eventType = $input['event_type'] ?? ''; // 'view', 'click', 'contact'
$adId = $input['ad_id'] ?? '';
$metadata = $input['metadata'] ?? [];

if (empty($eventType) || empty($adId)) {
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'message' => 'Missing required parameters'
    ]);
    exit;
}

$analyticsBase = __DIR__ . "/../companies/analytics/";
if (!is_dir($analyticsBase)) {
    mkdir($analyticsBase, 0775, true);
}

// Create analytics file for this ad if doesn't exist
$analyticsFile = "$analyticsBase/$adId.json";
$analytics = [];

if (file_exists($analyticsFile)) {
    $analytics = json_decode(file_get_contents($analyticsFile), true) ?? [];
}

// Initialize structure if needed
if (!isset($analytics['ad_id'])) {
    $analytics['ad_id'] = $adId;
    $analytics['total_views'] = 0;
    $analytics['total_clicks'] = 0;
    $analytics['total_contacts'] = 0;
    $analytics['events'] = [];
}

// Record event
$event = [
    'type' => $eventType,
    'timestamp' => time(),
    'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
    'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? 'unknown',
    'metadata' => $metadata
];

$analytics['events'][] = $event;

// Update counters
switch ($eventType) {
    case 'view':
        $analytics['total_views']++;
        break;
    case 'click':
        $analytics['total_clicks']++;
        break;
    case 'contact':
        $analytics['total_contacts']++;
        $analytics['last_contact'] = time();
        break;
}

$analytics['updated_at'] = time();

// Save analytics
file_put_contents($analyticsFile, json_encode($analytics, JSON_PRETTY_PRINT));

echo json_encode([
    'success' => true,
    'message' => 'Event tracked successfully',
    'event_type' => $eventType,
    'ad_id' => $adId
]);

