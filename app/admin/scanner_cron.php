#!/usr/bin/env php
<?php
/********************************************
 * Automated Scanner Cron Job
 * Run this script periodically to scan ads
 *
 * Usage:
 * php scanner_cron.php
 *
 * Add to crontab (runs every 15 minutes):
 * 15,30,45,0 * * * * php /path/to/scanner_cron.php
 ********************************************/

// Set time limit
set_time_limit(300); // 5 minutes max

// Change to script directory
chdir(__DIR__);

require_once __DIR__ . '/../includes/RealTimeAdScanner.php';

echo "===========================================\n";
echo "AdSphere Real-Time Scanner\n";
echo "Started: " . date('Y-m-d H:i:s') . "\n";
echo "===========================================\n\n";

try {
    $scanner = new RealTimeAdScanner();

    echo "Scanning all active ads...\n";
    $results = $scanner->scanAllAds();

    echo "\n";
    echo "===========================================\n";
    echo "SCAN RESULTS\n";
    echo "===========================================\n";
    echo "Total Scanned: " . $results['total_scanned'] . "\n";
    echo "Clean Ads: " . $results['clean_ads'] . "\n";
    echo "Flagged Ads: " . count($results['flagged_ads']) . "\n";
    echo "\n";
    echo "By Severity:\n";
    echo "  Critical: " . $results['statistics']['critical'] . "\n";
    echo "  High: " . $results['statistics']['high'] . "\n";
    echo "  Medium: " . $results['statistics']['medium'] . "\n";
    echo "  Low: " . $results['statistics']['low'] . "\n";
    echo "\n";
    echo "Processing Time: " . $results['processing_time'] . "\n";
    echo "===========================================\n\n";

    if (!empty($results['flagged_ads'])) {
        echo "FLAGGED ADS:\n";
        echo "-------------------------------------------\n";

        foreach ($results['flagged_ads'] as $ad) {
            echo "\n";
            echo "Ad ID: " . $ad['ad_id'] . "\n";
            echo "Title: " . $ad['title'] . "\n";
            echo "Company: " . $ad['company'] . "\n";
            echo "Severity: " . strtoupper($ad['severity_level']) . "\n";
            echo "AI Score: " . $ad['ai_score'] . "/100\n";
            echo "Action: " . strtoupper($ad['recommendation']['primary_action']) . "\n";
            echo "Urgency: " . strtoupper($ad['recommendation']['urgency']) . "\n";
            echo "Violations: " . implode(', ', $ad['violations']['content_issues']) . "\n";
            echo "-------------------------------------------\n";
        }
    }

    echo "\n";
    echo "Scan completed successfully!\n";
    echo "Report saved to: " . realpath(__DIR__ . '/../logs/scanner_reports_' . date('Y-m-d') . '.json') . "\n";
    echo "\n";

    exit(0);

} catch (Exception $e) {
    echo "\n";
    echo "ERROR: " . $e->getMessage() . "\n";
    echo "Trace: " . $e->getTraceAsString() . "\n";
    echo "\n";

    exit(1);
}

