<?php
/**
 * Admin Service - API Router
 * Handles all /api/* requests
 */

// Load path configuration
require_once dirname(dirname(__DIR__)) . '/python_shared/config/paths.php';

$requestUri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$apiPath = str_replace('/api/', '', $requestUri);
$apiPath = rtrim($apiPath, '/');

header('Content-Type: application/json');

// Check admin authentication for all API calls
if (!isset($_SESSION['admin_logged_in']) || $_SESSION['admin_logged_in'] !== true) {
    http_response_code(401);
    echo json_encode(['success' => false, 'error' => 'Unauthorized']);
    exit();
}

// API routing
switch ($apiPath) {
    case 'stats':
    case 'admin_stats':
        // Get admin statistics
        require SHARED_PATH . '/api/dashboard_stats.php';
        break;

    case 'ads':
    case 'get_ads':
        require SHARED_PATH . '/api/get_ads.php';
        break;

    case 'companies':
    case 'get_companies':
        require SHARED_PATH . '/api/get_companies.php';
        break;

    case 'categories':
    case 'get_categories':
        require SHARED_PATH . '/api/get_categories.php';
        break;

    case 'analytics':
    case 'get_analytics':
        require SHARED_PATH . '/api/get_analytics.php';
        break;

    case 'scanner/run':
        // Trigger ad scanner
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            require SHARED_PATH . '/api/scanner.php';
        } else {
            http_response_code(405);
            echo json_encode(['success' => false, 'error' => 'Method not allowed']);
        }
        break;

    case 'scanner':
        // Scanner with action parameter (scan, report)
        $_GET['action'] = $_GET['action'] ?? 'report';
        require BASE_PATH . '/python_shared/api/scanner.php';
        break;

    case 'moderation_violations':
        // Moderation violations endpoint
        require BASE_PATH . '/python_shared/api/moderation_violations.php';
        break;

    case 'moderation/flagged':
        // Get flagged content
        $flaggedFile = BASE_PATH . '/python_shared/data/flagged_ads.json';
        if (file_exists($flaggedFile)) {
            echo file_get_contents($flaggedFile);
        } else {
            echo json_encode(['success' => true, 'data' => []]);
        }
        break;

    case 'moderation/action':
        // Take moderation action
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $input = json_decode(file_get_contents('php://input'), true);
            $adId = $input['ad_id'] ?? '';
            $action = $input['action'] ?? '';

            if ($adId && $action) {
                // Log moderation action
                $logFile = BASE_PATH . '/python_admin/logs/moderation_' . date('Y-m-d') . '.log';
                $logEntry = [
                    'timestamp' => date('c'),
                    'admin' => $_SESSION['admin_username'] ?? 'unknown',
                    'ad_id' => $adId,
                    'action' => $action
                ];
                file_put_contents($logFile, json_encode($logEntry) . "\n", FILE_APPEND);

                echo json_encode(['success' => true, 'message' => "Action '$action' applied to ad $adId"]);
            } else {
                http_response_code(400);
                echo json_encode(['success' => false, 'error' => 'Missing ad_id or action']);
            }
        }
        break;

    case 'verify-2fa':
        // 2FA verification endpoint
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            $input = json_decode(file_get_contents('php://input'), true);
            $code = $input['code'] ?? '';

            // Verification logic handled by 2fa.php page
            echo json_encode(['success' => false, 'error' => 'Use /2fa page for verification']);
        }
        break;

    case 'logout':
        session_destroy();
        echo json_encode(['success' => true, 'message' => 'Logged out']);
        break;

    case 'session':
        // Get session info
        echo json_encode([
            'success' => true,
            'data' => [
                'username' => $_SESSION['admin_username'] ?? null,
                'role' => $_SESSION['admin_role'] ?? null,
                '2fa_verified' => $_SESSION['admin_2fa_verified'] ?? false,
                'last_activity' => $_SESSION['admin_last_activity'] ?? null
            ]
        ]);
        break;

    default:
        http_response_code(404);
        echo json_encode(['success' => false, 'error' => 'API endpoint not found: ' . $apiPath]);
        break;
}

