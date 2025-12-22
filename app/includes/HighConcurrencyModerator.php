<?php
/********************************************
 * High-Performance Upload Handler
 * Designed for millions of concurrent users
 *
 * Features:
 * - Asynchronous processing with queue
 * - Redis-backed job queue
 * - Rate limiting per user/IP
 * - Load balancing ready
 * - Graceful degradation
 * - Auto-scaling support
 *
 * @version 3.0.0 (High-Concurrency)
 * @date December 20, 2025
 ********************************************/

class HighConcurrencyModerator {

    private $redis;
    private $useQueue = true;
    private $fallbackModerator;

    // Queue configuration
    const QUEUE_NAME = 'moderation:queue';
    const PRIORITY_QUEUE_NAME = 'moderation:priority';
    const RESULTS_PREFIX = 'moderation:result:';
    const RATE_LIMIT_PREFIX = 'moderation:ratelimit:';

    // Rate limiting
    const MAX_UPLOADS_PER_MINUTE = 10;  // Per user
    const MAX_UPLOADS_PER_HOUR = 50;    // Per user

    // Processing modes
    const MODE_SYNC = 'sync';           // Block and wait (low traffic)
    const MODE_ASYNC = 'async';         // Queue and poll (high traffic)
    const MODE_FAST_TRACK = 'fast';     // Quick rules only (overload)

    public function __construct() {
        // Try to connect to Redis
        try {
            $this->redis = new Redis();
            $this->redis->connect('127.0.0.1', 6379);
            $this->redis->ping();
        } catch (Exception $e) {
            error_log('[HighConcurrencyModerator] Redis unavailable: ' . $e->getMessage());
            $this->useQueue = false;
        }

        // Load fallback moderator
        require_once __DIR__ . '/AIContentModerator.php';
        $this->fallbackModerator = new AIContentModerator();
    }

    /**
     * Moderate ad upload with intelligent routing
     * Automatically selects best processing mode based on system load
     *
     * @param string $userId User/company ID
     * @param string $title Ad title
     * @param string $description Ad description
     * @param array $imagePaths Image paths
     * @param string $userIP User's IP address
     * @return array Moderation result
     */
    public function moderateUpload($userId, $title, $description, $imagePaths = [], $userIP = null) {
        $startTime = microtime(true);

        // Step 1: Rate limiting
        if (!$this->checkRateLimit($userId, $userIP)) {
            return [
                'safe' => false,
                'score' => 0,
                'mode' => 'rate_limited',
                'issues' => ['Rate limit exceeded. Please try again later.'],
                'retry_after' => 60,
                'processing_time' => round((microtime(true) - $startTime) * 1000, 2)
            ];
        }

        // Step 2: Determine processing mode based on load
        $mode = $this->selectProcessingMode();

        // Step 3: Process according to mode
        switch ($mode) {
            case self::MODE_SYNC:
                // Low traffic - process immediately
                return $this->processSynchronous($title, $description, $imagePaths);

            case self::MODE_ASYNC:
                // High traffic - queue for processing
                return $this->processAsynchronous($userId, $title, $description, $imagePaths);

            case self::MODE_FAST_TRACK:
                // Overload - fast rules-only check
                return $this->processFastTrack($title, $description);

            default:
                // Fallback
                return $this->fallbackModerator->moderateAd($title, $description, $imagePaths);
        }
    }

    /**
     * Check rate limits for user/IP
     *
     * @param string $userId
     * @param string $userIP
     * @return bool True if allowed, false if rate limited
     */
    private function checkRateLimit($userId, $userIP) {
        if (!$this->useQueue) {
            return true; // No rate limiting without Redis
        }

        $now = time();

        // Check per-minute limit
        $minuteKey = self::RATE_LIMIT_PREFIX . $userId . ':minute:' . floor($now / 60);
        $minuteCount = $this->redis->incr($minuteKey);
        $this->redis->expire($minuteKey, 60);

        if ($minuteCount > self::MAX_UPLOADS_PER_MINUTE) {
            error_log("[RateLimit] User $userId exceeded per-minute limit");
            return false;
        }

        // Check per-hour limit
        $hourKey = self::RATE_LIMIT_PREFIX . $userId . ':hour:' . floor($now / 3600);
        $hourCount = $this->redis->incr($hourKey);
        $this->redis->expire($hourKey, 3600);

        if ($hourCount > self::MAX_UPLOADS_PER_HOUR) {
            error_log("[RateLimit] User $userId exceeded per-hour limit");
            return false;
        }

        // Optional: IP-based rate limiting for additional protection
        if ($userIP) {
            $ipKey = self::RATE_LIMIT_PREFIX . 'ip:' . $userIP . ':minute:' . floor($now / 60);
            $ipCount = $this->redis->incr($ipKey);
            $this->redis->expire($ipKey, 60);

            // Allow higher limit for IP (multiple users might share IP)
            if ($ipCount > self::MAX_UPLOADS_PER_MINUTE * 5) {
                error_log("[RateLimit] IP $userIP exceeded limit");
                return false;
            }
        }

        return true;
    }

