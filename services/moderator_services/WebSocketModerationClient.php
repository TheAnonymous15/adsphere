<?php
/********************************************
 * WebSocket Moderation Client
 *
 * Connects to the Python moderation service via WebSocket
 * for real-time streaming moderation results.
 *
 * Use cases:
 * - Video moderation with progress updates
 * - Real-time ad scanning dashboard
 * - Live content moderation
 *
 * Requirements:
 * - PHP 7.4+ with sockets extension
 * - Or use: composer require textalk/websocket
 *
 ********************************************/

class WebSocketModerationClient {

    private $wsUrl;
    private $timeout;
    private $socket;
    private $isConnected = false;

    /**
     * @param string $wsUrl WebSocket URL (default: ws://localhost:8002/ws/moderate)
     * @param int $timeout Connection timeout in seconds
     */
    public function __construct($wsUrl = null, $timeout = 30) {
        $this->wsUrl = $wsUrl ?? 'ws://localhost:8002/ws/moderate';
        $this->timeout = $timeout;
    }

    /**
     * Moderate content with streaming progress updates
     *
     * @param string $jobId Unique job identifier
     * @param string $content Base64 encoded content (image/video)
     * @param string $type Content type: 'image', 'video', 'text'
     * @param callable $onProgress Callback for progress updates: function($partial)
     * @return array Final moderation result
     */
    public function moderateWithProgress($jobId, $content, $type = 'image', $onProgress = null) {
        try {
            // Connect to WebSocket
            $this->connect();

            // Send moderation request
            $request = json_encode([
                'job_id' => $jobId,
                'asset_base64' => $content,
                'type' => $type,
                'timestamp' => time()
            ]);

            $this->send($request);

            // Receive streaming responses
            $finalResult = null;

            while ($this->isConnected) {
                $response = $this->receive();

                if ($response === null) {
                    break;
                }

                $data = json_decode($response, true);

                if ($data === null) {
                    // Might be binary protobuf - try to decode
                    $data = $this->decodeProtobuf($response);
                }

                if (isset($data['error'])) {
                    throw new Exception($data['error']);
                }

                // Check if this is a partial update
                if (isset($data['partial']) && $data['partial'] === true) {
                    if ($onProgress && is_callable($onProgress)) {
                        $onProgress($data);
                    }
                    continue;
                }

                // Check if this is the final result
                if (isset($data['final']) && $data['final'] === true) {
                    $finalResult = $data['data'] ?? $data['result'] ?? $data;
                    break;
                }

                // Cached result
                if (isset($data['cached']) && $data['cached'] === true) {
                    $finalResult = $data['result'] ?? $data;
                    break;
                }
            }

            $this->disconnect();
            return $finalResult;

        } catch (Exception $e) {
            $this->disconnect();
            throw $e;
        }
    }

    /**
     * Simple WebSocket connect using PHP sockets
     * For production, use a proper WebSocket library
     */
    private function connect() {
        $urlParts = parse_url($this->wsUrl);
        $host = $urlParts['host'] ?? 'localhost';
        $port = $urlParts['port'] ?? ($urlParts['scheme'] === 'wss' ? 443 : 80);
        $path = $urlParts['path'] ?? '/ws/moderate';

        // Create socket
        $this->socket = @fsockopen($host, $port, $errno, $errstr, $this->timeout);

        if (!$this->socket) {
            throw new Exception("WebSocket connection failed: $errstr ($errno)");
        }

        // Send WebSocket handshake
        $key = base64_encode(random_bytes(16));
        $headers = [
            "GET $path HTTP/1.1",
            "Host: $host:$port",
            "Upgrade: websocket",
            "Connection: Upgrade",
            "Sec-WebSocket-Key: $key",
            "Sec-WebSocket-Version: 13",
            "Origin: http://$host",
            ""
        ];

        fwrite($this->socket, implode("\r\n", $headers) . "\r\n");

        // Read response
        $response = fread($this->socket, 1024);

        if (strpos($response, '101') === false) {
            throw new Exception("WebSocket handshake failed: $response");
        }

        $this->isConnected = true;
        stream_set_timeout($this->socket, $this->timeout);
    }

    /**
     * Send data over WebSocket
     */
    private function send($data) {
        if (!$this->isConnected) {
            throw new Exception("Not connected");
        }

        $frame = $this->encodeFrame($data);
        fwrite($this->socket, $frame);
    }

