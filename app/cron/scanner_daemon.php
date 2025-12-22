tri#!/usr/bin/env php
<?php
/********************************************
 * Background Scanner Daemon
 *
 * Runs continuously in the background, scanning ads in real-time.
 *
 * Usage:
 *   # Start daemon
 *   php scanner_daemon.php start
 *
 *   # Start in background (daemon mode)
 *   php scanner_daemon.php start --daemon
 *
 *   # Stop daemon
 *   php scanner_daemon.php stop
 *
 *   # Check status
 *   php scanner_daemon.php status
 *
 *   # Restart
 *   php scanner_daemon.php restart
 *
 * Configuration:
 *   SCAN_INTERVAL=30        # Seconds between scans
 *   SCAN_BATCH_SIZE=50      # Ads per scan cycle
 *   USE_REMOTE_SERVICE=true # Use Python service
 *
 ********************************************/

// Ensure running from CLI
if (php_sapi_name() !== 'cli') {
    die("This script can only be run from command line\n");
}

// Configuration
define('PID_FILE', sys_get_temp_dir() . '/adsphere_scanner_daemon.pid');
define('LOG_FILE', dirname(__DIR__) . '/logs/scanner_daemon.log');
define('SCAN_INTERVAL', getenv('SCAN_INTERVAL') ?: 30);
define('SCAN_BATCH_SIZE', getenv('SCAN_BATCH_SIZE') ?: 50);

// Set working directory
chdir(dirname(__DIR__));

// Parse command
$command = $argv[1] ?? 'help';
$isDaemon = in_array('--daemon', $argv) || in_array('-d', $argv);

// Logging function
function logMessage($message, $level = 'INFO') {
    $timestamp = date('Y-m-d H:i:s');
    $formatted = "[{$timestamp}] [{$level}] {$message}\n";

    // Write to log file
    $logDir = dirname(LOG_FILE);
    if (!is_dir($logDir)) {
        mkdir($logDir, 0755, true);
    }
    file_put_contents(LOG_FILE, $formatted, FILE_APPEND | LOCK_EX);

    // Also output to console if not daemon
    if (!defined('DAEMON_MODE') || !DAEMON_MODE) {
        echo $formatted;
    }
}

// Get daemon PID
function getDaemonPid() {
    if (file_exists(PID_FILE)) {
        $pid = (int) file_get_contents(PID_FILE);

        // Check if process is still running
        if (posix_kill($pid, 0)) {
            return $pid;
        }

        // Process not running, remove stale PID file
        unlink(PID_FILE);
    }
    return null;
}

// Start the daemon
function startDaemon($daemon = false) {
    // Check if already running
    $pid = getDaemonPid();
    if ($pid) {
        echo "Scanner daemon is already running (PID: {$pid})\n";
        exit(1);
    }

    // Fork to background if daemon mode
    if ($daemon) {
        $pid = pcntl_fork();

        if ($pid < 0) {
            die("Failed to fork process\n");
        }

        if ($pid > 0) {
            // Parent process
            echo "Scanner daemon started in background (PID: {$pid})\n";
            exit(0);
        }

        // Child process - become session leader
        posix_setsid();
        define('DAEMON_MODE', true);

        // Close standard file descriptors
        fclose(STDIN);
        fclose(STDOUT);
        fclose(STDERR);

        // Reopen to /dev/null
        $GLOBALS['STDIN'] = fopen('/dev/null', 'r');
        $GLOBALS['STDOUT'] = fopen('/dev/null', 'w');
        $GLOBALS['STDERR'] = fopen('/dev/null', 'w');
    }

    // Save PID
    file_put_contents(PID_FILE, getmypid());

    // Register signal handlers
    if (function_exists('pcntl_signal')) {
        pcntl_signal(SIGTERM, 'signalHandler');
        pcntl_signal(SIGINT, 'signalHandler');
        pcntl_signal(SIGHUP, 'signalHandler');
    }

    logMessage("Scanner daemon starting (PID: " . getmypid() . ")");
    logMessage("Scan interval: " . SCAN_INTERVAL . " seconds");
    logMessage("Batch size: " . SCAN_BATCH_SIZE);

    // Run the main loop
    runMainLoop();
}

// Signal handler
function signalHandler($signal) {
    switch ($signal) {
        case SIGTERM:
        case SIGINT:
            logMessage("Received shutdown signal ({$signal})", 'WARN');
            cleanup();
            exit(0);

        case SIGHUP:
            logMessage("Received SIGHUP, reloading configuration", 'INFO');
            break;
    }
}

// Cleanup function
function cleanup() {
    if (file_exists(PID_FILE)) {
        unlink(PID_FILE);
    }
    logMessage("Scanner daemon stopped");
}

