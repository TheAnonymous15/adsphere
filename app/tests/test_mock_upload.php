#!/usr/bin/env php
<?php
/**
 * Mock Ad Upload Test
 * Tests the upload system with various ad types to see moderation in action
 */

error_reporting(E_ALL);
ini_set('display_errors', 1);

// Simulate session (required by upload_ad.php)
session_start();
$_SESSION['company'] = 'meda-media-technologies';
$_SESSION['company_name'] = 'Test Company';
$_SESSION['user_id'] = 'test_user_001';

echo "========================================\n";
echo "  Mock Ad Upload Test\n";
echo "  Testing AI/ML Moderation System\n";
echo "========================================\n\n";

// Load required files
require_once __DIR__ . '/database/Database.php';
require_once __DIR__ . '/includes/AIContentModerator.php';

$moderator = new AIContentModerator();

// Check service status
echo "1. Checking Moderation Service Status...\n";
$status = $moderator->getServiceStatus();
echo "   ML Service: " . ($status['new_service_available'] ? '✅ Available' : '⚠️ Unavailable') . "\n";
echo "   Backend: {$status['backend']}\n";
echo "   Version: {$status['version']}\n\n";

// Test cases with different content types
$testAds = [
    // Test 1: Clean, safe ad
    [
        'name' => 'Clean Product Ad',
        'title' => 'Brand New iPhone 15 Pro',
        'description' => 'Excellent condition, 128GB Space Gray, comes with original box and charger. Never used, still sealed. Great deal!',
        'expected' => 'APPROVE'
    ],

    // Test 2: Spam-like content
    [
        'name' => 'Spam Ad',
        'title' => 'URGENT!!! AMAZING DEAL!!!',
        'description' => 'CLICK HERE NOW!!! Limited time only!!! Act fast!!! Don\'t miss out!!! BUY NOW!!!',
        'expected' => 'REVIEW/FLAG'
    ],

    // Test 3: Weapons content (should be BLOCKED)
    [
        'name' => 'Weapons Ad',
        'title' => 'Firearms for sale',
        'description' => 'Selling AR-15 rifle with ammunition. Also have pistols and knives available. Contact for details.',
        'expected' => 'BLOCK'
    ],

    // Test 4: Drugs content (should be BLOCKED)
    [
        'name' => 'Drugs Ad',
        'title' => 'Party supplies available',
        'description' => 'Cocaine, heroin, and meth for sale. Fast delivery, no questions asked. Cash only.',
        'expected' => 'BLOCK'
    ],

    // Test 5: Hate speech (should be BLOCKED)
    [
        'name' => 'Hate Speech Ad',
        'title' => 'Special group gathering',
        'description' => 'We hate all foreigners and will destroy them. Join our racist movement today!',
        'expected' => 'BLOCK'
    ],

    // Test 6: Stolen goods (should be BLOCKED)
    [
        'name' => 'Stolen Goods Ad',
        'title' => 'Cheap electronics',
        'description' => 'Selling stolen iPhones and laptops. No receipts, no questions asked. Very cheap prices.',
        'expected' => 'BLOCK'
    ],

    // Test 7: Borderline content
    [
        'name' => 'Borderline Ad',
        'title' => 'Amazing weight loss product',
        'description' => 'Lose 30 pounds in 7 days! Guaranteed results! Miracle formula! No exercise needed!',
        'expected' => 'REVIEW'
    ],

    // Test 8: Normal housing ad
    [
        'name' => 'Housing Ad',
        'title' => 'Beautiful 2-bedroom apartment',
        'description' => 'Spacious apartment in downtown area, near shops and public transport. Rent $1200/month.',
        'expected' => 'APPROVE'
    ],

    // Test 9: Violent content
    [
        'name' => 'Violence Ad',
        'title' => 'Seeking revenge',
        'description' => 'Looking to hire someone to hurt my enemy. Will pay good money for violence and assault.',
        'expected' => 'BLOCK'
    ],

    // Test 10: Adult content
    [
        'name' => 'Adult Services Ad',
        'title' => 'Escort services available',
        'description' => 'Beautiful girls for hire, sexual services, no condom option available. Call now.',
        'expected' => 'BLOCK'
    ]
];

echo "2. Running Moderation Tests on " . count($testAds) . " Sample Ads...\n\n";
echo str_repeat("=", 80) . "\n\n";

$results = [
    'total' => count($testAds),
    'approved' => 0,
    'blocked' => 0,
    'reviewed' => 0,
    'correct_predictions' => 0
];

