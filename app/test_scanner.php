#!/usr/bin/env php
<?php
/**
 * Test RealTimeAdScanner with Database Ads
 * Scans all ads in your database and shows results
 */

echo "========================================\n";
echo "  Real-Time Ad Scanner Test\n";
echo "  Scanning Database Ads\n";
echo "========================================\n\n";

// Load required files
require_once __DIR__ . '/database/Database.php';
require_once __DIR__ . '/includes/RealTimeAdScanner.php';

echo "1. Initializing scanner...\n";
$scanner = new RealTimeAdScanner();

// Check service status
$serviceStatus = $scanner->getServiceStatus();
echo "   ML Service: " . ($serviceStatus['new_service_available'] ? '✅ Available' : '⚠️ Unavailable') . "\n";
echo "   Backend: {$serviceStatus['backend']}\n";
echo "   Version: {$serviceStatus['version']}\n\n";

echo "2. Checking database for ads...\n";
$db = Database::getInstance();
$adsCount = $db->queryOne("SELECT COUNT(*) as count FROM ads WHERE status = 'active'");
$totalAds = $adsCount['count'] ?? 0;

echo "   Found: {$totalAds} active ads\n\n";

if ($totalAds == 0) {
    echo "⚠️  No active ads found in database.\n";
    echo "   Upload some ads first, then run this test again.\n";
    exit(0);
}

echo "3. Running scanner on all active ads...\n";
echo "   This may take a few moments...\n\n";

$startTime = microtime(true);
$results = $scanner->scanAllAds();
$scanTime = round((microtime(true) - $startTime) * 1000, 2);

echo "========================================\n";
echo "  Scan Results\n";
echo "========================================\n\n";

echo "📊 Statistics:\n";
echo "   Total Scanned: {$results['total_scanned']}\n";
echo "   Clean Ads: {$results['clean_ads']}\n";
echo "   Flagged Ads: " . count($results['flagged_ads']) . "\n";
echo "   Processing Time: {$scanTime}ms\n\n";

echo "🎯 By Severity:\n";
echo "   Critical: {$results['statistics']['critical']}\n";
echo "   High: {$results['statistics']['high']}\n";
echo "   Medium: {$results['statistics']['medium']}\n";
echo "   Low: {$results['statistics']['low']}\n\n";

echo "🤖 ML Service:\n";
echo "   Available: " . ($results['ml_service']['available'] ? 'Yes' : 'No') . "\n";
echo "   Backend: {$results['ml_service']['backend']}\n";
echo "   Version: {$results['ml_service']['version']}\n\n";

if (count($results['flagged_ads']) > 0) {
    echo "========================================\n";
    echo "  Flagged Ads Details\n";
    echo "========================================\n\n";

    foreach ($results['flagged_ads'] as $index => $ad) {
        $num = $index + 1;
        echo "🚩 Ad #{$num}: {$ad['ad_id']}\n";
        echo "   Title: {$ad['title']}\n";
        echo "   Company: {$ad['company']}\n";
        echo "   Category: {$ad['category']}\n";
        echo "   AI Score: {$ad['ai_score']}/100\n";
        echo "   Risk Level: {$ad['risk_level']}\n";
        echo "   Severity: {$ad['severity_level']}\n";
        echo "   Recommended Action: {$ad['recommendation']['primary_action']}\n";

        if (!empty($ad['violations']['content_issues'])) {
            echo "   Issues:\n";
            foreach ($ad['violations']['content_issues'] as $issue) {
                echo "      - $issue\n";
            }
        }

        if (!empty($ad['violations']['warnings'])) {
            echo "   Warnings:\n";
            foreach ($ad['violations']['warnings'] as $warning) {
                echo "      - $warning\n";
            }
        }

        // Show ML audit data if available
        if (isset($ad['ml_audit'])) {
            echo "   ML Audit ID: {$ad['ml_audit']['audit_id']}\n";
            echo "   ML Decision: {$ad['ml_audit']['decision']}\n";
            echo "   ML Score: {$ad['ml_audit']['global_score']}\n";

            // Show category scores
            $categoryScores = $ad['ml_audit']['category_scores'];
            $flaggedCategories = array_filter($categoryScores, fn($score) => $score > 0);
            if (!empty($flaggedCategories)) {
                echo "   Categories:\n";
                foreach ($flaggedCategories as $category => $score) {
                    echo "      - {$category}: {$score}\n";
                }
            }
        }

        echo "\n";
    }
} else {
    echo "✅ All ads are clean! No violations found.\n\n";
}

echo "========================================\n";
echo "  Scan Complete\n";
echo "========================================\n\n";

// Show report file location
$reportFile = __DIR__ . '/logs/scanner_reports_' . date('Y-m-d') . '.json';
echo "📁 Full report saved to:\n";
echo "   $reportFile\n\n";

// Show recommendation based on results
if (count($results['flagged_ads']) > 0) {
    echo "📋 Next Steps:\n";
    echo "   1. Review flagged ads above\n";
    echo "   2. Take recommended actions (warn/pause/delete/ban)\n";
    echo "   3. Check admin dashboard for violations\n";
    echo "   4. Run scanner regularly to monitor content\n";
} else {
    echo "✅ Your ad content is clean!\n";
    echo "   Continue to run scanner regularly to maintain quality.\n";
}

echo "\n";

