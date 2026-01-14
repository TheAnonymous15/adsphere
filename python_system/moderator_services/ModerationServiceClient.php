<?php
/********************************************
 * ModerationServiceClient
 *
 * PHP client for the external AI/ML moderation microservice
 * (FastAPI / Docker-based system described in design).
 *
 * Pipeline: Scanner → Sanitizer → Compressor → OCR → Content Analysis
 *
 * This client:
 *  - Sends title/description/media for moderation
 *  - Receives moderation decision (approve/review/block)
 *  - Returns PROCESSED (sanitized + compressed) images back to caller
 *  - Falls back gracefully if the service is unavailable
 *  - Supports WebSocket for streaming progress (video moderation)
 *
 * Communication Methods:
 *  - REST API: For text, image, and quick operations
 *  - WebSocket: For video and long-running operations with progress
 ********************************************/

// Include WebSocket client for streaming operations
require_once __DIR__ . '/WebSocketModerationClient.php';

class ModerationServiceClient
{
    /**
     * Base URL of the external moderation service
     * e.g. http://localhost:8002 or http://moderation:8000 in Docker
     */
    private string $baseUrl;

    /**
     * Request timeout in seconds
     */
    private int $timeout;

    /**
     * WebSocket client for streaming operations
     */
    private ?WebSocketModerationClient $wsClient = null;

    public function __construct(?string $baseUrl = null, int $timeout = 30)
    {
        // Allow override via env, then parameter, then default
        $envUrl = getenv('MODERATION_SERVICE_URL');
        $this->baseUrl = rtrim($baseUrl ?: ($envUrl ?: 'http://localhost:8002'), '/');
        $this->timeout = $timeout;
    }

    /**
     * Get the base URL of the moderation service
     * @return string
     */
    public function getBaseUrl(): string
    {
        return $this->baseUrl;
    }

    /**
     * Get WebSocket URL from base URL
     * @return string
     */
    public function getWebSocketUrl(): string
    {
        $wsUrl = str_replace(['http://', 'https://'], ['ws://', 'wss://'], $this->baseUrl);
        return $wsUrl . '/ws/moderate';
    }

    /**
     * Get or create WebSocket client
     * @return WebSocketModerationClient
     */
    private function getWsClient(): WebSocketModerationClient
    {
        if ($this->wsClient === null) {
            $this->wsClient = new WebSocketModerationClient($this->getWebSocketUrl(), $this->timeout);
        }
        return $this->wsClient;
    }

    /**
     * Call the realtime moderation endpoint.
     *
     * PRIMARY: WebSocket (streaming, progress updates)
     * FALLBACK: REST API (if WebSocket unavailable)
     *
     * @param string $title
     * @param string $description
     * @param array $imageUrls  Array of public image URLs or paths the service can access
     * @param array $videoUrls  Array of public video URLs (optional)
     * @param array $context    Additional context (user, ad_id, category, etc.)
     * @param callable|null $onProgress Progress callback for WebSocket mode
     * @return array|null       Normalized response or null on hard failure
     */
    public function moderateRealtime(string $title, string $description, array $imageUrls = [], array $videoUrls = [], array $context = [], ?callable $onProgress = null): ?array
    {
        // TRY WEBSOCKET FIRST (Primary)
        if ($this->isWebSocketAvailable()) {
            try {
                $wsClient = $this->getWsClient();
                $result = $wsClient->moderateRealtime($title, $description, $imageUrls, $videoUrls, $context, $onProgress);

                if ($result !== null) {
                    return $result;
                }
            } catch (Exception $e) {
                error_log('[ModerationServiceClient] WebSocket failed, falling back to REST: ' . $e->getMessage());
            }
        }

        // FALLBACK TO REST API
        $payload = [
            'title'       => $title,
            'description' => $description,
            'category'    => $context['category'] ?? 'general',
            'language'    => $context['language'] ?? 'auto',
            'media'       => [],
            'user'        => [
                'id'      => $context['user_id'] ?? null,
                'company' => $context['company'] ?? null,
            ],
            'context'     => [
                'ad_id'  => $context['ad_id'] ?? null,
                'source' => $context['source'] ?? 'php_realtime_moderator',
                'ip'     => $_SERVER['REMOTE_ADDR'] ?? null,
            ],
        ];

        foreach ($imageUrls as $url) {
            if (!$url) continue;
            $payload['media'][] = [
                'type' => 'image',
                'url'  => $url,
            ];
        }

        foreach ($videoUrls as $url) {
            if (!$url) continue;
            $payload['media'][] = [
                'type' => 'video',
                'url'  => $url,
            ];
        }

        $url = $this->baseUrl . '/moderate/realtime';

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS     => json_encode($payload),
            CURLOPT_TIMEOUT        => $this->timeout,
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlErr  = curl_error($ch);
        curl_close($ch);

        if ($response === false) {
            error_log('[ModerationServiceClient] cURL error: ' . $curlErr);
            return null;
        }

        if ($httpCode < 200 || $httpCode >= 300) {
            error_log('[ModerationServiceClient] HTTP ' . $httpCode . ' from moderation service: ' . $response);
            return null;
        }

        $data = json_decode($response, true);
        if (!is_array($data)) {
            error_log('[ModerationServiceClient] Invalid JSON from moderation service');
            return null;
        }

        return $data;
    }

