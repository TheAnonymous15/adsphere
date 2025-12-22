#!/usr/bin/env php
<?php
/**
 * Automated Scanner - For Cron Job
 * Run this via cron for automatic scanning
 *
 * Usage in crontab:
 *
 * # Every hour - incremental scan
 * 0 * * * * cd /path/to/adsphere/app && php scanner_cron.php incremental 1 >> /var/log/scanner.log 2>&1
 *
 * # Every 6 hours - incremental scan (6 hours window)
 * 0 */6 * * * cd /path/to/adsphere/app && php scanner_cron.php incremental 6 >> /var/log/scanner.log 2>&1
 *
 * # Daily at 3 AM - full day scan
 * 0 3 * * * cd /path/to/adsphere/app && php scanner_cron.php incremental 24 >> /var/log/scanner.log 2>&1
 *
 * # Weekly - priority scan
 * 0 2 * * 0 cd /path/to/adsphere/app && php scanner_cron.php priority 5000 >> /var/log/scanner.log 2>&1
 */

require_once __DIR__ . '/includes/HighPerformanceAdScanner.php';

$mode = $argv[1] ?? 'incremental';
$param = $argv[2] ?? 24;

echo "[" . date('Y-m-d H:i:s') . "] Starting scanner in '{$mode}' mode\n";

$scanner = new HighPerformanceAdScanner();

try {
    switch ($mode) {
        case 'incremental':
            $hours = (int)$param;
            echo "[" . date('Y-m-d H:i:s') . "] Scanning ads modified in last {$hours} hours\n";
            $results = $scanner->scanIncremental($hours);
            break;

        case 'priority':
            $limit = (int)$param;
            echo "[" . date('Y-m-d H:i:s') . "] Scanning top {$limit} priority ads\n";
            $results = $scanner->scanPriority($limit);
            break;

        default:
            echo "[" . date('Y-m-d H:i:s') . "] ERROR: Unknown mode '{$mode}'\n";
            exit(1);
    }

    // Log results
    echo "[" . date('Y-m-d H:i:s') . "] Scan complete:\n";
    echo "  - Scanned: {$results['total_scanned']} ads\n";
    echo "  - Clean: {$results['clean_ads']}\n";
    echo "  - Flagged: " . count($results['flagged_ads']) . "\n";
    echo "  - Cached skips: {$results['cached_skips']}\n";
    echo "  - Time: {$results['processing_time']}ms\n";

    if (count($results['flagged_ads']) > 0) {
        echo "  ⚠️  {$results['statistics']['critical']} critical, ";
        echo "{$results['statistics']['high']} high, ";
        echo "{$results['statistics']['medium']} medium violations\n";
    }

    echo "[" . date('Y-m-d H:i:s') . "] Done.\n\n";

} catch (Exception $e) {
    echo "[" . date('Y-m-d H:i:s') . "] ERROR: " . $e->getMessage() . "\n";
    exit(1);
}

