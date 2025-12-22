<?php
/********************************************
 * Track User Interactions API
 * Handles likes, dislikes, and time spent
 ********************************************/
header("Content-Type: application/json");

// Get request data
$input = json_decode(file_get_contents('php://input'), true);
$interactionType = $input['interaction_type'] ?? ''; // 'like', 'dislike', 'time_spent'
$adId = $input['ad_id'] ?? '';
$value = $input['value'] ?? null; // For time_spent, this is seconds

if (empty($interactionType) || empty($adId)) {
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

// Load or create analytics file
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
    $analytics['total_likes'] = 0;
    $analytics['total_dislikes'] = 0;
    $analytics['total_favorites'] = 0;
    $analytics['total_unfavorites'] = 0;
    $analytics['current_favorites'] = 0;
    $analytics['total_time_spent'] = 0; // in seconds
    $analytics['avg_time_spent'] = 0;
    $analytics['events'] = [];
}

// Create event
$event = [
    'type' => $interactionType,
    'timestamp' => time(),
    'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
    'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? 'unknown'
];

// Handle different interaction types
switch ($interactionType) {
    case 'like':
        $analytics['total_likes']++;
        $event['action'] = 'liked';
        break;

    case 'dislike':
        $analytics['total_dislikes']++;
        $event['action'] = 'not_interested';
        break;

    case 'favorite':
        $analytics['total_favorites']++;
        $analytics['current_favorites']++;
        $event['action'] = 'favorited';
        break;

    case 'unfavorite':
        $analytics['total_unfavorites']++;
        $analytics['current_favorites'] = max(0, $analytics['current_favorites'] - 1);
        $event['action'] = 'unfavorited';
        break;

    case 'time_spent':
        if (is_numeric($value) && $value > 0) {
            $analytics['total_time_spent'] += $value;
            $event['duration'] = $value;

            // Calculate average time spent
            $timeEvents = array_filter($analytics['events'], function($e) {
                return $e['type'] === 'time_spent';
            });
            $totalEvents = count($timeEvents) + 1; // +1 for current event
            $analytics['avg_time_spent'] = round($analytics['total_time_spent'] / $totalEvents, 2);
        }
        break;
}

$analytics['events'][] = $event;
$analytics['updated_at'] = time();

// Save analytics
file_put_contents($analyticsFile, json_encode($analytics, JSON_PRETTY_PRINT));

echo json_encode([
    'success' => true,
    'message' => 'Interaction tracked successfully',
    'interaction_type' => $interactionType,
    'ad_id' => $adId,
    'stats' => [
        'likes' => $analytics['total_likes'],
        'dislikes' => $analytics['total_dislikes'],
        'favorites' => $analytics['total_favorites'],
        'current_favorites' => $analytics['current_favorites'],
        'avg_time_spent' => $analytics['avg_time_spent']
    ]
]);

