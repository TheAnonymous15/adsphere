<?php
/********************************************
 * Advanced Dashboard Statistics API
 * Comprehensive analytics and insights
 ********************************************/
session_start();
header("Content-Type: application/json");

if (!isset($_SESSION['company'])) {
    http_response_code(401);
    echo json_encode(['success' => false, 'message' => 'Unauthorized']);
    exit;
}

$companySlug = $_SESSION['company'];
$dataBase = __DIR__ . "/../companies/data/";
$analyticsBase = __DIR__ . "/../companies/analytics/";

// Initialize stats
$stats = [
    'overview' => [
        'total_ads' => 0,
        'active_ads' => 0,
        'paused_ads' => 0,
        'scheduled_ads' => 0,
        'expired_ads' => 0
    ],
    'performance' => [
        'total_views' => 0,
        'total_contacts' => 0,
        'total_clicks' => 0,
        'total_likes' => 0,
        'total_dislikes' => 0,
        'total_favorites' => 0,
        'current_favorites' => 0,
        'conversion_rate' => 0,
        'favorite_rate' => 0,
        'avg_views_per_ad' => 0
    ],
    'trends' => [
        'views_trend' => [],
        'contacts_trend' => [],
        'daily_stats' => []
    ],
    'top_performers' => [],
    'categories' => [],
    'recent_activity' => [],
    'revenue_estimate' => [
        'total_value' => 0,
        'projected_monthly' => 0
    ],
    'comparison' => [
        'vs_last_week' => [
            'views' => 0,
            'contacts' => 0,
            'ads' => 0
        ]
    ],
    'ai_insights' => []
];

// Collect all company ads
$allAds = [];
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

        $metaFile = "$adPath/meta.json";
        if (!file_exists($metaFile)) continue;

        $meta = json_decode(file_get_contents($metaFile), true);
        if (!$meta) continue;

        // Use folder name as ad_id if not present
        $adId = $meta['ad_id'] ?? $adFolder;
        $meta['ad_id'] = $adId;

        // Get analytics
        $analyticsFile = "$analyticsBase/$adId.json";
        $analytics = ['total_views' => 0, 'total_contacts' => 0, 'total_clicks' => 0, 'events' => []];
        if (file_exists($analyticsFile)) {
            $analytics = json_decode(file_get_contents($analyticsFile), true);
        }

        $allAds[] = [
            'meta' => $meta,
            'analytics' => $analytics,
            'category' => $category
        ];

        // Update overview stats
        $stats['overview']['total_ads']++;
        $status = $meta['status'] ?? 'active';
        if ($status === 'active') $stats['overview']['active_ads']++;
        elseif ($status === 'paused') $stats['overview']['paused_ads']++;
        elseif ($status === 'scheduled') $stats['overview']['scheduled_ads']++;
        elseif ($status === 'expired') $stats['overview']['expired_ads']++;

        // Update performance stats
        $stats['performance']['total_views'] += $analytics['total_views'] ?? 0;
        $stats['performance']['total_contacts'] += $analytics['total_contacts'] ?? 0;
        $stats['performance']['total_clicks'] += $analytics['total_clicks'] ?? 0;
        $stats['performance']['total_likes'] += $analytics['total_likes'] ?? 0;
        $stats['performance']['total_dislikes'] += $analytics['total_dislikes'] ?? 0;
        $stats['performance']['total_favorites'] += $analytics['total_favorites'] ?? 0;
        $stats['performance']['current_favorites'] += $analytics['current_favorites'] ?? 0;

        // Category breakdown
        if (!isset($stats['categories'][$category])) {
            $stats['categories'][$category] = [
                'count' => 0,
                'views' => 0,
                'contacts' => 0
            ];
        }
        $stats['categories'][$category]['count']++;
        $stats['categories'][$category]['views'] += $analytics['total_views'] ?? 0;
        $stats['categories'][$category]['contacts'] += $analytics['total_contacts'] ?? 0;

        // Process events for trends
        foreach ($analytics['events'] ?? [] as $event) {
            $date = date('Y-m-d', $event['timestamp']);
            if (!isset($stats['trends']['daily_stats'][$date])) {
                $stats['trends']['daily_stats'][$date] = [
                    'views' => 0,
                    'contacts' => 0,
                    'clicks' => 0
                ];
            }
            if ($event['type'] === 'view') $stats['trends']['daily_stats'][$date]['views']++;
            if ($event['type'] === 'contact') $stats['trends']['daily_stats'][$date]['contacts']++;
            if ($event['type'] === 'click') $stats['trends']['daily_stats'][$date]['clicks']++;
        }
    }
}

