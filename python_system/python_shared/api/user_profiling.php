<?php
/********************************************
 * Advanced User Profiling API
 * Device fingerprinting, preference learning, AI recommendations
 ********************************************/
header("Content-Type: application/json");

// Get request data
$input = json_decode(file_get_contents('php://input'), true);
$action = $input['action'] ?? ''; // 'get_profile', 'update_profile', 'get_recommendations'
$deviceId = $input['device_id'] ?? '';
$preferences = $input['preferences'] ?? [];

if (empty($action)) {
    http_response_code(400);
    echo json_encode(['success' => false, 'message' => 'No action specified']);
    exit;
}

$profilesBase = __DIR__ . "/../companies/user_profiles/";
if (!is_dir($profilesBase)) {
    mkdir($profilesBase, 0775, true);
}

// ============================================
// GET USER PROFILE
// ============================================
if ($action === 'get_profile' && $deviceId) {
    $profileFile = "$profilesBase/$deviceId.json";

    if (file_exists($profileFile)) {
        $profile = json_decode(file_get_contents($profileFile), true);
        echo json_encode([
            'success' => true,
            'profile' => $profile,
            'is_new' => false
        ]);
    } else {
        // Create new profile
        $profile = [
            'device_id' => $deviceId,
            'created_at' => time(),
            'last_active' => time(),
            'total_sessions' => 1,
            'preferences' => [
                'liked_categories' => [],
                'disliked_categories' => [],
                'liked_ads' => [],
                'disliked_ads' => [],
                'favorite_ads' => [],
                'viewed_ads' => [],
                'contacted_ads' => []
            ],
            'behavior' => [
                'avg_time_per_ad' => 0,
                'total_time_spent' => 0,
                'total_interactions' => 0,
                'preferred_ad_types' => [], // image, video
                'browse_patterns' => [],
                'peak_activity_hours' => []
            ],
            'demographics' => [
                'device_type' => $input['device_type'] ?? 'unknown',
                'browser' => $input['browser'] ?? 'unknown',
                'os' => $input['os'] ?? 'unknown',
                'screen_size' => $input['screen_size'] ?? 'unknown',
                'timezone' => $input['timezone'] ?? 'unknown'
            ],
            'ml_scores' => [
                'engagement_score' => 0,
                'conversion_probability' => 0,
                'value_score' => 0
            ]
        ];

        file_put_contents($profileFile, json_encode($profile, JSON_PRETTY_PRINT));

        echo json_encode([
            'success' => true,
            'profile' => $profile,
            'is_new' => true
        ]);
    }
    exit;
}

// ============================================
// UPDATE USER PROFILE
// ============================================
if ($action === 'update_profile' && $deviceId && $preferences) {
    $profileFile = "$profilesBase/$deviceId.json";
    $profile = [];

    if (file_exists($profileFile)) {
        $profile = json_decode(file_get_contents($profileFile), true);
    } else {
        http_response_code(404);
        echo json_encode(['success' => false, 'message' => 'Profile not found']);
        exit;
    }

    // Update profile with new preferences
    $profile['last_active'] = time();
    $profile['total_sessions']++;

    // Update preferences
    foreach ($preferences as $key => $value) {
        if (isset($profile['preferences'][$key])) {
            if (is_array($value)) {
                $profile['preferences'][$key] = array_unique(array_merge($profile['preferences'][$key], $value));
                // Limit array size
                $profile['preferences'][$key] = array_slice($profile['preferences'][$key], -100);
            } else {
                $profile['preferences'][$key] = $value;
            }
        }
    }

    // Update behavior patterns
    if (isset($preferences['time_spent'])) {
        $profile['behavior']['total_time_spent'] += $preferences['time_spent'];
        $profile['behavior']['total_interactions']++;
        $profile['behavior']['avg_time_per_ad'] = round(
            $profile['behavior']['total_time_spent'] / $profile['behavior']['total_interactions'],
            2
        );
    }

    // Track activity hours
    $currentHour = (int)date('G');
    if (!isset($profile['behavior']['peak_activity_hours'][$currentHour])) {
        $profile['behavior']['peak_activity_hours'][$currentHour] = 0;
    }
    $profile['behavior']['peak_activity_hours'][$currentHour]++;

    // Calculate ML scores
    $profile['ml_scores'] = calculateMLScores($profile);

    file_put_contents($profileFile, json_encode($profile, JSON_PRETTY_PRINT));

    echo json_encode([
        'success' => true,
        'profile' => $profile,
        'message' => 'Profile updated'
    ]);
    exit;
}

