<?php
/********************************************
 * Scanner API Endpoint
 *
 * REST API for triggering scans remotely.
 * Useful for webhooks, admin dashboards, and external integrations.
 *
 * Endpoints:
 *   POST /api/scanner/scan          - Run a scan
 *   POST /api/scanner/enqueue       - Enqueue ad for async scanning
 *   GET  /api/scanner/status        - Get scanner status
 *   GET  /api/scanner/stats         - Get statistics
 *   GET  /api/scanner/health        - Health check
 *   POST /api/scanner/clear-cache   - Clear scan cache
 *
 ********************************************/

header('Content-Type: application/json');

// CORS headers
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-API-Key');

// Handle preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// Simple API key authentication
$apiKey = $_SERVER['HTTP_X_API_KEY'] ?? $_GET['api_key'] ?? '';
$validApiKey = getenv('SCANNER_API_KEY') ?: 'your-secret-api-key-change-me';

if ($apiKey !== $validApiKey && $validApiKey !== 'your-secret-api-key-change-me') {
    http_response_code(401);
    echo json_encode(['error' => 'Unauthorized', 'message' => 'Invalid or missing API key']);
    exit;
}

// Include scanner
require_once __DIR__ . '/../includes/RealTimeAdScanner.php';

// Parse request
$method = $_SERVER['REQUEST_METHOD'];
$path = $_SERVER['PATH_INFO'] ?? '';
$input = json_decode(file_get_contents('php://input'), true) ?? [];

// Initialize scanner
$scanner = new HighPerformanceAdScanner();

// Response helper
function respond($data, $statusCode = 200) {
    http_response_code($statusCode);
    echo json_encode($data, JSON_PRETTY_PRINT);
    exit;
}

// Route handling
try {
    switch ($path) {

        // POST /api/scanner/scan - Run a scan
        case '/scan':
            if ($method !== 'POST') {
                respond(['error' => 'Method not allowed'], 405);
            }

            $mode = $input['mode'] ?? 'incremental';
            $limit = $input['limit'] ?? 100;
            $adId = $input['ad_id'] ?? null;
            $companySlug = $input['company_slug'] ?? null;
            $categorySlug = $input['category_slug'] ?? null;

            switch ($mode) {
                case 'single':
                    if (!$adId) {
                        respond(['error' => 'ad_id required for single mode'], 400);
                    }
                    $result = $scanner->scanSingle($adId);
                    break;

                case 'company':
                    if (!$companySlug) {
                        respond(['error' => 'company_slug required for company mode'], 400);
                    }
                    $result = $scanner->scanByCompany($companySlug, $limit);
                    break;

                case 'category':
                    if (!$categorySlug) {
                        respond(['error' => 'category_slug required for category mode'], 400);
                    }
                    $result = $scanner->scanByCategory($categorySlug, $limit);
                    break;

                case 'priority':
                    $result = $scanner->scanPriority($limit);
                    break;

                case 'full':
                    $result = $scanner->scanFull($limit);
                    break;

                case 'incremental':
                default:
                    $sinceHours = $input['since_hours'] ?? 24;
                    $result = $scanner->scanIncremental($sinceHours);
                    break;
            }

            respond([
                'success' => true,
                'mode' => $mode,
                'result' => $result
            ]);
            break;

        // POST /api/scanner/enqueue - Enqueue ad for async scanning
        case '/enqueue':
            if ($method !== 'POST') {
                respond(['error' => 'Method not allowed'], 405);
            }

            $adId = $input['ad_id'] ?? null;
            $adIds = $input['ad_ids'] ?? null;
            $priority = $input['priority'] ?? 'normal';

            if ($adIds && is_array($adIds)) {
                // Bulk enqueue
                $result = $scanner->enqueueAds($adIds, $priority);
            } elseif ($adId) {
                // Single enqueue
                $result = $scanner->enqueueAd($adId, $priority);
            } else {
                respond(['error' => 'ad_id or ad_ids required'], 400);
            }

            respond($result);
            break;

        // GET /api/scanner/status - Get scanner status
        case '/status':
            if ($method !== 'GET') {
                respond(['error' => 'Method not allowed'], 405);
            }

            $scannerId = $_GET['scanner_id'] ?? null;

            if ($scannerId) {
                $result = $scanner->getScannerStatus($scannerId);
            } else {
                $result = [
                    'remote_service_available' => $scanner->isRemoteServiceAvailable(),
                    'health' => $scanner->getServiceHealth()
                ];
            }

            respond($result);
            break;

        // GET /api/scanner/stats - Get statistics
        case '/stats':
            if ($method !== 'GET') {
                respond(['error' => 'Method not allowed'], 405);
            }

            respond($scanner->getStatistics());
            break;

        // GET /api/scanner/health - Health check
        case '/health':
            $health = $scanner->getServiceHealth();
            $statusCode = ($health['status'] ?? '') === 'healthy' ? 200 : 503;
            respond($health, $statusCode);
            break;

        // POST /api/scanner/clear-cache - Clear cache
        case '/clear-cache':
            if ($method !== 'POST') {
                respond(['error' => 'Method not allowed'], 405);
            }

            $olderThanDays = $input['older_than_days'] ?? 0;

            ob_start();
            $scanner->clearCache($olderThanDays);
            $output = ob_get_clean();

            respond([
                'success' => true,
                'message' => trim($output)
            ]);
            break;

        // POST /api/scanner/start-daemon - Start background scanner
        case '/start-daemon':
            if ($method !== 'POST') {
                respond(['error' => 'Method not allowed'], 405);
            }

            $result = $scanner->startBackgroundScanner();
            respond($result);
            break;

        // POST /api/scanner/stop-daemon - Stop background scanner
        case '/stop-daemon':
            if ($method !== 'POST') {
                respond(['error' => 'Method not allowed'], 405);
            }

            $scannerId = $input['scanner_id'] ?? null;
            if (!$scannerId) {
                respond(['error' => 'scanner_id required'], 400);
            }

            $result = $scanner->stopBackgroundScanner($scannerId);
            respond($result);
            break;

        // Default - list available endpoints
        default:
            respond([
                'service' => 'AdSphere Scanner API',
                'version' => '3.0.0',
                'endpoints' => [
                    'POST /scan' => 'Run a scan (modes: single, incremental, priority, full, company, category)',
                    'POST /enqueue' => 'Enqueue ad(s) for async scanning',
                    'GET /status' => 'Get scanner status',
                    'GET /stats' => 'Get scan statistics',
                    'GET /health' => 'Health check',
                    'POST /clear-cache' => 'Clear scan cache',
                    'POST /start-daemon' => 'Start background scanner',
                    'POST /stop-daemon' => 'Stop background scanner',
                ],
                'documentation' => 'https://github.com/your-repo/docs/scanner-api.md'
            ]);
    }

} catch (Exception $e) {
    respond([
        'error' => 'Internal server error',
        'message' => $e->getMessage()
    ], 500);
}

