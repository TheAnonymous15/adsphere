#!/usr/bin/env php
<?php
error_reporting(E_ALL);
ini_set('display_errors', 1);

echo "Testing High-Performance Scanner...\n\n";

try {
    require_once __DIR__ . '/includes/HighPerformanceAdScanner.php';
    echo "✅ Scanner loaded\n";

    $scanner = new HighPerformanceAdScanner();
    echo "✅ Scanner initialized\n\n";

    // Get statistics
    echo "📊 Getting statistics...\n";
    $stats = $scanner->getStatistics();
    echo "   Total Active Ads: {$stats['total_active_ads']}\n";
    echo "   Scanned Ads: {$stats['scanned_ads']}\n";
    echo "   Clean Ads: {$stats['clean_ads']}\n";
    echo "   Flagged Ads: {$stats['flagged_ads']}\n";
    echo "   Coverage: {$stats['scan_coverage']}\n\n";

    // Run incremental scan
    echo "🔄 Running incremental scan (24 hours)...\n\n";
    $start = microtime(true);
    $results = $scanner->scanIncremental(24);
    $elapsed = round((microtime(true) - $start) * 1000, 2);

    echo "✅ Scan complete!\n\n";
    echo "Results:\n";
    echo "   Mode: {$results['mode']}\n";
    echo "   Scanned: {$results['total_scanned']}\n";
    echo "   Clean: {$results['clean_ads']}\n";
    echo "   Flagged: " . count($results['flagged_ads']) . "\n";
    echo "   Skipped (cached): {$results['cached_skips']}\n";
    echo "   Time: {$elapsed}ms\n\n";

    if ($results['total_scanned'] > 0) {
        $speed = $results['total_scanned'] / ($elapsed / 1000);
        echo "⚡ Speed: " . round($speed, 2) . " ads/second\n";

        // Project for 1M ads
        $timeFor1M = (1000000 / $speed) / 60;
        echo "📈 Projection: 1 million ads in " . round($timeFor1M, 2) . " minutes\n\n";
    }

    // Show flagged ads
    if (count($results['flagged_ads']) > 0) {
        echo "🚩 Flagged Ads:\n";
        foreach ($results['flagged_ads'] as $ad) {
            echo "   - {$ad['title']} ({$ad['severity_level']})\n";
        }
    }

    echo "\n✅ Test passed!\n";

} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
    echo $e->getTraceAsString() . "\n";
    exit(1);
}