    /**
     * Process image through the full pipeline: Scan → Sanitize → Compress → OCR
     * Returns the processed (sanitized + compressed) image data.
     *
     * PRIMARY: WebSocket (streaming, progress updates)
     * FALLBACK: REST API (if WebSocket unavailable)
     *
     * @param string $imagePath Path to the image file
     * @param array $context Additional context
     * @param callable|null $onProgress Progress callback for WebSocket mode
     * @return array|null Response with processed image data and moderation result
     *   [
     *     'success' => bool,
     *     'decision' => 'approve'|'review'|'block',
     *     'processed_image' => base64 encoded WebP image data (if success),
     *     'original_size' => int,
     *     'processed_size' => int,
     *     'format' => 'webp',
     *     'warnings' => [],
     *     'ocr_text' => string|null,
     *   ]
     */
    public function processImage(string $imagePath, array $context = [], ?callable $onProgress = null): ?array
    {
        if (!file_exists($imagePath)) {
            error_log('[ModerationServiceClient] Image file not found: ' . $imagePath);
            return null;
        }

        // TRY WEBSOCKET FIRST (Primary)
        if ($this->isWebSocketAvailable()) {
            try {
                $wsClient = $this->getWsClient();
                $result = $wsClient->moderateImage($imagePath, $context, $onProgress);

                if ($result !== null) {
                    return $result;
                }
            } catch (Exception $e) {
                error_log('[ModerationServiceClient] WebSocket image failed, falling back to REST: ' . $e->getMessage());
            }
        }

        // FALLBACK TO REST API
        // Read image and encode as base64
        $imageData = file_get_contents($imagePath);
        if ($imageData === false) {
            error_log('[ModerationServiceClient] Failed to read image: ' . $imagePath);
            return null;
        }

        $payload = [
            'image_data' => base64_encode($imageData),
            'filename' => basename($imagePath),
            'context' => $context,
            'options' => [
                'sanitize' => true,
                'compress' => true,
                'target_size' => 1024 * 1024, // 1MB
                'output_format' => 'webp',
                'extract_text' => true, // OCR
            ]
        ];

        $url = $this->baseUrl . '/moderate/image/process';

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS     => json_encode($payload),
            CURLOPT_TIMEOUT        => $this->timeout,
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlErr  = curl_error($ch);
        curl_close($ch);

        if ($response === false) {
            error_log('[ModerationServiceClient] processImage cURL error: ' . $curlErr);
            return null;
        }

        if ($httpCode < 200 || $httpCode >= 300) {
            error_log('[ModerationServiceClient] processImage HTTP ' . $httpCode . ': ' . $response);
            return null;
        }

        $data = json_decode($response, true);
        if (!is_array($data)) {
            error_log('[ModerationServiceClient] processImage invalid JSON response');
            return null;
        }

        return $data;
    }