// ============================================
// GET PERSONALIZED RECOMMENDATIONS
// ============================================
if ($action === 'get_recommendations' && $deviceId) {
    $profileFile = "$profilesBase/$deviceId.json";

    if (!file_exists($profileFile)) {
        echo json_encode([
            'success' => true,
            'recommendations' => [],
            'algorithm' => 'default',
            'message' => 'No profile found, showing default'
        ]);
        exit;
    }

    $profile = json_decode(file_get_contents($profileFile), true);

    // Load all ads
    $adsBase = __DIR__ . "/../companies/data/";
    $allAds = [];

    foreach (scandir($adsBase) as $category) {
        if ($category === '.' || $category === '..') continue;

        $categoryPath = "$adsBase/$category";
        if (!is_dir($categoryPath)) continue;

        foreach (scandir($categoryPath) as $company) {
            if ($company === '.' || $company === '..') continue;

            $companyPath = "$categoryPath/$company";
            if (!is_dir($companyPath)) continue;

            foreach (scandir($companyPath) as $adFolder) {
                if ($adFolder === '.' || $adFolder === '..') continue;

                $metaFile = "$companyPath/$adFolder/meta.json";
                if (!file_exists($metaFile)) continue;

                $meta = json_decode(file_get_contents($metaFile), true);
                if (!$meta) continue;

                // Calculate relevance score for this ad
                $score = calculateRelevanceScore($meta, $profile, $category);

                $allAds[] = [
                    'ad' => $meta,
                    'category' => $category,
                    'score' => $score
                ];
            }
        }
    }

    // Sort by relevance score
    usort($allAds, function($a, $b) {
        return $b['score'] - $a['score'];
    });

    // Get top recommendations
    $recommendations = array_slice($allAds, 0, 50);

    echo json_encode([
        'success' => true,
        'recommendations' => $recommendations,
        'algorithm' => 'ml_personalized',
        'profile_strength' => calculateProfileStrength($profile),
        'total_ads_scored' => count($allAds)
    ]);
    exit;
}

// ============================================
// ML SCORING FUNCTIONS
// ============================================
function calculateRelevanceScore($ad, $profile, $category) {
    $score = 0;
    $weights = [
        'favorite' => 40,           // Highest weight for favorites
        'category_match' => 25,
        'previous_likes' => 20,
        'time_engagement' => 15,
        'recency' => 10,
        'novelty' => 10,
        'popularity' => 5
    ];

    // Favorite ads (STRONGEST signal)
    $favoriteAds = $profile['preferences']['favorite_ads'] ?? [];
    if (in_array($ad['ad_id'], $favoriteAds)) {
        $score += $weights['favorite'];
    }

    // Category preference
    $likedCategories = $profile['preferences']['liked_categories'] ?? [];
    if (in_array($category, $likedCategories)) {
        $score += $weights['category_match'];
    }

    // Previous likes
    $likedAds = $profile['preferences']['liked_ads'] ?? [];
    $dislikedAds = $profile['preferences']['disliked_ads'] ?? [];

    if (in_array($ad['ad_id'], $likedAds)) {
        $score += $weights['previous_likes'];
    }
    if (in_array($ad['ad_id'], $dislikedAds)) {
        $score -= $weights['previous_likes'] * 2; // Heavy penalty
    }

    // Time engagement pattern
    $avgTime = $profile['behavior']['avg_time_per_ad'] ?? 0;
    if ($avgTime > 20) { // User engages deeply
        $score += $weights['time_engagement'];
    }

    // Recency (newer ads get slight boost)
    $adAge = time() - ($ad['timestamp'] ?? time());
    $daysSincePosted = $adAge / 86400;
    if ($daysSincePosted < 7) {
        $score += $weights['recency'] * (1 - ($daysSincePosted / 7));
    }

    // Novelty (haven't seen this ad before)
    $viewedAds = $profile['preferences']['viewed_ads'] ?? [];
    if (!in_array($ad['ad_id'], $viewedAds)) {
        $score += $weights['novelty'];
    }

    // Popularity boost
    $analyticsFile = __DIR__ . "/../companies/analytics/{$ad['ad_id']}.json";
    if (file_exists($analyticsFile)) {
        $analytics = json_decode(file_get_contents($analyticsFile), true);
        $likes = $analytics['total_likes'] ?? 0;
        $dislikes = $analytics['total_dislikes'] ?? 0;

        if ($likes > $dislikes && $likes > 10) {
            $score += $weights['popularity'];
        }
    }

    // Random factor for diversity (5%)
    $score += rand(0, 5);

    return $score;
}

function calculateMLScores($profile) {
    $scores = [
        'engagement_score' => 0,
        'conversion_probability' => 0,
        'value_score' => 0
    ];

    // Engagement score (0-100)
    $totalInteractions = $profile['behavior']['total_interactions'] ?? 0;
    $avgTime = $profile['behavior']['avg_time_per_ad'] ?? 0;
    $likedAds = count($profile['preferences']['liked_ads'] ?? []);

    $scores['engagement_score'] = min(100, (
        ($totalInteractions * 2) +
        ($avgTime * 1.5) +
        ($likedAds * 3)
    ));

    // Conversion probability (0-1)
    $contactedAds = count($profile['preferences']['contacted_ads'] ?? []);
    $viewedAds = count($profile['preferences']['viewed_ads'] ?? []);

    if ($viewedAds > 0) {
        $scores['conversion_probability'] = round($contactedAds / $viewedAds, 4);
    }

    // Value score (estimated user value)
    $scores['value_score'] = round(
        ($contactedAds * 5) +
        ($likedAds * 1) +
        ($scores['engagement_score'] * 0.1),
        2
    );

    return $scores;
}

function calculateProfileStrength($profile) {
    $totalInteractions = $profile['behavior']['total_interactions'] ?? 0;
    $sessions = $profile['total_sessions'] ?? 1;

    if ($totalInteractions < 5) return 'weak';
    if ($totalInteractions < 20) return 'moderate';
    if ($totalInteractions < 50) return 'strong';
    return 'very_strong';
}

echo json_encode(['success' => false, 'message' => 'Invalid action']);

