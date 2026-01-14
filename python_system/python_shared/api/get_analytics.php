<?php
/********************************************
 * Get Analytics API
 * Retrieves analytics data for company ads
 ********************************************/
session_start();
header("Content-Type: application/json");

// Security check
if (!isset($_SESSION['company'])) {
    http_response_code(401);
    echo json_encode([
        'success' => false,
        'message' => 'Unauthorized access'
    ]);
    exit;
}

$companySlug = $_SESSION['company'];
$adId = $_GET['ad_id'] ?? '';

$analyticsBase = __DIR__ . "/../companies/analytics/";

// If specific ad ID requested
if (!empty($adId)) {
    $analyticsFile = "$analyticsBase/$adId.json";

    if (file_exists($analyticsFile)) {
        $analytics = json_decode(file_get_contents($analyticsFile), true);

        // Verify ad belongs to company
        $dataBase = __DIR__ . "/../companies/data/";
        $belongs = false;

        foreach (scandir($dataBase) as $category) {
            if ($category === '.' || $category === '..') continue;

            $adPath = "$dataBase/$category/$companySlug/$adId";
            if (is_dir($adPath)) {
                $belongs = true;
                break;
            }
        }

        if (!$belongs) {
            http_response_code(403);
            echo json_encode([
                'success' => false,
                'message' => 'Unauthorized access to analytics'
            ]);
            exit;
        }

        echo json_encode([
            'success' => true,
            'analytics' => $analytics
        ]);
    } else {
        echo json_encode([
            'success' => true,
            'analytics' => [
                'ad_id' => $adId,
                'total_views' => 0,
                'total_clicks' => 0,
                'total_contacts' => 0,
                'events' => []
            ]
        ]);
    }
    exit;
}

// Get all analytics for company's ads
$dataBase = __DIR__ . "/../companies/data/";
$allAnalytics = [];

foreach (scandir($dataBase) as $category) {
    if ($category === '.' || $category === '..') continue;

    $categoryPath = "$dataBase/$category";
    if (!is_dir($categoryPath)) continue;

    $companyPath = "$categoryPath/$companySlug";
    if (!is_dir($companyPath)) continue;

    foreach (scandir($companyPath) as $adFolder) {
        if ($adFolder === '.' || $adFolder === '..') continue;

        $adPath = "$companyPath/$adFolder";
        if (!is_dir($adPath)) continue;

        $analyticsFile = "$analyticsBase/$adFolder.json";

        if (file_exists($analyticsFile)) {
            $analytics = json_decode(file_get_contents($analyticsFile), true);
            $allAnalytics[$adFolder] = $analytics;
        } else {
            $allAnalytics[$adFolder] = [
                'ad_id' => $adFolder,
                'total_views' => 0,
                'total_clicks' => 0,
                'total_contacts' => 0,
                'events' => []
            ];
        }
    }
}

echo json_encode([
    'success' => true,
    'analytics' => $allAnalytics,
    'summary' => [
        'total_ads' => count($allAnalytics),
        'total_views' => array_sum(array_column($allAnalytics, 'total_views')),
        'total_clicks' => array_sum(array_column($allAnalytics, 'total_clicks')),
        'total_contacts' => array_sum(array_column($allAnalytics, 'total_contacts'))
    ]
]);

