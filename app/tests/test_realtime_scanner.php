<?php
/********************************************
 * Real-Time Ad Scanner Test
 * Tests the scanner against actual database ads
 * Generates comprehensive moderation report
 ********************************************/

error_reporting(E_ALL);
ini_set('display_errors', 1);

require_once __DIR__ . '/includes/RealTimeAdScanner.php';

echo "╔══════════════════════════════════════════════════════════════════════════════╗\n";
echo "║                    🔍 REAL-TIME AD SCANNER TEST                              ║\n";
echo "╚══════════════════════════════════════════════════════════════════════════════╝\n\n";

// Initialize scanner
echo "1. Initializing Real-Time Ad Scanner...\n";
$scanner = new RealTimeAdScanner();

// Check ML service status
$serviceStatus = $scanner->getServiceStatus();
echo "   ML Service Status:\n";
echo "   └─ Available: " . ($serviceStatus['new_service_available'] ? '✅ Yes' : '❌ No') . "\n";
echo "   └─ Backend: {$serviceStatus['backend']}\n";
echo "   └─ Version: {$serviceStatus['version']}\n\n";

// Run the scan
echo "2. Scanning all active ads in database...\n";
echo "   ⏳ This may take a moment...\n\n";

$startTime = microtime(true);
$scanResults = $scanner->scanAllAds();
$totalTime = round((microtime(true) - $startTime) * 1000, 2);

echo "═══════════════════════════════════════════════════════════════════════════════\n";
echo "                           📊 SCAN RESULTS SUMMARY\n";
echo "═══════════════════════════════════════════════════════════════════════════════\n\n";

// Overall statistics
echo "🕐 Scan Time: {$scanResults['scan_time']}\n";
echo "⚡ Processing Time: {$totalTime}ms\n";
echo "📊 Total Ads Scanned: {$scanResults['total_scanned']}\n";
echo "✅ Clean Ads: {$scanResults['clean_ads']}\n";
echo "🚩 Flagged Ads: " . count($scanResults['flagged_ads']) . "\n\n";

// Severity breakdown
echo "═══════════════════════════════════════════════════════════════════════════════\n";
echo "                          🎯 SEVERITY BREAKDOWN\n";
echo "═══════════════════════════════════════════════════════════════════════════════\n\n";

$stats = $scanResults['statistics'];
echo "🔴 CRITICAL: {$stats['critical']}\n";
echo "🟠 HIGH:     {$stats['high']}\n";
echo "🟡 MEDIUM:   {$stats['medium']}\n";
echo "🟢 LOW:      {$stats['low']}\n\n";

// Calculate percentages
if ($scanResults['total_scanned'] > 0) {
    $cleanPercent = round(($scanResults['clean_ads'] / $scanResults['total_scanned']) * 100, 1);
    $flaggedPercent = round((count($scanResults['flagged_ads']) / $scanResults['total_scanned']) * 100, 1);

    echo "📈 Clean Rate: {$cleanPercent}%\n";
    echo "📉 Violation Rate: {$flaggedPercent}%\n\n";
}

