sun<?php
/**
 * ============================================================================
 * COMPANY SERVICE - API Router
 * ============================================================================
 * Handles all /api/* requests for the company portal
 */

// Define paths
if (!defined('BASE_PATH')) {
    define('BASE_PATH', dirname(dirname(dirname(__DIR__))));
}

$requestUri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$apiPath = str_replace('/api/', '', $requestUri);
$apiPath = rtrim($apiPath, '/');

header('Content-Type: application/json');

// Check company authentication for most API calls
$publicApis = ['auth', 'login', 'register'];
if (!in_array($apiPath, $publicApis)) {
    if (!isset($_SESSION['company']) || !isset($_SESSION['company_logged_in'])) {
        http_response_code(401);
        echo json_encode(['success' => false, 'error' => 'Unauthorized']);
        exit();
    }
}

// Get company info
$companySlug = $_SESSION['company'] ?? null;

// API routing
switch ($apiPath) {
    // Get ads (filtered by company)
    case 'get_ads':
        // Force company filter for security
        $_GET['company'] = $companySlug;
        require BASE_PATH . '/services/api/get_ads.php';
        break;

    // Dashboard statistics
    case 'dashboard_stats':
        require BASE_PATH . '/services/api/dashboard_stats.php';
        break;

    // Live activity feed
    case 'live_activity':
        require BASE_PATH . '/services/api/live_activity.php';
        break;

    // Contact analytics
    case 'contact_analytics':
        require BASE_PATH . '/services/api/contact_analytics.php';
        break;

    // Get analytics
    case 'analytics':
    case 'get_analytics':
        require BASE_PATH . '/services/api/get_analytics.php';
        break;

    // Delete ad
    case 'delete_ad':
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            require BASE_PATH . '/services/api/delete_ad.php';
        } else {
            http_response_code(405);
            echo json_encode(['success' => false, 'error' => 'Method not allowed']);
        }
        break;

    // Update ad status
    case 'update_ad_status':
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            require BASE_PATH . '/services/api/update_ad_status.php';
        } else {
            http_response_code(405);
            echo json_encode(['success' => false, 'error' => 'Method not allowed']);
        }
        break;

    // Duplicate ad
    case 'duplicate_ad':
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            require BASE_PATH . '/services/api/duplicate_ad.php';
        } else {
            http_response_code(405);
            echo json_encode(['success' => false, 'error' => 'Method not allowed']);
        }
        break;

    // Schedule ad
    case 'schedule_ad':
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            require BASE_PATH . '/services/api/schedule_ad.php';
        } else {
            http_response_code(405);
            echo json_encode(['success' => false, 'error' => 'Method not allowed']);
        }
        break;

    // Track events (views, clicks, etc.)
    case 'track_event':
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            require BASE_PATH . '/services/api/track_event.php';
        } else {
            http_response_code(405);
            echo json_encode(['success' => false, 'error' => 'Method not allowed']);
        }
        break;

    // Track interactions
    case 'track_interaction':
        if ($_SERVER['REQUEST_METHOD'] === 'POST') {
            require BASE_PATH . '/services/api/track_interaction.php';
        } else {
            http_response_code(405);
            echo json_encode(['success' => false, 'error' => 'Method not allowed']);
        }
        break;

    // Get categories
    case 'categories':
    case 'get_categories':
        require BASE_PATH . '/services/api/get_categories.php';
        break;

    // Session info
    case 'session':
        echo json_encode([
            'success' => true,
            'data' => [
                'company' => $companySlug,
                'company_name' => $_SESSION['company_name'] ?? null,
                'email' => $_SESSION['company_email'] ?? null,
                'logged_in' => isset($_SESSION['company_logged_in']),
                'login_time' => $_SESSION['login_time'] ?? null
            ]
        ]);
        break;

    // Logout
    case 'logout':
        session_destroy();
        echo json_encode(['success' => true, 'message' => 'Logged out']);
        break;

    // Health check
    case 'health':
        echo json_encode([
            'status' => 'healthy',
            'service' => 'company',
            'authenticated' => isset($_SESSION['company']),
            'timestamp' => date('c')
        ]);
        break;

    // Default - endpoint not found
    default:
        http_response_code(404);
        echo json_encode([
            'success' => false,
            'error' => 'API endpoint not found: ' . $apiPath,
            'available_endpoints' => [
                'GET /api/get_ads' => 'Get company ads',
                'GET /api/dashboard_stats' => 'Get dashboard statistics',
                'GET /api/live_activity' => 'Get live activity feed',
                'GET /api/contact_analytics' => 'Get contact analytics',
                'GET /api/get_analytics' => 'Get ad analytics',
                'POST /api/delete_ad' => 'Delete an ad',
                'POST /api/update_ad_status' => 'Update ad status',
                'POST /api/duplicate_ad' => 'Duplicate an ad',
                'POST /api/schedule_ad' => 'Schedule an ad',
                'GET /api/categories' => 'Get categories',
                'GET /api/session' => 'Get session info',
                'GET /api/health' => 'Health check'
            ]
        ]);
        break;
}

