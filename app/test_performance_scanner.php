#!/usr/bin/env php
<?php
/**
 * High-Performance Scanner Demo
 * Shows how to scan millions of ads efficiently
 */

echo "========================================\n";
echo "  High-Performance Ad Scanner Demo\n";
echo "  Optimized for Large Scale\n";
echo "========================================\n\n";

require_once __DIR__ . '/includes/HighPerformanceAdScanner.php';

$scanner = new HighPerformanceAdScanner();

// Show current statistics
echo "📊 Current Database Statistics:\n";
$stats = $scanner->getStatistics();
echo "   Total Active Ads: {$stats['total_active_ads']}\n";
echo "   Already Scanned: {$stats['scanned_ads']}\n";
echo "   Clean Ads: {$stats['clean_ads']}\n";
echo "   Flagged Ads: {$stats['flagged_ads']}\n";
echo "   Scan Coverage: {$stats['scan_coverage']}\n\n";

// Show available modes
echo "========================================\n";
echo "  Available Scan Modes\n";
echo "========================================\n\n";

echo "1. INCREMENTAL (Recommended for regular use)\n";
echo "   - Only scans new or modified ads\n";
echo "   - Uses smart caching\n";
echo "   - 100-1000x faster than full scan\n";
echo "   - Run this daily/hourly\n\n";

echo "2. PRIORITY (For focused security)\n";
echo "   - Scans high-risk ads first\n";
echo "   - Flagged ads, new uploads\n";
echo "   - Useful for immediate threats\n\n";

echo "3. BATCH (For specific ads)\n";
echo "   - Process specific subset\n";
echo "   - Controlled load\n\n";

// Menu
echo "========================================\n";
echo "Select scan mode:\n";
echo "  1) Incremental (last 24 hours)\n";
echo "  2) Incremental (last 1 hour)\n";
echo "  3) Priority (top 100 risky ads)\n";
echo "  4) Show statistics only\n";
echo "  5) Clear cache (force full rescan)\n";
echo "========================================\n";
echo "Choice [1-5]: ";

$choice = trim(fgets(STDIN));

echo "\n";

switch ($choice) {
    case '1':
        echo "🔄 Running Incremental Scan (24 hours)...\n\n";
        $results = $scanner->scanIncremental(24);
        displayResults($results);
        break;

    case '2':
        echo "🔄 Running Incremental Scan (1 hour)...\n\n";
        $results = $scanner->scanIncremental(1);
        displayResults($results);
        break;

    case '3':
        echo "🎯 Running Priority Scan (100 ads)...\n\n";
        $results = $scanner->scanPriority(100);
        displayResults($results);
        break;

    case '4':
        echo "📊 Statistics:\n";
        $stats = $scanner->getStatistics();
        print_r($stats);
        break;

    case '5':
        echo "⚠️  This will clear the cache and force rescan of all ads.\n";
        echo "Are you sure? [y/N]: ";
        $confirm = trim(fgets(STDIN));
        if (strtolower($confirm) === 'y') {
            $scanner->clearCache();
        } else {
            echo "Cancelled.\n";
        }
        break;

    default:
        echo "❌ Invalid choice\n";
}

function displayResults($results) {
    echo "\n========================================\n";
    echo "  Scan Results\n";
    echo "========================================\n\n";

    echo "📊 Summary:\n";
    echo "   Mode: {$results['mode']}\n";
    echo "   Total Scanned: {$results['total_scanned']}\n";
    echo "   Clean Ads: {$results['clean_ads']}\n";
    echo "   Flagged Ads: " . count($results['flagged_ads']) . "\n";
    echo "   Cached Skips: {$results['cached_skips']}\n";
    echo "   Processing Time: {$results['processing_time']}ms\n\n";

    if (isset($results['batches_processed'])) {
        $adsPerSecond = $results['total_scanned'] / ($results['processing_time'] / 1000);
        echo "⚡ Performance:\n";
        echo "   Batches Processed: {$results['batches_processed']}\n";
        echo "   Speed: " . round($adsPerSecond, 2) . " ads/second\n\n";

        // Projection for 1 million ads
        if ($adsPerSecond > 0) {
            $timeFor1M = (1000000 / $adsPerSecond) / 60;
            echo "📈 Projection:\n";
            echo "   Time for 1 million ads: " . round($timeFor1M, 2) . " minutes\n\n";
        }
    }

    echo "🎯 By Severity:\n";
    echo "   Critical: {$results['statistics']['critical']}\n";
    echo "   High: {$results['statistics']['high']}\n";
    echo "   Medium: {$results['statistics']['medium']}\n";
    echo "   Low: {$results['statistics']['low']}\n\n";

    if (count($results['flagged_ads']) > 0) {
        echo "🚩 Flagged Ads (showing first 5):\n";
        $displayed = 0;
        foreach ($results['flagged_ads'] as $ad) {
            if ($displayed >= 5) break;
            echo "   - {$ad['title']} ({$ad['severity_level']})\n";
            $displayed++;
        }
        if (count($results['flagged_ads']) > 5) {
            $remaining = count($results['flagged_ads']) - 5;
            echo "   ... and {$remaining} more\n";
        }
    }

    echo "\n";
}

echo "\n========================================\n";
echo "  Performance Tips\n";
echo "========================================\n\n";

echo "For 1 MILLION ads:\n\n";

echo "✅ DO:\n";
echo "  • Use incremental mode daily\n";
echo "  • Only scans new/modified ads\n";
echo "  • Typical: 1000-5000 ads/day = 1-2 minutes\n\n";

echo "⚠️  DON'T:\n";
echo "  • Run full scan on all ads\n";
echo "  • Clear cache unnecessarily\n";
echo "  • Scan without caching\n\n";

echo "🚀 Best Practice:\n";
echo "  • Cron job: Incremental scan every hour\n";
echo "  • Manual: Priority scan when needed\n";
echo "  • Full scan: Once per week (off-peak)\n\n";

echo "Estimated Performance:\n";
echo "  • 1M ads, incremental (1% new): ~30 seconds\n";
echo "  • 1M ads, incremental (10% new): ~5 minutes\n";
echo "  • 1M ads, full scan: ~8-15 minutes (with caching)\n\n";