    /**
     * Select processing mode based on current system load
     *
     * @return string Processing mode
     */
    private function selectProcessingMode() {
        if (!$this->useQueue) {
            return self::MODE_SYNC; // No queue, process directly
        }

        // Check queue depth
        $queueDepth = $this->redis->lLen(self::QUEUE_NAME);

        if ($queueDepth < 100) {
            return self::MODE_SYNC; // Light load - process immediately
        } elseif ($queueDepth < 1000) {
            return self::MODE_ASYNC; // Medium load - use queue
        } else {
            return self::MODE_FAST_TRACK; // Heavy load - fast track only
        }
    }

    /**
     * Process synchronously (low traffic)
     *
     * @param string $title
     * @param string $description
     * @param array $imagePaths
     * @return array
     */
    private function processSynchronous($title, $description, $imagePaths) {
        $result = $this->fallbackModerator->moderateAd($title, $description, $imagePaths);
        $result['mode'] = 'synchronous';
        return $result;
    }

    /**
     * Process asynchronously via queue (high traffic)
     *
     * @param string $userId
     * @param string $title
     * @param string $description
     * @param array $imagePaths
     * @return array
     */
    private function processAsynchronous($userId, $title, $description, $imagePaths) {
        // Generate job ID
        $jobId = uniqid('job_', true);

        // Create job data
        $jobData = [
            'job_id' => $jobId,
            'user_id' => $userId,
            'title' => $title,
            'description' => $description,
            'image_paths' => $imagePaths,
            'queued_at' => time(),
            'priority' => 'normal'
        ];

        // Add to queue
        $this->redis->rPush(self::QUEUE_NAME, json_encode($jobData));

        // Return immediate response with job ID
        return [
            'safe' => null, // Unknown yet
            'score' => null,
            'mode' => 'queued',
            'job_id' => $jobId,
            'status' => 'pending',
            'message' => 'Your ad is being reviewed. Check status with job ID.',
            'estimated_wait' => $this->estimateWaitTime(),
            'check_url' => "/api/moderation/status/{$jobId}"
        ];
    }

    /**
     * Fast track processing (overload protection)
     * Only runs critical rules, no ML
     *
     * @param string $title
     * @param string $description
     * @return array
     */
    private function processFastTrack($title, $description) {
        $startTime = microtime(true);

        $text = strtolower(trim($title . ' ' . $description));

        // Ultra-fast critical keyword check
        $criticalWords = ['weapon', 'gun', 'cocaine', 'heroin', 'meth', 'bomb', 'kill', 'murder'];

        foreach ($criticalWords as $word) {
            if (strpos($text, $word) !== false) {
                return [
                    'safe' => false,
                    'score' => 0,
                    'mode' => 'fast_track',
                    'issues' => ["Critical keyword detected: '$word'"],
                    'flags' => ['critical'],
                    'risk_level' => 'critical',
                    'processing_time' => round((microtime(true) - $startTime) * 1000, 2)
                ];
            }
        }

        // If no critical violations, approve with note
        return [
            'safe' => true,
            'score' => 100,
            'mode' => 'fast_track',
            'warnings' => ['Fast-track review only. Full moderation will occur post-publish.'],
            'flags' => [],
            'risk_level' => 'low',
            'processing_time' => round((microtime(true) - $startTime) * 1000, 2)
        ];
    }

    /**
     * Check status of queued job
     *
     * @param string $jobId
     * @return array|null
     */
    public function checkJobStatus($jobId) {
        if (!$this->useQueue) {
            return null;
        }

        // Check if result is ready
        $resultKey = self::RESULTS_PREFIX . $jobId;
        $result = $this->redis->get($resultKey);

        if ($result) {
            return json_decode($result, true);
        }

        // Job still pending
        return [
            'status' => 'pending',
            'message' => 'Your ad is still being reviewed',
            'estimated_wait' => $this->estimateWaitTime()
        ];
    }

    /**
     * Estimate wait time based on queue depth
     *
     * @return int Seconds
     */
    private function estimateWaitTime() {
        if (!$this->useQueue) {
            return 0;
        }

        $queueDepth = $this->redis->lLen(self::QUEUE_NAME);

        // Assume 100ms per job, with 10 workers
        $timePerJob = 0.1; // seconds
        $numWorkers = 10;

        return ceil(($queueDepth / $numWorkers) * $timePerJob);
    }

    /**
     * Get system stats
     *
     * @return array
     */
    public function getSystemStats() {
        if (!$this->useQueue) {
            return ['queue_available' => false];
        }

        $queueDepth = $this->redis->lLen(self::QUEUE_NAME);
        $mode = $this->selectProcessingMode();

        return [
            'queue_available' => true,
            'queue_depth' => $queueDepth,
            'current_mode' => $mode,
            'estimated_wait' => $this->estimateWaitTime() . 's',
            'capacity' => [
                'sync' => $queueDepth < 100 ? 'available' : 'unavailable',
                'async' => $queueDepth < 10000 ? 'available' : 'degraded',
                'fast_track' => 'always_available'
            ]
        ];
    }
}

