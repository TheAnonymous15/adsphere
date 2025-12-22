#!/usr/bin/env php
<?php
/********************************************
 * Scanner Cron Job
 *
 * Schedule this script to run periodically via crontab:
 *
 * # Every 5 minutes (recommended for high-traffic sites)
 * */5 * * * * /usr/bin/php /path/to/scanner_cron.php incremental >> /var/log/scanner.log 2>&1
 *
 * # Every hour (for medium-traffic sites)
 * 0 * * * * /usr/bin/php /path/to/scanner_cron.php incremental >> /var/log/scanner.log 2>&1
 *
 * # Daily full scan at 3 AM
 * 0 3 * * * /usr/bin/php /path/to/scanner_cron.php full >> /var/log/scanner.log 2>&1
 *
 * # Priority scan every 15 minutes
 * */15 * * * * /usr/bin/php /path/to/scanner_cron.php priority >> /var/log/scanner.log 2>&1
 *
 ********************************************/

// Ensure running from CLI
if (php_sapi_name() !== 'cli') {
    die("This script can only be run from command line\n");
}

// Set working directory
chdir(dirname(__DIR__));

// Include scanner
require_once __DIR__ . '/../includes/RealTimeAdScanner.php';

// Parse arguments
$mode = $argv[1] ?? 'incremental';
$limit = isset($argv[2]) ? (int)$argv[2] : 1000;

// Lock file to prevent concurrent runs
$lockFile = sys_get_temp_dir() . '/adsphere_scanner.lock';

// Check if already running
if (file_exists($lockFile)) {
    $lockTime = filemtime($lockFile);
    $lockAge = time() - $lockTime;

    // If lock is older than 30 minutes, consider it stale
    if ($lockAge < 1800) {
        echo "[" . date('Y-m-d H:i:s') . "] Scanner already running (lock age: {$lockAge}s). Skipping.\n";
        exit(0);
    }

    echo "[" . date('Y-m-d H:i:s') . "] Removing stale lock file (age: {$lockAge}s)\n";
    unlink($lockFile);
}

// Create lock file
file_put_contents($lockFile, getmypid());

// Register shutdown function to clean up lock
register_shutdown_function(function() use ($lockFile) {
    if (file_exists($lockFile)) {
        unlink($lockFile);
    }
});

// Handle signals for graceful shutdown
if (function_exists('pcntl_signal')) {
    pcntl_signal(SIGTERM, function() use ($lockFile) {
        echo "\n[" . date('Y-m-d H:i:s') . "] Received SIGTERM, shutting down gracefully...\n";
        if (file_exists($lockFile)) {
            unlink($lockFile);
        }
        exit(0);
    });
    pcntl_signal(SIGINT, function() use ($lockFile) {
        echo "\n[" . date('Y-m-d H:i:s') . "] Received SIGINT, shutting down gracefully...\n";
        if (file_exists($lockFile)) {
            unlink($lockFile);
        }
        exit(0);
    });
}

echo "╔══════════════════════════════════════════════════════════════╗\n";
echo "║           AdSphere Real-Time Ad Scanner                      ║\n";
echo "╠══════════════════════════════════════════════════════════════╣\n";
echo "║  Mode: " . str_pad($mode, 53) . "║\n";
echo "║  Limit: " . str_pad($limit, 52) . "║\n";
echo "║  Time: " . str_pad(date('Y-m-d H:i:s'), 53) . "║\n";
echo "╚══════════════════════════════════════════════════════════════╝\n\n";

try {
    $scanner = new HighPerformanceAdScanner();

    // Check service health
    $health = $scanner->getServiceHealth();
    echo "🏥 Service Health: " . ($health['status'] ?? 'unknown') . "\n\n";

    // Run scan based on mode
    switch ($mode) {
        case 'incremental':
            $results = $scanner->scanIncremental(24); // Last 24 hours
            break;

        case 'priority':
            $results = $scanner->scanPriority($limit);
            break;

        case 'full':
            $results = $scanner->scanFull($limit);
            break;

        default:
            echo "Unknown mode: {$mode}\n";
            echo "Usage: scanner_cron.php [incremental|priority|full] [limit]\n";
            exit(1);
    }

    // Print summary
    echo "\n╔══════════════════════════════════════════════════════════════╗\n";
    echo "║                      SCAN SUMMARY                            ║\n";
    echo "╠══════════════════════════════════════════════════════════════╣\n";
    echo "║  Total Scanned: " . str_pad($results['total_scanned'] ?? 0, 44) . "║\n";
    echo "║  Clean Ads: " . str_pad($results['clean_ads'] ?? 0, 48) . "║\n";
    echo "║  Flagged Ads: " . str_pad(count($results['flagged_ads'] ?? []), 46) . "║\n";
    echo "║  Processing Time: " . str_pad(($results['processing_time'] ?? 0) . ' ms', 42) . "║\n";

    if (!empty($results['ads_per_second'])) {
        echo "║  Speed: " . str_pad($results['ads_per_second'] . ' ads/sec', 52) . "║\n";
    }

    echo "╚══════════════════════════════════════════════════════════════╝\n";

    // Report flagged ads
    if (!empty($results['flagged_ads'])) {
        echo "\n⚠️  FLAGGED ADS:\n";
        echo str_repeat('-', 60) . "\n";

        foreach ($results['flagged_ads'] as $ad) {
            $severity = $ad['severity_level'] ?? $ad['risk_level'] ?? 'unknown';
            $icon = match($severity) {
                'critical' => '🔴',
                'high' => '🟠',
                'medium' => '🟡',
                'low' => '🟢',
                default => '⚪'
            };

            echo "{$icon} [{$severity}] {$ad['ad_id']} - {$ad['title']}\n";
            echo "   Company: {$ad['company']}\n";
            echo "   Action: " . ($ad['suggested_action'] ?? 'review') . "\n";

            if (!empty($ad['violations']['issues'])) {
                echo "   Issues: " . implode(', ', $ad['violations']['issues']) . "\n";
            }
            echo "\n";
        }
    }

    echo "\n✅ Scan completed at " . date('Y-m-d H:i:s') . "\n";

} catch (Exception $e) {
    echo "❌ Scanner error: " . $e->getMessage() . "\n";
    echo "Stack trace:\n" . $e->getTraceAsString() . "\n";
    exit(1);
}

exit(0);