// Calculate derived metrics
if ($stats['overview']['total_ads'] > 0) {
    $stats['performance']['avg_views_per_ad'] = round($stats['performance']['total_views'] / $stats['overview']['total_ads'], 2);
}

if ($stats['performance']['total_views'] > 0) {
    $stats['performance']['conversion_rate'] = round(($stats['performance']['total_contacts'] / $stats['performance']['total_views']) * 100, 2);
    $stats['performance']['favorite_rate'] = round(($stats['performance']['current_favorites'] / $stats['performance']['total_views']) * 100, 2);
}

// Sort and get top performers (by combined score)
usort($allAds, function($a, $b) {
    $scoreA = ($a['analytics']['total_views'] ?? 0) +
              ($a['analytics']['total_contacts'] ?? 0) * 5 +
              ($a['analytics']['current_favorites'] ?? 0) * 3;
    $scoreB = ($b['analytics']['total_views'] ?? 0) +
              ($b['analytics']['total_contacts'] ?? 0) * 5 +
              ($b['analytics']['current_favorites'] ?? 0) * 3;
    return $scoreB - $scoreA;
});
$stats['top_performers'] = array_slice(array_map(function($ad) {
    return [
        'ad_id' => $ad['meta']['ad_id'],
        'title' => $ad['meta']['title'],
        'views' => $ad['analytics']['total_views'] ?? 0,
        'contacts' => $ad['analytics']['total_contacts'] ?? 0,
        'favorites' => $ad['analytics']['current_favorites'] ?? 0,
        'likes' => $ad['analytics']['total_likes'] ?? 0,
        'category' => $ad['category']
    ];
}, $allAds), 0, 5);

// Get last 7 days trend
for ($i = 6; $i >= 0; $i--) {
    $date = date('Y-m-d', strtotime("-$i days"));
    $dayStats = $stats['trends']['daily_stats'][$date] ?? ['views' => 0, 'contacts' => 0];
    $stats['trends']['views_trend'][] = $dayStats['views'];
    $stats['trends']['contacts_trend'][] = $dayStats['contacts'];
}

// Revenue estimation (basic)
$stats['revenue_estimate']['total_value'] = $stats['performance']['total_contacts'] * 5; // $5 per lead
$stats['revenue_estimate']['projected_monthly'] = $stats['revenue_estimate']['total_value'] * 4;

// AI Insights (rule-based)
if ($stats['performance']['conversion_rate'] < 2) {
    $stats['ai_insights'][] = [
        'type' => 'warning',
        'title' => 'Low Conversion Rate',
        'message' => 'Your conversion rate is below 2%. Consider improving ad descriptions and images.',
        'action' => 'View Tips'
    ];
}

if ($stats['overview']['total_ads'] > 0 && $stats['performance']['avg_views_per_ad'] < 50) {
    $stats['ai_insights'][] = [
        'type' => 'info',
        'title' => 'Boost Visibility',
        'message' => 'Your ads are getting less than 50 views on average. Consider using the Boost feature.',
        'action' => 'Boost Ads'
    ];
}

if ($stats['overview']['paused_ads'] > $stats['overview']['active_ads']) {
    $stats['ai_insights'][] = [
        'type' => 'info',
        'title' => 'Many Paused Ads',
        'message' => 'You have more paused ads than active ones. Activate them to reach more customers.',
        'action' => 'Manage Ads'
    ];
}

if (count($stats['top_performers']) > 0 && $stats['top_performers'][0]['views'] > 100) {
    $topAd = $stats['top_performers'][0];
    $stats['ai_insights'][] = [
        'type' => 'success',
        'title' => 'Top Performer Detected',
        'message' => "'{$topAd['title']}' is performing exceptionally well with {$topAd['views']} views!",
        'action' => 'Duplicate'
    ];
}

echo json_encode([
    'success' => true,
    'data' => $stats,
    'generated_at' => time()
]);

