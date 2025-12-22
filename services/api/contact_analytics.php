<?php
/********************************************
 * Contact Method Analytics API
 * Comprehensive analytics for SMS, Call, Email, WhatsApp
 ********************************************/
session_start();
header("Content-Type: application/json");

if (!isset($_SESSION['company'])) {
    http_response_code(401);
    echo json_encode(['success' => false, 'message' => 'Unauthorized']);
    exit;
}

$companySlug = $_SESSION['company'];
$adId = $_GET['ad_id'] ?? '';
$days = intval($_GET['days'] ?? 30); // Default to 30 days

// Validate days parameter
if ($days < 1) $days = 30;
if ($days > 365) $days = 365;

$analyticsBase = __DIR__ . "/../companies/analytics/";
$dataBase = __DIR__ . "/../companies/data/";

// Helper function to analyze age group from user agent
function detectAgeGroup($userAgent) {
    // Simple heuristic based on device/browser patterns
    // In production, use ML or third-party services
    $patterns = [
        'youth' => ['TikTok', 'Snapchat', 'Instagram', 'Mobile', 'Android'],
        'middle_age' => ['Facebook', 'LinkedIn', 'Chrome', 'Safari'],
        'elderly' => ['Desktop', 'Windows', 'MSIE', 'Edge']
    ];

    foreach ($patterns as $group => $keywords) {
        foreach ($keywords as $keyword) {
            if (stripos($userAgent, $keyword) !== false) {
                return $group;
            }
        }
    }

    return 'unknown';
}

// Helper function to detect language preference
function detectLanguage($content, $metadata) {
    // Simple detection - can be enhanced with NLP
    $englishWords = ['the', 'and', 'for', 'you', 'with', 'best', 'new', 'free'];
    $swahiliWords = ['na', 'ya', 'kwa', 'ni', 'wa', 'kila', 'sana', 'kabisa'];

    $englishScore = 0;
    $swahiliScore = 0;

    $text = strtolower($content);
    foreach ($englishWords as $word) {
        if (stripos($text, $word) !== false) $englishScore++;
    }
    foreach ($swahiliWords as $word) {
        if (stripos($text, $word) !== false) $swahiliScore++;
    }

    if ($swahiliScore > $englishScore) return 'swahili';
    if ($englishScore > $swahiliScore) return 'english';
    return 'mixed';
}

