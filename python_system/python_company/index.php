<?php
/**
 * ============================================================================
 * COMPANY PORTAL SERVICE - Port 8003
 * ============================================================================
 *
 * Entry point for company users (advertisers)
 * Requires company authentication
 *
 * Start: php -S localhost:8003 -t services/company
 * ============================================================================
 */

session_start();

// Service configuration
define('SERVICE_NAME', 'company');
define('SERVICE_PORT', 8003);
// Load path configuration
require_once dirname(__DIR__) . '/python_shared/config/paths.php';

// Include shared utilities
require_once SHARED_PATH . '/bootstrap.php';

// Router
$requestUri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$requestUri = rtrim($requestUri, '/') ?: '/';

// Public routes (no auth required)
$publicRoutes = ['/login', '/login.php', '/register', '/health', '/api/auth', '/forgot-password'];

// Check authentication for protected routes
if (!in_array($requestUri, $publicRoutes) && strpos($requestUri, '/assets') !== 0) {
    if (!isset($_SESSION['company']) || !isset($_SESSION['company_logged_in'])) {
        header('Location: /login');
        exit();
    }

    // Session timeout (2 hours)
    if (isset($_SESSION['company_last_activity']) && (time() - $_SESSION['company_last_activity']) > 7200) {
        session_destroy();
        header('Location: /login?timeout=1');
        exit();
    }
    $_SESSION['company_last_activity'] = time();
}

// Get company info for authenticated routes
$companySlug = $_SESSION['company'] ?? null;
$companyName = $_SESSION['company_name'] ?? 'Company';

// Route handling
switch (true) {
    // Login
    case $requestUri === '/' && !isset($_SESSION['company']):
    case $requestUri === '/login' || $requestUri === '/login.php':
        require __DIR__ . '/pages/login.php';
        break;

    // Register
    case $requestUri === '/register':
        require __DIR__ . '/pages/register.php';
        break;

    // Forgot password
    case $requestUri === '/forgot-password':
        require __DIR__ . '/pages/forgot_password.php';
        break;

    // Dashboard (default after login)
    case $requestUri === '/' || $requestUri === '/dashboard':
        require __DIR__ . '/pages/dashboard.php';
        break;

    // My Ads
    case $requestUri === '/ads' || $requestUri === '/my-ads':
        require __DIR__ . '/pages/my_ads.php';
        break;

    // Upload new ad
    case $requestUri === '/upload' || $requestUri === '/new-ad':
        require __DIR__ . '/pages/upload_ad.php';
        break;

    // Edit ad
    case preg_match('/^\/edit\/([a-zA-Z0-9\-_]+)$/', $requestUri, $matches):
        $_GET['id'] = $matches[1];
        require __DIR__ . '/pages/edit_ad.php';
        break;

    // Analytics
    case $requestUri === '/analytics':
        require __DIR__ . '/pages/analytics.php';
        break;

    // Profile
    case $requestUri === '/profile':
        require __DIR__ . '/pages/profile.php';
        break;

    // Settings
    case $requestUri === '/settings':
        require __DIR__ . '/pages/settings.php';
        break;

    // Notifications
    case $requestUri === '/notifications':
        require __DIR__ . '/pages/notifications.php';
        break;

    // Logout
    case $requestUri === '/logout':
        session_destroy();
        header('Location: /login');
        exit();
        break;

    // API endpoints
    case strpos($requestUri, '/api/') === 0:
        require __DIR__ . '/api/router.php';
        break;

    // Static assets from shared assets directory
    case strpos($requestUri, '/services/assets/') === 0:
    case strpos($requestUri, '/assets/') === 0:
        $assetPath = $requestUri;
        if (strpos($assetPath, '/services/assets/') === 0) {
            $assetPath = str_replace('/services/assets/', '/assets/', $assetPath);
        }
        $filePath = BASE_PATH . '/services' . $assetPath;
        if (file_exists($filePath)) {
            $mimeTypes = [
                'css' => 'text/css',
                'js' => 'application/javascript',
                'png' => 'image/png',
                'jpg' => 'image/jpeg',
                'jpeg' => 'image/jpeg',
                'gif' => 'image/gif',
                'ico' => 'image/x-icon',
                'svg' => 'image/svg+xml',
                'woff' => 'font/woff',
                'woff2' => 'font/woff2',
                'webp' => 'image/webp',
                'mp4' => 'video/mp4',
                'webm' => 'video/webm'
            ];
            $ext = strtolower(pathinfo($filePath, PATHINFO_EXTENSION));
            $mime = $mimeTypes[$ext] ?? 'application/octet-stream';
            header('Content-Type: ' . $mime);
            header('Cache-Control: public, max-age=86400');
            readfile($filePath);
            exit();
        }
        http_response_code(404);
        echo "Asset not found";
        exit();

    // Local static assets (fallback)
    case preg_match('/\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2)$/', $requestUri):
        return false;

    // Health check
    case $requestUri === '/health':
        header('Content-Type: application/json');
        echo json_encode([
            'status' => 'healthy',
            'service' => SERVICE_NAME,
            'port' => SERVICE_PORT,
            'authenticated' => isset($_SESSION['company']),
            'company' => $companySlug,
            'timestamp' => date('c')
        ]);
        exit();

    // 404
    default:
        http_response_code(404);
        require __DIR__ . '/pages/404.php';
        break;
}