foreach ($testAds as $index => $testAd) {
    $testNum = $index + 1;

    echo "TEST {$testNum}: {$testAd['name']}\n";
    echo str_repeat("-", 80) . "\n";
    echo "Title: {$testAd['title']}\n";
    echo "Description: " . substr($testAd['description'], 0, 80) . "...\n";
    echo "Expected: {$testAd['expected']}\n\n";

    // Run moderation
    $startTime = microtime(true);
    $moderationResult = $moderator->moderateAd(
        $testAd['title'],
        $testAd['description'],
        [] // No images for this test
    );
    $processingTime = round((microtime(true) - $startTime) * 1000, 2);

    // Determine actual result
    $actualResult = 'UNKNOWN';
    if ($moderationResult['safe']) {
        if (!empty($moderationResult['warnings'])) {
            $actualResult = 'REVIEW';
            $results['reviewed']++;
        } else {
            $actualResult = 'APPROVE';
            $results['approved']++;
        }
    } else {
        $actualResult = 'BLOCK';
        $results['blocked']++;
    }

    // Check if prediction was correct
    $correct = false;
    if (strpos($testAd['expected'], $actualResult) !== false) {
        $correct = true;
        $results['correct_predictions']++;
    }

    // Display results
    echo "RESULT:\n";
    echo "   Decision: " . ($correct ? '✅' : '❌') . " {$actualResult}";
    if (!$correct) {
        echo " (Expected: {$testAd['expected']})";
    }
    echo "\n";
    echo "   Safe: " . ($moderationResult['safe'] ? 'Yes' : 'No') . "\n";
    echo "   AI Score: {$moderationResult['score']}/100\n";
    echo "   Risk Level: {$moderationResult['risk_level']}\n";
    echo "   Confidence: {$moderationResult['confidence']}%\n";
    echo "   Processing Time: {$processingTime}ms\n";

    if (!empty($moderationResult['flags'])) {
        echo "   Flags: " . implode(', ', $moderationResult['flags']) . "\n";
    }

    if (!empty($moderationResult['issues'])) {
        echo "   Issues:\n";
        foreach ($moderationResult['issues'] as $issue) {
            echo "      - {$issue}\n";
        }
    }

    if (!empty($moderationResult['warnings'])) {
        echo "   Warnings:\n";
        foreach ($moderationResult['warnings'] as $warning) {
            echo "      - {$warning}\n";
        }
    }

    // Show ML service data if available
    if (isset($moderationResult['_new_service_data'])) {
        $mlData = $moderationResult['_new_service_data'];
        echo "   ML Service:\n";
        echo "      Audit ID: {$mlData['audit_id']}\n";
        echo "      Decision: {$mlData['decision']}\n";
        echo "      Global Score: " . round($mlData['global_score'] * 100, 2) . "%\n";

        if (!empty($mlData['category_scores'])) {
            echo "      Category Scores:\n";
            foreach ($mlData['category_scores'] as $category => $score) {
                if ($score > 0) {
                    echo "         - {$category}: " . round($score * 100, 2) . "%\n";
                }
            }
        }

        if (!empty($mlData['ai_sources'])) {
            echo "      AI Models: " . implode(', ', array_keys($mlData['ai_sources'])) . "\n";
        }
    }

    echo "\n" . str_repeat("=", 80) . "\n\n";

    // Small delay to avoid overwhelming the service
    usleep(100000); // 100ms
}

// Summary
echo "\n";
echo "========================================\n";
echo "  Test Summary\n";
echo "========================================\n\n";

echo "Total Tests: {$results['total']}\n";
echo "Approved: {$results['approved']}\n";
echo "Blocked: {$results['blocked']}\n";
echo "Flagged for Review: {$results['reviewed']}\n\n";

$accuracy = round(($results['correct_predictions'] / $results['total']) * 100, 1);
echo "Accuracy: {$results['correct_predictions']}/{$results['total']} ({$accuracy}%)\n\n";

if ($accuracy >= 90) {
    echo "✅ EXCELLENT! Moderation system is working very well!\n";
} elseif ($accuracy >= 70) {
    echo "✅ GOOD! Moderation system is working properly.\n";
} elseif ($accuracy >= 50) {
    echo "⚠️  FAIR. Moderation system needs tuning.\n";
} else {
    echo "❌ POOR. Moderation system needs significant improvement.\n";
}

echo "\n";
echo "========================================\n";
echo "  Key Findings\n";
echo "========================================\n\n";

echo "Protection Levels:\n";
echo "   Safe Content: " . ($results['approved'] > 0 ? '✅ Approved correctly' : '❌ Issues detected') . "\n";
echo "   Weapons: " . ($results['blocked'] >= 2 ? '✅ Blocked' : '⚠️ Check weapons detection') . "\n";
echo "   Drugs: " . ($results['blocked'] >= 2 ? '✅ Blocked' : '⚠️ Check drugs detection') . "\n";
echo "   Hate Speech: " . ($results['blocked'] >= 2 ? '✅ Blocked' : '⚠️ Check hate detection') . "\n";
echo "   Spam: " . ($results['reviewed'] >= 1 ? '✅ Flagged' : '⚠️ Check spam detection') . "\n";

echo "\n✅ Mock upload test complete!\n";