// Get specific ad analytics
if (!empty($adId)) {
    $analyticsFile = "$analyticsBase/$adId.json";

    if (!file_exists($analyticsFile)) {
        echo json_encode([
            'success' => true,
            'contact_methods' => [
                'sms' => ['count' => 0, 'trend' => []],
                'call' => ['count' => 0, 'trend' => []],
                'email' => ['count' => 0, 'trend' => []],
                'whatsapp' => ['count' => 0, 'trend' => []]
            ],
            'demographics' => [],
            'ai_insights' => []
        ]);
        exit;
    }

    $analytics = json_decode(file_get_contents($analyticsFile), true);
    $events = $analytics['events'] ?? [];

    // Analyze contact methods
    $contactMethods = [
        'sms' => ['count' => 0, 'trend' => [], 'hourly' => array_fill(0, 24, 0)],
        'call' => ['count' => 0, 'trend' => [], 'hourly' => array_fill(0, 24, 0)],
        'email' => ['count' => 0, 'trend' => [], 'hourly' => array_fill(0, 24, 0)],
        'whatsapp' => ['count' => 0, 'trend' => [], 'hourly' => array_fill(0, 24, 0)]
    ];

    $ageGroups = ['youth' => 0, 'middle_age' => 0, 'elderly' => 0, 'unknown' => 0];
    $dailyData = [];

    // Analyze last 30 days
    $startDate = strtotime('-30 days');

    foreach ($events as $event) {
        if ($event['type'] === 'contact') {
            $method = strtolower($event['metadata']['method'] ?? 'unknown');
            $timestamp = $event['timestamp'];

            if (isset($contactMethods[$method])) {
                $contactMethods[$method]['count']++;

                // Track hourly patterns
                $hour = (int)date('H', $timestamp);
                $contactMethods[$method]['hourly'][$hour]++;

                // Track daily for line graph
                $date = date('Y-m-d', $timestamp);
                if (!isset($dailyData[$date])) {
                    $dailyData[$date] = [
                        'sms' => 0, 'call' => 0, 'email' => 0, 'whatsapp' => 0
                    ];
                }
                $dailyData[$date][$method]++;

                // Detect age group
                $ageGroup = detectAgeGroup($event['user_agent'] ?? '');
                $ageGroups[$ageGroup]++;
            }
        }
    }

    // Build trend data for requested number of days
    for ($i = $days - 1; $i >= 0; $i--) {
        $date = date('Y-m-d', strtotime("-$i days"));
        $day = date('M j', strtotime("-$i days"));

        foreach ($contactMethods as $method => &$data) {
            $data['trend'][] = [
                'date' => $day,
                'count' => $dailyData[$date][$method] ?? 0
            ];
        }
    }

    // Find dominant age group
    arsort($ageGroups);
    $dominantAge = array_key_first($ageGroups);

    // Find best performing contact method
    $bestMethod = 'call';
    $maxContacts = 0;
    foreach ($contactMethods as $method => $data) {
        if ($data['count'] > $maxContacts) {
            $maxContacts = $data['count'];
            $bestMethod = $method;
        }
    }

    // Find peak contact hours
    $allHourly = array_fill(0, 24, 0);
    foreach ($contactMethods as $data) {
        for ($h = 0; $h < 24; $h++) {
            $allHourly[$h] += $data['hourly'][$h];
        }
    }
    $peakHour = array_keys($allHourly, max($allHourly))[0];

    // Generate AI insights
    $insights = [];

    // Age demographic insight
    if ($ageGroups[$dominantAge] > 0) {
        $percentage = round(($ageGroups[$dominantAge] / array_sum($ageGroups)) * 100);
        $ageLabel = [
            'youth' => 'young audience (18-25 years)',
            'middle_age' => 'middle-aged audience (26-45 years)',
            'elderly' => 'mature audience (46+ years)',
            'unknown' => 'diverse audience'
        ];

        $insights[] = [
            'type' => 'demographics',
            'icon' => 'fa-users',
            'title' => 'Audience Profile',
            'message' => "Your ads are mostly viewed by {$ageLabel[$dominantAge]} ({$percentage}% of viewers)",
            'recommendation' => getAgeGroupRecommendation($dominantAge),
            'priority' => 'high'
        ];
    }

    // Best contact method insight
    if ($maxContacts > 0) {
        $methodLabels = [
            'whatsapp' => 'WhatsApp',
            'call' => 'Phone Calls',
            'sms' => 'SMS',
            'email' => 'Email'
        ];

        $insights[] = [
            'type' => 'contact_preference',
            'icon' => 'fa-phone',
            'title' => 'Preferred Contact Method',
            'message' => "{$methodLabels[$bestMethod]} is your top-performing contact method with {$maxContacts} contacts",
            'recommendation' => "Highlight your {$bestMethod} contact prominently in ad descriptions",
            'priority' => 'high'
        ];
    }

    // Peak time insight
    if ($peakHour !== null) {
        $timeLabel = ($peakHour < 12) ? "{$peakHour}AM" : (($peakHour == 12) ? "12PM" : ($peakHour - 12) . "PM");

        $insights[] = [
            'type' => 'timing',
            'icon' => 'fa-clock',
            'title' => 'Peak Contact Time',
            'message' => "Most contacts happen around {$timeLabel}",
            'recommendation' => "Post new ads or boost existing ones before peak hours for maximum visibility",
            'priority' => 'medium'
        ];
    }

    // Content insights
    $totalViews = $analytics['total_views'] ?? 0;
    $totalContacts = $analytics['total_contacts'] ?? 0;
    $conversionRate = $totalViews > 0 ? ($totalContacts / $totalViews) * 100 : 0;

    if ($conversionRate < 2) {
        $insights[] = [
            'type' => 'content',
            'icon' => 'fa-edit',
            'title' => 'Improve Your Ad Copy',
            'message' => "Your conversion rate is {$conversionRate}%. Try using more action words",
            'recommendation' => getContentRecommendation($dominantAge),
            'priority' => 'high'
        ];
    }

    echo json_encode([
        'success' => true,
        'contact_methods' => $contactMethods,
        'demographics' => $ageGroups,
        'peak_hour' => $peakHour,
        'best_method' => $bestMethod,
        'conversion_rate' => round($conversionRate, 2),
        'ai_insights' => $insights
    ]);
    exit;
}

// Get all ads analytics for company
$allContactMethods = [
    'sms' => ['count' => 0, 'trend' => []],
    'call' => ['count' => 0, 'trend' => []],
    'email' => ['count' => 0, 'trend' => []],
    'whatsapp' => ['count' => 0, 'trend' => []]
];

$allAgeGroups = ['youth' => 0, 'middle_age' => 0, 'elderly' => 0, 'unknown' => 0];
$dailyTotals = [];

// Scan all company ads
$debugInfo = ['scanned_files' => [], 'contact_events' => 0];