// Main scanning loop
function runMainLoop() {
    // Include scanner
    require_once __DIR__ . '/../includes/RealTimeAdScanner.php';

    $scanner = new HighPerformanceAdScanner();
    $cycleCount = 0;
    $totalScanned = 0;
    $totalFlagged = 0;
    $startTime = time();

    logMessage("Main loop started, entering continuous scanning mode");

    // Check if remote service is available
    if ($scanner->isRemoteServiceAvailable()) {
        logMessage("Using remote Python moderation service");

        // Start background scanner on Python service
        $backgroundScanner = $scanner->startBackgroundScanner();
        if ($backgroundScanner && isset($backgroundScanner['scanner_id'])) {
            logMessage("Started remote background scanner: " . $backgroundScanner['scanner_id']);
        }
    } else {
        logMessage("Remote service not available, using local scanning", 'WARN');
    }

    while (true) {
        $cycleStart = microtime(true);
        $cycleCount++;

        // Process signals
        if (function_exists('pcntl_signal_dispatch')) {
            pcntl_signal_dispatch();
        }

        try {
            // Run incremental scan
            logMessage("Starting scan cycle #{$cycleCount}");

            $results = $scanner->scanIncremental(1); // Last 1 hour

            $scanned = $results['total_scanned'] ?? 0;
            $flagged = count($results['flagged_ads'] ?? []);

            $totalScanned += $scanned;
            $totalFlagged += $flagged;

            $cycleTime = round((microtime(true) - $cycleStart) * 1000, 2);

            logMessage("Cycle #{$cycleCount} complete: {$scanned} scanned, {$flagged} flagged, {$cycleTime}ms");

            // Report flagged ads immediately
            if (!empty($results['flagged_ads'])) {
                foreach ($results['flagged_ads'] as $ad) {
                    $severity = $ad['severity_level'] ?? $ad['risk_level'] ?? 'unknown';
                    logMessage("FLAGGED [{$severity}]: {$ad['ad_id']} - {$ad['title']}", 'WARN');
                }
            }

            // Periodic statistics (every 10 cycles)
            if ($cycleCount % 10 === 0) {
                $runtime = time() - $startTime;
                $avgRate = $runtime > 0 ? round($totalScanned / $runtime, 2) : 0;

                logMessage("=== STATISTICS (Cycle #{$cycleCount}) ===");
                logMessage("Runtime: " . formatDuration($runtime));
                logMessage("Total scanned: {$totalScanned} ads");
                logMessage("Total flagged: {$totalFlagged} ads");
                logMessage("Average rate: {$avgRate} ads/sec");

                // Get system statistics
                $stats = $scanner->getStatistics();
                logMessage("DB Stats: " . json_encode($stats));
            }

        } catch (Exception $e) {
            logMessage("Scan error: " . $e->getMessage(), 'ERROR');
        }

        // Sleep until next cycle
        $sleepTime = max(1, SCAN_INTERVAL - (microtime(true) - $cycleStart));
        logMessage("Sleeping for {$sleepTime} seconds until next cycle");
        sleep((int) $sleepTime);
    }
}

// Format duration
function formatDuration($seconds) {
    $hours = floor($seconds / 3600);
    $minutes = floor(($seconds % 3600) / 60);
    $secs = $seconds % 60;

    return sprintf("%02d:%02d:%02d", $hours, $minutes, $secs);
}

// Stop the daemon
function stopDaemon() {
    $pid = getDaemonPid();

    if (!$pid) {
        echo "Scanner daemon is not running\n";
        exit(1);
    }

    echo "Stopping scanner daemon (PID: {$pid})...\n";

    // Send SIGTERM
    posix_kill($pid, SIGTERM);

    // Wait for process to exit
    $timeout = 10;
    while ($timeout > 0 && posix_kill($pid, 0)) {
        sleep(1);
        $timeout--;
    }

    if (posix_kill($pid, 0)) {
        echo "Daemon did not stop gracefully, sending SIGKILL...\n";
        posix_kill($pid, SIGKILL);
        sleep(1);
    }

    if (file_exists(PID_FILE)) {
        unlink(PID_FILE);
    }

    echo "Scanner daemon stopped\n";
}

// Show daemon status
function showStatus() {
    $pid = getDaemonPid();

    if ($pid) {
        echo "Scanner daemon is running (PID: {$pid})\n";

        // Show recent log entries
        if (file_exists(LOG_FILE)) {
            echo "\nRecent log entries:\n";
            echo str_repeat('-', 60) . "\n";
            $lines = file(LOG_FILE);
            $recentLines = array_slice($lines, -20);
            foreach ($recentLines as $line) {
                echo $line;
            }
        }

        exit(0);
    } else {
        echo "Scanner daemon is not running\n";
        exit(1);
    }
}

// Main command handler
switch ($command) {
    case 'start':
        startDaemon($isDaemon);
        break;

    case 'stop':
        stopDaemon();
        break;

    case 'restart':
        stopDaemon();
        sleep(2);
        startDaemon($isDaemon);
        break;

    case 'status':
        showStatus();
        break;

    case 'help':
    default:
        echo "AdSphere Scanner Daemon\n";
        echo "=======================\n\n";
        echo "Usage: php scanner_daemon.php <command> [options]\n\n";
        echo "Commands:\n";
        echo "  start [--daemon]  Start the scanner (--daemon for background)\n";
        echo "  stop              Stop the scanner daemon\n";
        echo "  restart           Restart the scanner daemon\n";
        echo "  status            Show daemon status\n";
        echo "  help              Show this help message\n\n";
        echo "Environment variables:\n";
        echo "  SCAN_INTERVAL     Seconds between scans (default: 30)\n";
        echo "  SCAN_BATCH_SIZE   Ads per scan cycle (default: 50)\n\n";
        echo "Examples:\n";
        echo "  php scanner_daemon.php start           # Run in foreground\n";
        echo "  php scanner_daemon.php start --daemon  # Run in background\n";
        echo "  php scanner_daemon.php status          # Check if running\n";
        exit(0);
}