    /**
     * Process image locally using Python pipeline (fallback when service unavailable).
     * Calls the Python security scanner directly.
     *
     * @param string $imagePath Path to the image file
     * @param string $outputPath Path for processed output
     * @return array Result with processed image info
     */
    public function processImageLocal(string $imagePath, string $outputPath): array
    {
        $result = [
            'success' => false,
            'decision' => 'approve', // Default to approve if processing succeeds
            'original_size' => filesize($imagePath),
            'processed_size' => 0,
            'format' => 'webp',
            'warnings' => [],
            'sanitized' => false,
            'compressed' => false,
        ];

        // Path to the Python processor script
        $pythonScript = __DIR__ . '/process_image_cli.py';

        // If CLI script doesn't exist, use the security package directly
        if (!file_exists($pythonScript)) {
            $pythonScript = __DIR__ . '/moderation_service/app/services/images/security/image_sanitizer.py';
        }

        // Build command
        $cmd = sprintf(
            'python3 %s %s %s 2>&1',
            escapeshellarg($pythonScript),
            escapeshellarg($imagePath),
            escapeshellarg($outputPath)
        );

        $output = [];
        $returnCode = 0;
        exec($cmd, $output, $returnCode);

        if ($returnCode === 0 && file_exists($outputPath)) {
            $result['success'] = true;
            $result['processed_size'] = filesize($outputPath);
            $result['sanitized'] = true;
            $result['compressed'] = true;

            // Check if output is significantly different (hidden data was removed)
            if ($result['processed_size'] < $result['original_size'] * 0.9) {
                $result['warnings'][] = 'Hidden data may have been removed';
            }
        } else {
            $result['warnings'][] = 'Local processing failed: ' . implode("\n", $output);
            // Copy original if processing fails
            if (copy($imagePath, $outputPath)) {
                $result['success'] = true;
                $result['processed_size'] = filesize($outputPath);
            }
        }

        return $result;
    }