foreach (scandir($dataBase) as $category) {
    if ($category === '.' || $category === '..') continue;

    $categoryPath = "$dataBase/$category";
    if (!is_dir($categoryPath)) continue;

    $companyPath = "$categoryPath/$companySlug";
    if (!is_dir($companyPath)) continue;

    foreach (scandir($companyPath) as $adFolder) {
        if ($adFolder === '.' || $adFolder === '..') continue;

        $analyticsFile = "$analyticsBase/$adFolder.json";
        if (!file_exists($analyticsFile)) continue;

        $debugInfo['scanned_files'][] = $adFolder;

        $analytics = json_decode(file_get_contents($analyticsFile), true);
        $events = $analytics['events'] ?? [];

        foreach ($events as $event) {
            if ($event['type'] === 'contact') {
                $debugInfo['contact_events']++;
                $method = strtolower($event['metadata']['method'] ?? 'unknown');
                $timestamp = $event['timestamp'];

                // Debug: track methods found
                if (!isset($debugInfo['methods_found'])) {
                    $debugInfo['methods_found'] = [];
                }
                if (!isset($debugInfo['methods_found'][$method])) {
                    $debugInfo['methods_found'][$method] = 0;
                }
                $debugInfo['methods_found'][$method]++;

                if (isset($allContactMethods[$method])) {
                    $allContactMethods[$method]['count']++;

                    $date = date('Y-m-d', $timestamp);
                    if (!isset($dailyTotals[$date])) {
                        $dailyTotals[$date] = [
                            'sms' => 0, 'call' => 0, 'email' => 0, 'whatsapp' => 0
                        ];
                    }
                    $dailyTotals[$date][$method]++;

                    $ageGroup = detectAgeGroup($event['user_agent'] ?? '');
                    $allAgeGroups[$ageGroup]++;
                } else {
                    // Debug: track unrecognized methods
                    if (!isset($debugInfo['unrecognized_methods'])) {
                        $debugInfo['unrecognized_methods'] = [];
                    }
                    $debugInfo['unrecognized_methods'][] = $method;
                }
            }
        }
    }
}

// Debug: Check counts after loop
$debugInfo['counts_after_loop'] = [
    'whatsapp' => $allContactMethods['whatsapp']['count'],
    'call' => $allContactMethods['call']['count'],
    'sms' => $allContactMethods['sms']['count'],
    'email' => $allContactMethods['email']['count']
];

// Build trend for requested number of days
for ($i = $days - 1; $i >= 0; $i--) {
    $date = date('Y-m-d', strtotime("-$i days"));
    $day = date('M j', strtotime("-$i days"));

    foreach ($allContactMethods as $method => &$data) {
        $data['trend'][] = [
            'date' => $day,
            'count' => $dailyTotals[$date][$method] ?? 0
        ];
    }
    unset($data); // Critical: Unset reference to prevent PHP reference bug
}

// Generate company-wide insights
arsort($allAgeGroups);
$dominantAge = array_key_first($allAgeGroups);

$bestMethod = 'call';
$maxContacts = 0;
foreach ($allContactMethods as $method => $data) {
    if ($data['count'] > $maxContacts) {
        $maxContacts = $data['count'];
        $bestMethod = $method;
    }
}

$companyInsights = [];

if ($allAgeGroups[$dominantAge] > 0) {
    $percentage = round(($allAgeGroups[$dominantAge] / array_sum($allAgeGroups)) * 100);
    $ageLabel = [
        'youth' => 'young audience (18-25 years)',
        'middle_age' => 'middle-aged audience (26-45 years)',
        'elderly' => 'mature audience (46+ years)',
        'unknown' => 'diverse audience'
    ];

    $companyInsights[] = [
        'type' => 'demographics',
        'icon' => 'fa-users',
        'title' => 'Overall Audience Profile',
        'message' => "Your ads primarily attract {$ageLabel[$dominantAge]} ({$percentage}% of all viewers)",
        'recommendation' => getAgeGroupRecommendation($dominantAge),
        'priority' => 'high'
    ];
}

// Add final counts to debug
$debugInfo['final_counts'] = [
    'whatsapp' => $allContactMethods['whatsapp']['count'],
    'call' => $allContactMethods['call']['count'],
    'sms' => $allContactMethods['sms']['count'],
    'email' => $allContactMethods['email']['count']
];

echo json_encode([
    'success' => true,
    'contact_methods' => $allContactMethods,
    'demographics' => $allAgeGroups,
    'best_method' => $bestMethod,
    'ai_insights' => $companyInsights,
    'debug' => $debugInfo
]);

// Helper functions for recommendations
function getAgeGroupRecommendation($ageGroup) {
    $recommendations = [
        'youth' => "Use trendy language, emojis, and social media references. Highlight mobile payment options and fast delivery.",
        'middle_age' => "Focus on value, quality, and reliability. Use professional language and emphasize family benefits.",
        'elderly' => "Use clear, simple language. Emphasize safety, quality, and personal service. Include phone contact prominently.",
        'unknown' => "Use balanced language that appeals to all ages. Focus on universal benefits like quality and value."
    ];

    return $recommendations[$ageGroup] ?? $recommendations['unknown'];
}

function getContentRecommendation($ageGroup) {
    $recommendations = [
        'youth' => "Try: 'Grab this deal NOW! 🔥', 'Limited time offer!', 'DM for fast response'",
        'middle_age' => "Try: 'Quality guaranteed', 'Best value for your family', 'Call now for details'",
        'elderly' => "Try: 'Trusted quality', 'Personal service available', 'Easy to reach us by phone'",
        'unknown' => "Try: 'Contact us today', 'Great quality, great price', 'Multiple ways to reach us'"
    ];

    return $recommendations[$ageGroup] ?? $recommendations['unknown'];
}

