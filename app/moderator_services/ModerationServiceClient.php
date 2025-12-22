<?php
/********************************************
 * ModerationServiceClient
 *
 * PHP client for the external AI/ML moderation microservice
 * (FastAPI / Docker-based system described in design).
 *
 * This client is designed to be called from PHP endpoints
 * like `app/api/moderators/realtime_moderator.php`.
 *
 * It:
 *  - Sends title/description/media metadata
 *  - Receives a unified moderation decision (approve/review/reject)
 *  - Falls back gracefully if the service is unavailable
 ********************************************/

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

    public function __construct(?string $baseUrl = null, int $timeout = 10)
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
     * Call the realtime moderation endpoint.
     *
     * @param string $title
     * @param string $description
     * @param array $imageUrls  Array of public image URLs or paths the service can access
     * @param array $videoUrls  Array of public video URLs (optional)
     * @param array $context    Additional context (user, ad_id, category, etc.)
     * @return array|null       Normalized response or null on hard failure
     */
    public function moderateRealtime(string $title, string $description, array $imageUrls = [], array $videoUrls = [], array $context = []): ?array
    {
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
}