// Detailed flagged ads
if (!empty($scanResults['flagged_ads'])) {
    echo "═══════════════════════════════════════════════════════════════════════════════\n";
    echo "                        🚨 FLAGGED ADS DETAILS\n";
    echo "═══════════════════════════════════════════════════════════════════════════════\n\n";

    foreach ($scanResults['flagged_ads'] as $index => $flaggedAd) {
        $num = $index + 1;
        $severityIcon = [
            'critical' => '🔴',
            'high' => '🟠',
            'medium' => '🟡',
            'low' => '🟢'
        ][$flaggedAd['severity_level']] ?? '⚪';

        echo "───────────────────────────────────────────────────────────────────────────────\n";
        echo "FLAGGED AD #{$num}\n";
        echo "───────────────────────────────────────────────────────────────────────────────\n\n";

        echo "📋 Ad ID: {$flaggedAd['ad_id']}\n";
        echo "📝 Title: {$flaggedAd['title']}\n";
        echo "📄 Description: {$flaggedAd['description']}\n";
        echo "🏢 Company: {$flaggedAd['company']} ({$flaggedAd['company_slug']})\n";
        echo "📧 Email: {$flaggedAd['company_email']}\n";
        echo "🏷️  Category: {$flaggedAd['category']}\n";
        echo "📅 Created: " . date('Y-m-d H:i:s', (int)$flaggedAd['created_at']) . "\n\n";

        echo "{$severityIcon} Severity: " . strtoupper($flaggedAd['severity_level']) . "\n";
        echo "🤖 AI Score: {$flaggedAd['ai_score']}/100\n";
        echo "⚠️  Risk Level: {$flaggedAd['risk_level']}\n\n";

        // Violations
        echo "🚫 VIOLATIONS:\n";

        if (!empty($flaggedAd['violations']['content_issues'])) {
            echo "   Content Issues:\n";
            foreach ($flaggedAd['violations']['content_issues'] as $issue) {
                echo "   • {$issue}\n";
            }
        }

        if (!empty($flaggedAd['violations']['warnings'])) {
            echo "   Warnings:\n";
            foreach ($flaggedAd['violations']['warnings'] as $warning) {
                echo "   • {$warning}\n";
            }
        }

        if (!empty($flaggedAd['violations']['pattern_flags'])) {
            echo "   Pattern Flags:\n";
            foreach ($flaggedAd['violations']['pattern_flags'] as $flag) {
                echo "   • {$flag}\n";
            }
        }

        if (!empty($flaggedAd['violations']['copyright_concerns'])) {
            echo "   Copyright Concerns:\n";
            foreach ($flaggedAd['violations']['copyright_concerns'] as $concern) {
                echo "   • {$concern}\n";
            }
        }

        echo "\n";

        // ML Audit Data
        if (isset($flaggedAd['ml_audit'])) {
            echo "🤖 ML AUDIT DATA:\n";
            echo "   Audit ID: {$flaggedAd['ml_audit']['audit_id']}\n";
            echo "   Decision: {$flaggedAd['ml_audit']['decision']}\n";
            echo "   Global Score: {$flaggedAd['ml_audit']['global_score']}/100\n";

            if (!empty($flaggedAd['ml_audit']['category_scores'])) {
                echo "   Category Scores:\n";
                $topScores = array_filter($flaggedAd['ml_audit']['category_scores'], function($v) {
                    return $v > 0.1;
                });
                arsort($topScores);

                foreach (array_slice($topScores, 0, 5, true) as $category => $score) {
                    $percent = round($score * 100, 1);
                    echo "      - {$category}: {$percent}%\n";
                }
            }

            if (!empty($flaggedAd['ml_audit']['ai_models_used'])) {
                echo "   AI Models Used: " . implode(', ', $flaggedAd['ml_audit']['ai_models_used']) . "\n";
            }

            echo "   Processing Time: {$flaggedAd['ml_audit']['processing_time']}ms\n\n";
        }

        // Recommendations
        $rec = $flaggedAd['recommendation'];
        echo "💡 RECOMMENDATION:\n";
        echo "   Primary Action: " . strtoupper($rec['primary_action']) . "\n";
        echo "   Urgency: " . strtoupper($rec['urgency']) . "\n\n";

        if (!empty($rec['reasoning'])) {
            echo "   Reasoning:\n";
            foreach ($rec['reasoning'] as $reason) {
                echo "   • {$reason}\n";
            }
            echo "\n";
        }

        if (!empty($rec['violation_details'])) {
            echo "   Violation Details:\n";
            foreach ($rec['violation_details'] as $detail) {
                echo "   • {$detail}\n";
            }
            echo "\n";
        }

        echo "   Suggested Message to Company:\n";
        echo "   ┌─────────────────────────────────────────────────────────────────────┐\n";
        $lines = explode("\n", $rec['suggested_message']);
        foreach ($lines as $line) {
            echo "   │ " . str_pad($line, 69) . "│\n";
        }
        echo "   └─────────────────────────────────────────────────────────────────────┘\n\n";
    }
}

// Performance metrics
echo "═══════════════════════════════════════════════════════════════════════════════\n";
echo "                         ⚡ PERFORMANCE METRICS\n";
echo "═══════════════════════════════════════════════════════════════════════════════\n\n";

if ($scanResults['total_scanned'] > 0) {
    $avgTime = round($totalTime / $scanResults['total_scanned'], 2);
    $adsPerSecond = round($scanResults['total_scanned'] / ($totalTime / 1000), 2);

    echo "⏱️  Total Time: {$totalTime}ms\n";
    echo "📊 Average Time per Ad: {$avgTime}ms\n";
    echo "🚀 Throughput: {$adsPerSecond} ads/second\n\n";

    // Projection for large scale
    if ($scanResults['total_scanned'] > 0) {
        $timeFor1000 = round(($avgTime * 1000) / 1000, 2);
        $timeFor1M = round(($avgTime * 1000000) / 60000, 2);

        echo "📈 Projections:\n";
        echo "   • 1,000 ads: ~{$timeFor1000} seconds\n";
        echo "   • 1,000,000 ads: ~{$timeFor1M} minutes\n\n";
    }
}

// System health check
echo "═══════════════════════════════════════════════════════════════════════════════\n";
echo "                         🏥 SYSTEM HEALTH CHECK\n";
echo "═══════════════════════════════════════════════════════════════════════════════\n\n";

$health = [];

