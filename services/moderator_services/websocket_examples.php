<?php
/********************************************
 * WebSocket-First Integration Examples
 *
 * The moderation system now uses WebSocket as PRIMARY
 * for ALL endpoints, with REST as fallback.
 *
 * Benefits:
 * - Real-time progress updates
 * - Streaming responses
 * - Lower latency for long operations
 * - Better resource utilization
 ********************************************/

require_once __DIR__ . '/ModerationServiceClient.php';

/**
 * Example 1: Text Moderation (WebSocket Primary)
 * Even text uses WebSocket now for consistency
 */
function moderateText($title, $description, $category = 'general') {
    $client = new ModerationServiceClient();

    // Method auto-selects WebSocket (primary) or REST (fallback)
    $result = $client->processText(
        $title,
        $description,
        $category,
        'auto',
        [],
        function($progress) {
            // Progress callback (optional)
            echo "Text analysis: " . ($progress['data']['status'] ?? 'processing') . "\n";
        }
    );

    return $result;
}

/**
 * Example 2: Image Moderation (WebSocket Primary)
 */
function moderateImage($imagePath) {
    $client = new ModerationServiceClient();

    $result = $client->processImage(
        $imagePath,
        ['source' => 'upload'],
        function($progress) {
            $status = $progress['data']['status'] ?? 'scanning';
            echo "Image: {$status}\n";
        }
    );

    return $result;
}

/**
 * Example 3: Video Moderation with Progress (WebSocket Primary)
 * Best use case for WebSocket - long processing with updates
 */
function moderateVideoWithProgress($videoPath, $adId, $company) {
    $client = new ModerationServiceClient();

    $result = $client->processVideo(
        $videoPath,
        null,  // videoUrl
        ['ad_id' => $adId, 'company' => $company],
        ['fps' => 2, 'max_duration' => 60],
        function($progress) {
            // Real-time progress updates via WebSocket
            $frame = $progress['data']['frame'] ?? 0;
            $total = $progress['data']['total_frames'] ?? 100;
            $percent = round(($frame / max($total, 1)) * 100);
            $status = $progress['data']['status'] ?? 'Processing';

            echo "\r[{$percent}%] {$status} - Frame {$frame}/{$total}";

            // For web: Send via Server-Sent Events or save to session
            // header('Content-Type: text/event-stream');
            // echo "data: " . json_encode(['percent' => $percent]) . "\n\n";
            // flush();
        }
    );

    echo "\nDone!\n";
    return $result;
}

/**
 * Example 4: Realtime Ad Scanner with Progress (WebSocket Primary)
 * Streams progress for each ad scanned
 */
function scanAdsWithProgress($mode = 'incremental', $limit = 100) {
    $client = new ModerationServiceClient();

    $scannedCount = 0;
    $flaggedCount = 0;

    $result = $client->realtimeScanner(
        $mode,
        null,  // adId
        null,  // companyId
        null,  // category
        $limit,
        true,  // skipCached
        function($progress) use (&$scannedCount, &$flaggedCount) {
            $scannedCount++;
            $adId = $progress['data']['ad_id'] ?? 'unknown';
            $decision = $progress['data']['decision'] ?? 'approve';

            if ($decision !== 'approve') {
                $flaggedCount++;
                echo "⚠️ ";
            } else {
                echo "✅ ";
            }

            echo "Scanned: {$adId} -> {$decision}\n";
        }
    );

    echo "\n=== Scan Complete ===\n";
    echo "Total: {$scannedCount}, Flagged: {$flaggedCount}\n";

    return $result;
}

/**
 * Example 5: Combined Ad Upload Moderation
 * Full ad moderation with text + images via WebSocket
 */
function moderateAdUpload($title, $description, $imagePaths, $category, $context) {
    $client = new ModerationServiceClient();

    echo "🔄 Moderating ad upload via WebSocket...\n";

    $result = $client->moderateRealtime(
        $title,
        $description,
        $imagePaths,  // imageUrls
        [],           // videoUrls
        array_merge($context, ['category' => $category]),
        function($progress) {
            $step = $progress['data']['step'] ?? 'processing';
            echo "  → {$step}\n";
        }
    );

    $decision = $result['decision'] ?? 'unknown';
    echo "✅ Decision: {$decision}\n";

    return $result;
}

/**
 * Example 6: Check Connection Status
 */
function checkStatus() {
    $client = new ModerationServiceClient();

    echo "=== Moderation Service Status ===\n\n";

    $status = $client->getConnectionStatus();

    echo "WebSocket (PRIMARY):\n";
    echo "  Available: " . ($status['websocket']['available'] ? "✅ Yes" : "❌ No") . "\n";
    echo "  URL: " . $status['websocket']['url'] . "\n\n";

    echo "REST API (FALLBACK):\n";
    echo "  Available: " . ($status['rest']['available'] ? "✅ Yes" : "❌ No") . "\n";
    echo "  URL: " . $status['rest']['url'] . "\n\n";

    echo "Current Method: " . $client->getPreferredMethod('any') . "\n";

    return $status;
}

/**
 * Example 7: Batch Scan Multiple Ads
 */
function batchScanAds($adIds) {
    $client = new ModerationServiceClient();

    echo "🔄 Batch scanning " . count($adIds) . " ads via WebSocket...\n";

    $result = $client->streamBatchScan(
        $adIds,
        function($progress) {
            $adId = $progress['data']['ad_id'] ?? '';
            $decision = $progress['data']['decision'] ?? 'processing';
            echo "  [{$adId}] {$decision}\n";
        }
    );

    return $result;
}

// ============================================
// RUN EXAMPLES IF CALLED DIRECTLY
// ============================================
if (php_sapi_name() === 'cli' && basename(__FILE__) === basename($argv[0])) {
    echo "╔══════════════════════════════════════════════════════════════╗\n";
    echo "║       WebSocket-First Moderation System                      ║\n";
    echo "║       All endpoints use WebSocket as PRIMARY                 ║\n";
    echo "║       REST API is only used as FALLBACK                      ║\n";
    echo "╚══════════════════════════════════════════════════════════════╝\n\n";

    checkStatus();
}