    /**
     * Receive data from WebSocket
     */
    private function receive() {
        if (!$this->isConnected) {
            return null;
        }

        $header = fread($this->socket, 2);
        if (strlen($header) < 2) {
            return null;
        }

        $firstByte = ord($header[0]);
        $secondByte = ord($header[1]);

        $opcode = $firstByte & 0x0F;
        $length = $secondByte & 0x7F;

        // Handle different length formats
        if ($length === 126) {
            $extLength = fread($this->socket, 2);
            $length = unpack('n', $extLength)[1];
        } elseif ($length === 127) {
            $extLength = fread($this->socket, 8);
            $length = unpack('J', $extLength)[1];
        }

        // Read payload
        $payload = '';
        while (strlen($payload) < $length) {
            $chunk = fread($this->socket, $length - strlen($payload));
            if ($chunk === false) {
                break;
            }
            $payload .= $chunk;
        }

        // Handle close frame
        if ($opcode === 8) {
            $this->isConnected = false;
            return null;
        }

        return $payload;
    }

    /**
     * Encode WebSocket frame
     */
    private function encodeFrame($data) {
        $length = strlen($data);
        $frame = chr(0x81); // Text frame, FIN=1

        if ($length < 126) {
            $frame .= chr($length | 0x80); // Masked
        } elseif ($length < 65536) {
            $frame .= chr(126 | 0x80);
            $frame .= pack('n', $length);
        } else {
            $frame .= chr(127 | 0x80);
            $frame .= pack('J', $length);
        }

        // Add mask
        $mask = random_bytes(4);
        $frame .= $mask;

        // Mask the data
        for ($i = 0; $i < $length; $i++) {
            $frame .= $data[$i] ^ $mask[$i % 4];
        }

        return $frame;
    }

    /**
     * Decode protobuf ModerationFrame (simplified)
     */
    private function decodeProtobuf($binary) {
        // Simple protobuf decoding for ModerationFrame
        // For production, use google/protobuf PHP library

        try {
            $result = [
                'task_id' => '',
                'sequence' => 0,
                'final' => false,
                'payload' => ''
            ];

            $pos = 0;
            $len = strlen($binary);

            while ($pos < $len) {
                $tag = ord($binary[$pos]);
                $fieldNum = $tag >> 3;
                $wireType = $tag & 0x07;
                $pos++;

                switch ($fieldNum) {
                    case 1: // task_id (string)
                        $strLen = ord($binary[$pos++]);
                        $result['task_id'] = substr($binary, $pos, $strLen);
                        $pos += $strLen;
                        break;

                    case 2: // sequence (int64)
                        $result['sequence'] = ord($binary[$pos++]);
                        break;

                    case 3: // final (bool)
                        $result['final'] = ord($binary[$pos++]) === 1;
                        break;

                    case 4: // payload (bytes)
                        $payloadLen = ord($binary[$pos++]);
                        $result['payload'] = substr($binary, $pos, $payloadLen);
                        $pos += $payloadLen;

                        // Try to decode payload as JSON
                        $decoded = json_decode($result['payload'], true);
                        if ($decoded) {
                            $result['data'] = $decoded;
                        }
                        break;

                    default:
                        $pos++;
                }
            }

            return $result;

        } catch (Exception $e) {
            return ['raw' => bin2hex($binary)];
        }
    }

    /**
     * Disconnect WebSocket
     */
    private function disconnect() {
        if ($this->socket) {
            // Send close frame
            if ($this->isConnected) {
                fwrite($this->socket, chr(0x88) . chr(0x80) . random_bytes(4));
            }
            fclose($this->socket);
            $this->socket = null;
        }
        $this->isConnected = false;
    }

    /**
     * Check if WebSocket service is available
     */
    public static function isServiceAvailable($wsUrl = null) {
        $url = $wsUrl ?? 'ws://localhost:8002/ws/moderate';
        $urlParts = parse_url($url);
        $host = $urlParts['host'] ?? 'localhost';
        $port = $urlParts['port'] ?? 80;

        $socket = @fsockopen($host, $port, $errno, $errstr, 2);
        if ($socket) {
            fclose($socket);
            return true;
        }
        return false;
    }

    // =========================================================================
    // HIGH-LEVEL MODERATION METHODS (WebSocket Primary)
    // =========================================================================

    /**
     * Moderate text content via WebSocket
     *
     * @param string $title Ad title
     * @param string $description Ad description
     * @param string $category Category for context
     * @param callable|null $onProgress Progress callback
     * @return array Moderation result
     */
    public function moderateText($title, $description, $category = 'general', $onProgress = null) {
        $jobId = 'text-' . uniqid() . '-' . time();

        $content = json_encode([
            'title' => $title,
            'description' => $description,
            'category' => $category
        ]);

        return $this->moderateWithProgress($jobId, base64_encode($content), 'text', $onProgress);
    }