// Check ML service
$health['ml_service'] = $serviceStatus['new_service_available'] ? '✅ Operational' : '⚠️  Degraded (Using Fallback)';

// Check violation rate
$violationRate = $scanResults['total_scanned'] > 0
    ? (count($scanResults['flagged_ads']) / $scanResults['total_scanned']) * 100
    : 0;

if ($violationRate > 50) {
    $health['content_quality'] = '🔴 Critical (>50% violations)';
} elseif ($violationRate > 25) {
    $health['content_quality'] = '🟡 Warning (>25% violations)';
} else {
    $health['content_quality'] = '✅ Good';
}

// Check for critical violations
if ($stats['critical'] > 0) {
    $health['critical_threats'] = "🔴 {$stats['critical']} critical violation(s) detected";
} else {
    $health['critical_threats'] = '✅ No critical threats';
}

foreach ($health as $component => $status) {
    $label = ucwords(str_replace('_', ' ', $component));
    echo "{$label}: {$status}\n";
}

echo "\n";

// Recommendations
echo "═══════════════════════════════════════════════════════════════════════════════\n";
echo "                      📋 SYSTEM RECOMMENDATIONS\n";
echo "═══════════════════════════════════════════════════════════════════════════════\n\n";

$recommendations = [];

if ($stats['critical'] > 0) {
    $recommendations[] = "🔴 URGENT: Review {$stats['critical']} critical violation(s) immediately";
}

if ($stats['high'] > 0) {
    $recommendations[] = "🟠 Review {$stats['high']} high-severity violation(s) within 24 hours";
}

if ($violationRate > 25) {
    $recommendations[] = "⚠️  High violation rate ({$violationRate}%) - Consider stricter upload validation";
}

if (!$serviceStatus['new_service_available']) {
    $recommendations[] = "⚠️  ML service unavailable - Restart moderation service for better accuracy";
}

if (empty($recommendations)) {
    echo "✅ No immediate action required. System is operating normally.\n\n";
} else {
    foreach ($recommendations as $i => $rec) {
        echo ($i + 1) . ". {$rec}\n";
    }
    echo "\n";
}

// Report location
echo "═══════════════════════════════════════════════════════════════════════════════\n";
echo "                           📄 REPORT SAVED\n";
echo "═══════════════════════════════════════════════════════════════════════════════\n\n";

$reportPath = __DIR__ . '/logs/scanner_reports_' . date('Y-m-d') . '.json';
echo "📁 Location: {$reportPath}\n";
echo "📊 Format: JSON\n";
echo "🔍 View in dashboard: /admin/admin_dashboard.php (Violations Tab)\n\n";

// Final summary
echo "═══════════════════════════════════════════════════════════════════════════════\n";
echo "                         ✅ SCAN COMPLETE\n";
echo "═══════════════════════════════════════════════════════════════════════════════\n\n";

if (count($scanResults['flagged_ads']) > 0) {
    echo "⚠️  {$scanResults['total_scanned']} ads scanned, " . count($scanResults['flagged_ads']) . " violations detected.\n";
    echo "📊 Please review flagged ads in the admin dashboard.\n\n";
} else {
    echo "✅ All {$scanResults['total_scanned']} ads passed moderation checks!\n\n";
}

// Export summary to file
$summaryFile = __DIR__ . '/test_scanner_summary.txt';
ob_start();
echo "REAL-TIME AD SCANNER TEST SUMMARY\n";
echo "Generated: " . date('Y-m-d H:i:s') . "\n";
echo str_repeat('=', 80) . "\n\n";
echo "Total Ads Scanned: {$scanResults['total_scanned']}\n";
echo "Clean Ads: {$scanResults['clean_ads']}\n";
echo "Flagged Ads: " . count($scanResults['flagged_ads']) . "\n\n";
echo "SEVERITY BREAKDOWN:\n";
echo "  Critical: {$stats['critical']}\n";
echo "  High: {$stats['high']}\n";
echo "  Medium: {$stats['medium']}\n";
echo "  Low: {$stats['low']}\n\n";

if (!empty($scanResults['flagged_ads'])) {
    echo "FLAGGED ADS:\n\n";
    foreach ($scanResults['flagged_ads'] as $i => $ad) {
        echo ($i + 1) . ". {$ad['title']} (ID: {$ad['ad_id']})\n";
        echo "   Company: {$ad['company']}\n";
        echo "   Severity: {$ad['severity_level']}\n";
        echo "   AI Score: {$ad['ai_score']}/100\n";
        echo "   Action: {$ad['recommendation']['primary_action']}\n\n";
    }
}

echo "\nFull JSON report: {$reportPath}\n";
$summary = ob_get_clean();
file_put_contents($summaryFile, $summary);

echo "💾 Summary also saved to: {$summaryFile}\n\n";