    /**
     * Check if the moderation service is available
     * @return bool
     */
    public function isServiceAvailable(): bool
    {
        $ch = curl_init($this->baseUrl . '/health');
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 3,
            CURLOPT_NOBODY => true,
        ]);
        curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        return $httpCode >= 200 && $httpCode < 300;
    }

    /**
     * Process text through the moderation pipeline.
     *
     * PRIMARY: WebSocket (streaming, progress updates)
     * FALLBACK: REST API (if WebSocket unavailable)
     *
     * @param string $title Ad title
     * @param string $description Ad description
     * @param string $category Content category
     * @param string $language Language code or 'auto' for detection
     * @param array $context Additional context
     * @param callable|null $onProgress Progress callback for WebSocket mode
     * @return array|null Response with moderation decision
     *   [
     *     'success' => bool,
     *     'decision' => 'approve'|'review'|'block',
     *     'risk_level' => 'low'|'medium'|'high'|'critical',
     *     'global_score' => float,
     *     'category_scores' => [...],
     *     'flags' => [...],
     *     'reasons' => [...],
     *     'detected_language' => string,
     *     'intent' => string,
     *     'ai_insights' => [...],
     *   ]
     */
    public function processText(string $title, string $description, string $category = 'general', string $language = 'auto', array $context = [], ?callable $onProgress = null): ?array
    {
        // TRY WEBSOCKET FIRST (Primary)
        if ($this->isWebSocketAvailable()) {
            try {
                $wsClient = $this->getWsClient();
                $result = $wsClient->moderateText($title, $description, $category, $onProgress);

                if ($result !== null) {
                    return $result;
                }
            } catch (Exception $e) {
                error_log('[ModerationServiceClient] WebSocket text failed, falling back to REST: ' . $e->getMessage());
            }
        }

        // FALLBACK TO REST API
        $payload = [
            'title' => $title,
            'description' => $description,
            'category' => $category,
            'language' => $language,
            'context' => $context,
        ];

        $url = $this->baseUrl . '/moderate/text/process';

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS     => json_encode($payload),
            CURLOPT_TIMEOUT        => $this->timeout,
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlErr  = curl_error($ch);
        curl_close($ch);

        if ($response === false) {
            error_log('[ModerationServiceClient] processText cURL error: ' . $curlErr);
            return null;
        }

        if ($httpCode < 200 || $httpCode >= 300) {
            error_log('[ModerationServiceClient] processText HTTP ' . $httpCode . ': ' . $response);
            return null;
        }

        $data = json_decode($response, true);
        if (!is_array($data)) {
            error_log('[ModerationServiceClient] processText invalid JSON response');
            return null;
        }

        return $data;
    }

    /**
     * Process video through the moderation pipeline.
     *
     * PRIMARY: WebSocket (streaming, progress updates)
     * FALLBACK: REST API (if WebSocket unavailable)
     *
     * @param string|null $videoPath Local path to video file
     * @param string|null $videoUrl URL to video file
     * @param array $context Additional context
     * @param array $options Processing options (fps, analyze_audio, max_duration)
     * @param callable|null $onProgress Progress callback for WebSocket mode
     * @return array|null Response with moderation decision
     *   [
     *     'success' => bool,
     *     'decision' => 'approve'|'review'|'block',
     *     'risk_level' => string,
     *     'duration_seconds' => float,
     *     'frames_analyzed' => int,
     *     'audio_analyzed' => bool,
     *     'category_scores' => [...],
     *     'flags' => [...],
     *     'detected_objects' => [...],
     *     'detected_text' => [...],
     *     'detected_speech' => string,
     *   ]
     */
    public function processVideo(?string $videoPath = null, ?string $videoUrl = null, array $context = [], array $options = [], ?callable $onProgress = null): ?array
    {
        // TRY WEBSOCKET FIRST (Primary) - especially good for video with progress
        if ($videoPath && $this->isWebSocketAvailable()) {
            try {
                $wsClient = $this->getWsClient();
                $result = $wsClient->moderateVideo($videoPath, $context, $onProgress);

                if ($result !== null) {
                    return $result;
                }
            } catch (Exception $e) {
                error_log('[ModerationServiceClient] WebSocket video failed, falling back to REST: ' . $e->getMessage());
            }
        }

        // FALLBACK TO REST API
        $payload = [
            'video_path' => $videoPath,
            'video_url' => $videoUrl,
            'context' => $context,
            'options' => array_merge([
                'fps' => 2,
                'analyze_audio' => true,
                'max_duration' => 60,
            ], $options),
        ];

        $url = $this->baseUrl . '/moderate/video/process';

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS     => json_encode($payload),
            CURLOPT_TIMEOUT        => 120, // Videos take longer
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlErr  = curl_error($ch);
        curl_close($ch);

        if ($response === false) {
            error_log('[ModerationServiceClient] processVideo cURL error: ' . $curlErr);
            return null;
        }

        if ($httpCode < 200 || $httpCode >= 300) {
            error_log('[ModerationServiceClient] processVideo HTTP ' . $httpCode . ': ' . $response);
            return null;
        }

        $data = json_decode($response, true);
        if (!is_array($data)) {
            error_log('[ModerationServiceClient] processVideo invalid JSON response');
            return null;
        }

        return $data;
    }

    /**
     * Process video asynchronously (for long videos).
     * Returns a job_id that can be used to check status.
     *
     * @param string|null $videoPath Local path to video file
     * @param string|null $videoUrl URL to video file
     * @param array $options Processing options
     * @return array|null ['job_id' => string, 'status' => 'processing']
     */
    public function processVideoAsync(?string $videoPath = null, ?string $videoUrl = null, array $options = []): ?array
    {
        $payload = [
            'video_path' => $videoPath,
            'video_url' => $videoUrl,
            'options' => $options,
        ];

        $url = $this->baseUrl . '/moderate/video/process-async';

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS     => json_encode($payload),
            CURLOPT_TIMEOUT        => 10,
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode < 200 || $httpCode >= 300) {
            return null;
        }

        return json_decode($response, true);
    }

    /**
     * Check job status for async processing.
     *
     * @param string $jobId Job ID from async processing
     * @return array|null Job status and result if completed
     */
    public function getJobStatus(string $jobId): ?array
    {
        $url = $this->baseUrl . '/moderate/job/' . urlencode($jobId);

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 5,
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode < 200 || $httpCode >= 300) {
            return null;
        }

        return json_decode($response, true);
    }

    /**
     * Run the realtime ad scanner to scan all ads in the system.
     *
     * PRIMARY: WebSocket (streaming progress for each ad scanned)
     * FALLBACK: REST API (if WebSocket unavailable)
     *
     * @param string $mode Scan mode: 'incremental', 'full', or 'single'
     * @param string|null $adId For single ad scan
     * @param string|null $companyId Filter by company
     * @param string|null $category Filter by category
     * @param int $limit Max ads to scan per run
     * @param bool $skipCached Skip recently scanned ads
     * @param callable|null $onProgress Progress callback (called for each ad scanned)
     * @return array|null Scanner results
     */
    public function realtimeScanner(
        string $mode = 'incremental',
        ?string $adId = null,
        ?string $companyId = null,
        ?string $category = null,
        int $limit = 100,
        bool $skipCached = true,
        ?callable $onProgress = null
    ): ?array {
        // TRY WEBSOCKET FIRST (Primary) - great for batch scanning with progress
        if ($this->isWebSocketAvailable()) {
            try {
                $wsClient = $this->getWsClient();
                $result = $wsClient->realtimeScanner($mode, $adId, $companyId, $category, $limit, $onProgress);

                if ($result !== null) {
                    return $result;
                }
            } catch (Exception $e) {
                error_log('[ModerationServiceClient] WebSocket scanner failed, falling back to REST: ' . $e->getMessage());
            }
        }

        // FALLBACK TO REST API
        $payload = [
            'mode' => $mode,
            'ad_id' => $adId,
            'company_id' => $companyId,
            'category' => $category,
            'limit' => $limit,
            'skip_cached' => $skipCached,
            'cache_ttl_hours' => 24,
        ];

        $url = $this->baseUrl . '/moderate/realtimescanner';

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS     => json_encode($payload),
            CURLOPT_TIMEOUT        => 120, // Scanning can take time
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $curlErr  = curl_error($ch);
        curl_close($ch);

        if ($response === false) {
            error_log('[ModerationServiceClient] realtimeScanner cURL error: ' . $curlErr);
            return null;
        }

        if ($httpCode < 200 || $httpCode >= 300) {
            error_log('[ModerationServiceClient] realtimeScanner HTTP ' . $httpCode . ': ' . $response);
            return null;
        }

        return json_decode($response, true);
    }

    /**
     * Start a background scanner that continuously scans ads.
     *
     * @return array|null ['scanner_id' => string, 'status' => 'started']
     */
    public function startBackgroundScanner(): ?array
    {
        $url = $this->baseUrl . '/moderate/realtimescanner/start';

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS     => '{}',
            CURLOPT_TIMEOUT        => 10,
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode < 200 || $httpCode >= 300) {
            return null;
        }

        return json_decode($response, true);
    }

    /**
     * Stop a running background scanner.
     *
     * @param string $scannerId Scanner ID from startBackgroundScanner
     * @return array|null
     */
    public function stopBackgroundScanner(string $scannerId): ?array
    {
        $url = $this->baseUrl . '/moderate/realtimescanner/stop/' . urlencode($scannerId);

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST           => true,
            CURLOPT_HTTPHEADER     => ['Content-Type: application/json'],
            CURLOPT_POSTFIELDS     => '{}',
            CURLOPT_TIMEOUT        => 5,
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode < 200 || $httpCode >= 300) {
            return null;
        }

        return json_decode($response, true);
    }

    /**
     * Get status of a background scanner.
     *
     * @param string $scannerId Scanner ID
     * @return array|null Scanner status
     */
    public function getScannerStatus(string $scannerId): ?array
    {
        $url = $this->baseUrl . '/moderate/realtimescanner/status/' . urlencode($scannerId);

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 5,
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode < 200 || $httpCode >= 300) {
            return null;
        }

        return json_decode($response, true);
    }

    /**
     * Get overall scanner statistics.
     *
     * @return array|null Scanner stats
     */
    public function getScannerStats(): ?array
    {
        $url = $this->baseUrl . '/moderate/realtimescanner/stats';

        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT        => 5,
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode < 200 || $httpCode >= 300) {
            return null;
        }

        return json_decode($response, true);
    }

    // =========================================================================
    // WEBSOCKET STREAMING METHODS
    // =========================================================================

    /**
     * Check if WebSocket service is available
     * @return bool
     */
    public function isWebSocketAvailable(): bool
    {
        return WebSocketModerationClient::isServiceAvailable($this->getWebSocketUrl());
    }

    /**
     * Moderate video with streaming progress updates via WebSocket.
     *
     * Use this for video moderation when you need real-time progress.
     * Falls back to REST API if WebSocket is unavailable.
     *
     * @param string $videoPath Path to video file
     * @param callable|null $onProgress Callback for progress: function($data) { echo $data['status']; }
     * @param array $context Additional context
     * @return array Moderation result
     */
    public function moderateVideoWithProgress(string $videoPath, ?callable $onProgress = null, array $context = []): array
    {
        // Check if WebSocket is available
        if (!$this->isWebSocketAvailable()) {
            // Fall back to REST API
            error_log('[ModerationServiceClient] WebSocket unavailable, using REST API fallback');
            return $this->processVideo($videoPath, null, $context) ?? ['error' => 'Service unavailable'];
        }

        try {
            // Read and encode video
            if (!file_exists($videoPath)) {
                return ['error' => 'Video file not found: ' . $videoPath];
            }

            $videoContent = base64_encode(file_get_contents($videoPath));
            $jobId = 'video-' . uniqid() . '-' . time();

            // Use WebSocket for streaming
            $wsClient = $this->getWsClient();

            $result = $wsClient->moderateWithProgress(
                $jobId,
                $videoContent,
                'video',
                $onProgress
            );

            return $result ?? ['error' => 'No result received'];

        } catch (Exception $e) {
            error_log('[ModerationServiceClient] WebSocket error: ' . $e->getMessage());

            // Fall back to REST API
            return $this->processVideo($videoPath, null, $context) ?? ['error' => $e->getMessage()];
        }
    }

    /**
     * Moderate image with streaming progress via WebSocket.
     *
     * Useful for large images or when you want progress updates.
     *
     * @param string $imagePath Path to image file
     * @param callable|null $onProgress Callback for progress
     * @param array $context Additional context
     * @return array Moderation result
     */
    public function moderateImageWithProgress(string $imagePath, ?callable $onProgress = null, array $context = []): array
    {
        // For images, WebSocket is optional - REST is usually fast enough
        // But we support it for consistency

        if (!$this->isWebSocketAvailable()) {
            return $this->processImage($imagePath, $context) ?? ['error' => 'Service unavailable'];
        }

        try {
            if (!file_exists($imagePath)) {
                return ['error' => 'Image file not found: ' . $imagePath];
            }

            $imageContent = base64_encode(file_get_contents($imagePath));
            $jobId = 'img-' . uniqid() . '-' . time();

            $wsClient = $this->getWsClient();

            $result = $wsClient->moderateWithProgress(
                $jobId,
                $imageContent,
                'image',
                $onProgress
            );

            return $result ?? ['error' => 'No result received'];

        } catch (Exception $e) {
            error_log('[ModerationServiceClient] WebSocket error: ' . $e->getMessage());
            return $this->processImage($imagePath, $context) ?? ['error' => $e->getMessage()];
        }
    }

    /**
     * Stream batch scanning via WebSocket.
     *
     * Useful for scanning multiple ads with real-time progress.
     *
     * @param array $adIds Array of ad IDs to scan
     * @param callable|null $onProgress Callback for each ad scanned
     * @return array Final results
     */
    public function streamBatchScan(array $adIds, ?callable $onProgress = null): array
    {
        if (!$this->isWebSocketAvailable()) {
            // Fall back to REST batch scan
            return $this->realtimeScanner('batch', null, null, null, count($adIds)) ?? ['error' => 'Service unavailable'];
        }

        try {
            $wsClient = $this->getWsClient();
            $jobId = 'batch-' . uniqid();

            $result = $wsClient->moderateWithProgress(
                $jobId,
                json_encode(['ad_ids' => $adIds]),
                'batch_scan',
                $onProgress
            );

            return $result ?? ['error' => 'No result received'];

        } catch (Exception $e) {
            error_log('[ModerationServiceClient] WebSocket batch scan error: ' . $e->getMessage());
            return ['error' => $e->getMessage()];
        }
    }

    /**
     * Get the preferred communication method based on content type.
     *
     * WebSocket is ALWAYS preferred for real-time streaming.
     * REST is only used as fallback when WebSocket is unavailable.
     *
     * @param string $contentType Type of content: 'text', 'image', 'video', 'batch', 'scanner'
     * @return string 'websocket' or 'rest'
     */
    public function getPreferredMethod(string $contentType): string
    {
        // WebSocket is ALWAYS primary for ALL content types
        // REST is only fallback
        return $this->isWebSocketAvailable() ? 'websocket' : 'rest';
    }

    /**
     * Get connection status for both methods
     *
     * @return array Status of both connection methods
     */
    public function getConnectionStatus(): array
    {
        return [
            'websocket' => [
                'available' => $this->isWebSocketAvailable(),
                'url' => $this->getWebSocketUrl(),
                'primary' => true
            ],
            'rest' => [
                'available' => $this->isServiceAvailable(),
                'url' => $this->baseUrl,
                'primary' => false,
                'role' => 'fallback'
            ]
        ];
    }
}