    /**
     * Moderate image via WebSocket
     *
     * @param string $imagePath Path to image file
     * @param array $context Additional context
     * @param callable|null $onProgress Progress callback
     * @return array Moderation result
     */
    public function moderateImage($imagePath, $context = [], $onProgress = null) {
        if (!file_exists($imagePath)) {
            throw new Exception("Image file not found: $imagePath");
        }

        $jobId = 'img-' . uniqid() . '-' . time();
        $imageContent = base64_encode(file_get_contents($imagePath));

        $payload = json_encode([
            'image_data' => $imageContent,
            'filename' => basename($imagePath),
            'context' => $context
        ]);

        return $this->moderateWithProgress($jobId, base64_encode($payload), 'image', $onProgress);
    }

    /**
     * Moderate video via WebSocket
     *
     * @param string $videoPath Path to video file
     * @param array $context Additional context
     * @param callable|null $onProgress Progress callback
     * @return array Moderation result
     */
    public function moderateVideo($videoPath, $context = [], $onProgress = null) {
        if (!file_exists($videoPath)) {
            throw new Exception("Video file not found: $videoPath");
        }

        $jobId = 'video-' . uniqid() . '-' . time();
        $videoContent = base64_encode(file_get_contents($videoPath));

        $payload = json_encode([
            'video_data' => $videoContent,
            'filename' => basename($videoPath),
            'context' => $context
        ]);

        return $this->moderateWithProgress($jobId, base64_encode($payload), 'video', $onProgress);
    }

    /**
     * Combined realtime moderation (text + media) via WebSocket
     *
     * @param string $title
     * @param string $description
     * @param array $imageUrls
     * @param array $videoUrls
     * @param array $context
     * @param callable|null $onProgress
     * @return array Moderation result
     */
    public function moderateRealtime($title, $description, $imageUrls = [], $videoUrls = [], $context = [], $onProgress = null) {
        $jobId = 'realtime-' . uniqid() . '-' . time();

        // Build media array
        $media = [];
        foreach ($imageUrls as $url) {
            if ($url) {
                $media[] = ['type' => 'image', 'url' => $url];
            }
        }
        foreach ($videoUrls as $url) {
            if ($url) {
                $media[] = ['type' => 'video', 'url' => $url];
            }
        }

        $payload = json_encode([
            'title' => $title,
            'description' => $description,
            'category' => $context['category'] ?? 'general',
            'media' => $media,
            'user' => [
                'id' => $context['user_id'] ?? null,
                'company' => $context['company'] ?? null
            ],
            'context' => [
                'ad_id' => $context['ad_id'] ?? null,
                'source' => $context['source'] ?? 'websocket_client'
            ]
        ]);

        return $this->moderateWithProgress($jobId, base64_encode($payload), 'realtime', $onProgress);
    }

    /**
     * Run realtime scanner via WebSocket
     *
     * @param string $mode 'incremental', 'full', 'single', 'priority'
     * @param string|null $adId For single mode
     * @param string|null $companyId Filter by company
     * @param string|null $category Filter by category
     * @param int $limit Max ads to scan
     * @param callable|null $onProgress Progress callback (called for each ad scanned)
     * @return array Scanner results
     */
    public function realtimeScanner($mode = 'incremental', $adId = null, $companyId = null, $category = null, $limit = 100, $onProgress = null) {
        $jobId = 'scanner-' . uniqid() . '-' . time();

        $payload = json_encode([
            'mode' => $mode,
            'ad_id' => $adId,
            'company_id' => $companyId,
            'category' => $category,
            'limit' => $limit,
            'skip_cached' => true
        ]);

        return $this->moderateWithProgress($jobId, base64_encode($payload), 'scanner', $onProgress);
    }

    /**
     * Batch scan multiple ads via WebSocket
     *
     * @param array $adIds Array of ad IDs
     * @param string $priority 'urgent', 'high', 'normal', 'low'
     * @param callable|null $onProgress Progress callback
     * @return array Batch results
     */
    public function batchScan($adIds, $priority = 'normal', $onProgress = null) {
        $jobId = 'batch-' . uniqid() . '-' . time();

        $payload = json_encode([
            'ad_ids' => $adIds,
            'priority' => $priority
        ]);

        return $this->moderateWithProgress($jobId, base64_encode($payload), 'batch_scan', $onProgress);
    }

    /**
     * Enqueue single ad for scanning via WebSocket
     *
     * @param string $adId Ad ID
     * @param string $priority Priority level
     * @param callable|null $onProgress Progress callback
     * @return array Result
     */
    public function enqueueAd($adId, $priority = 'normal', $onProgress = null) {
        $jobId = 'enqueue-' . uniqid();

        $payload = json_encode([
            'action' => 'enqueue',
            'ad_id' => $adId,
            'priority' => $priority
        ]);

        return $this->moderateWithProgress($jobId, base64_encode($payload), 'enqueue', $onProgress);
    }
}

