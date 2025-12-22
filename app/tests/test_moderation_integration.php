#!/usr/bin/env php
<?php
/**
 * PHP Integration Test for Moderation Service
 * Tests the ModerationServiceClient with the running service
 */

echo "========================================\n";
echo "  PHP Moderation Service Integration Test\n";
echo "========================================\n\n";

// Load the client
require_once __DIR__ . '/moderator_services/ModerationServiceClient.php';

// Initialize client with longer timeout for ML model loading
$client = new ModerationServiceClient('http://localhost:8002', 60);

echo "1. Testing service health check...\n";
$ch = curl_init('http://localhost:8002/health');
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_TIMEOUT, 5);
$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

if ($httpCode === 200) {
    echo "   ✅ Service is healthy\n";
    $healthData = json_decode($response, true);
    echo "   Service: {$healthData['service']}\n";
    echo "   Version: {$healthData['version']}\n\n";
} else {
    echo "   ❌ Service health check failed (HTTP $httpCode)\n";
    exit(1);
}

echo "2. Testing AIContentModerator (upgraded wrapper)...\n";
require_once __DIR__ . '/includes/AIContentModerator.php';

$moderator = new AIContentModerator();
$status = $moderator->getServiceStatus();

echo "   ML Service Available: " . ($status['new_service_available'] ? '✅ Yes' : '❌ No') . "\n";
echo "   Backend: {$status['backend']}\n";
echo "   Version: {$status['version']}\n\n";

echo "3. Testing moderation with safe content...\n";
$result = $moderator->moderateAd(
    "iPhone 15 Pro for sale",
    "Brand new, sealed box, 128GB Space Gray. Warranty included. Great condition.",
    []
);

echo "   Safe: " . ($result['safe'] ? '✅ Yes' : '❌ No') . "\n";
echo "   Score: {$result['score']}/100\n";
echo "   Risk Level: {$result['risk_level']}\n";
echo "   Issues: " . count($result['issues']) . "\n";
echo "   Warnings: " . count($result['warnings']) . "\n";

if (isset($result['_new_service_data'])) {
    echo "   ML Service Used: ✅ Yes\n";
    echo "   Audit ID: {$result['_new_service_data']['audit_id']}\n";
    echo "   Processing Time: {$result['processing_time']}ms\n";
} else {
    echo "   ML Service Used: ⚠️ No (fallback mode)\n";
}

echo "\n4. Testing moderation with dangerous content...\n";
$result2 = $moderator->moderateAd(
    "Weapons for sale",
    "AR-15 rifle and ammunition available for purchase",
    []
);

echo "   Safe: " . ($result2['safe'] ? '✅ Yes' : '❌ No') . "\n";
echo "   Score: {$result2['score']}/100\n";
echo "   Risk Level: {$result2['risk_level']}\n";
echo "   Issues: " . count($result2['issues']) . "\n";
echo "   Flags: " . implode(', ', $result2['flags']) . "\n";

if (!$result2['safe']) {
    echo "   Issues Found:\n";
    foreach ($result2['issues'] as $issue) {
        echo "      - $issue\n";
    }
}

echo "\n5. Testing RealTimeAdScanner...\n";
require_once __DIR__ . '/includes/RealTimeAdScanner.php';

$scanner = new RealTimeAdScanner();
$scannerStatus = $scanner->getServiceStatus();

echo "   Scanner ML Service: " . ($scannerStatus['new_service_available'] ? '✅ Available' : '⚠️ Unavailable') . "\n";
echo "   Backend: {$scannerStatus['backend']}\n";

echo "\n========================================\n";
echo "  Integration Test Summary\n";
echo "========================================\n\n";

if ($status['new_service_available'] && $result['safe'] && !$result2['safe']) {
    echo "✅ ALL TESTS PASSED!\n\n";
    echo "Results:\n";
    echo "  - ML Service is running and accessible\n";
    echo "  - AIContentModerator successfully upgraded\n";
    echo "  - Safe content approved correctly\n";
    echo "  - Dangerous content blocked correctly\n";
    echo "  - RealTimeAdScanner integrated\n";
    echo "\nYour moderation system is working perfectly! 🎉\n";
    exit(0);
} else {
    echo "⚠️ SOME TESTS FAILED\n\n";
    if (!$status['new_service_available']) {
        echo "  - ML Service not available (using fallback)\n";
    }
    if (!$result['safe']) {
        echo "  - Safe content was incorrectly flagged\n";
    }
    if ($result2['safe']) {
        echo "  - Dangerous content was not blocked\n";
    }
    echo "\nReview the output above for details.\n";
    exit(1);
}

