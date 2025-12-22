<?php
/**
 * ============================================================================
 * PLATFORM ADMIN SERVICE - Port 8002
 * ============================================================================
 *
 * Entry point for platform administrators
 * Requires admin authentication + 2FA
 *
 * Start: php -S localhost:8002 -t services/admin
 * ============================================================================
 */

session_start();

// Service configuration
define('SERVICE_NAME', 'admin');
define('SERVICE_PORT', 8002);
define('BASE_PATH', dirname(dirname(__DIR__)));

// Include shared utilities
require_once BASE_PATH . '/services/shared/bootstrap.php';

// Router
$requestUri = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$requestUri = rtrim($requestUri, '/') ?: '/';

// Public routes (no auth required)
$publicRoutes = ['/login', '/login.php', '/health', '/api/auth', '/handlers/verify-2fa'];

// Routes that allow pending 2FA state (password verified but 2FA not yet complete)
$pending2faRoutes = ['/2fa'];

// Check authentication for protected routes
if (!in_array($requestUri, $publicRoutes) && strpos($requestUri, '/assets') !== 0) {

    // Check if user has pending 2FA (password verified, awaiting 2FA)
    $hasPending2fa = isset($_SESSION['pending_2fa_setup']) || isset($_SESSION['pending_2fa']);
    $isLoggedIn = isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in'] === true;

    // Allow access to 2FA page if user has pending 2FA
    if (in_array($requestUri, $pending2faRoutes) && $hasPending2fa) {
        // Allow through - user is in 2FA setup/verification flow
    }
    // Otherwise require full login
    elseif (!$isLoggedIn && !$hasPending2fa) {
        header('Location: /login');
        exit();
    }
    // If logged in but not 2FA verified, redirect to 2FA
    elseif ($isLoggedIn && (!isset($_SESSION['admin_2fa_verified']) || $_SESSION['admin_2fa_verified'] !== true)) {
        if (!in_array($requestUri, $pending2faRoutes) && strpos($requestUri, '/handlers/') !== 0) {
            header('Location: /2fa');
            exit();
        }
    }

    // Session timeout (1 hour) - only for fully logged in users
    if ($isLoggedIn && isset($_SESSION['admin_last_activity']) && (time() - $_SESSION['admin_last_activity']) > 3600) {
        session_destroy();
        header('Location: /login?timeout=1');
        exit();
    }
    if ($isLoggedIn) {
        $_SESSION['admin_last_activity'] = time();
    }
}

// Route handling
switch (true) {
    // Login
    case $requestUri === '/' && !isset($_SESSION['admin_logged_in']):
    case $requestUri === '/login' || $requestUri === '/login.php':
        require __DIR__ . '/pages/login.php';
        break;

    // 2FA Setup/Verify
    case $requestUri === '/2fa':
        require __DIR__ . '/pages/2fa.php';
        break;

    // Dashboard (default after login)
    case $requestUri === '/' || $requestUri === '/dashboard':
        require __DIR__ . '/pages/dashboard.php';
        break;

    // Companies management
    case $requestUri === '/companies':
        require __DIR__ . '/pages/companies.php';
        break;

    // Ads management
    case $requestUri === '/ads':
        require __DIR__ . '/pages/ads.php';
        break;

    // Content moderation
    case $requestUri === '/moderation':
        require __DIR__ . '/pages/moderation.php';
        break;

    // Flagged content
    case $requestUri === '/flagged':
        require __DIR__ . '/pages/flagged.php';
        break;

    // Ad scanner
    case $requestUri === '/scanner':
        require __DIR__ . '/pages/scanner.php';
        break;

    // Categories
    case $requestUri === '/categories':
        require __DIR__ . '/pages/categories.php';
        break;

    // Analytics
    case $requestUri === '/analytics':
        require __DIR__ . '/pages/analytics.php';
        break;

    // Admin users
    case $requestUri === '/users':
        require __DIR__ . '/pages/users.php';
        break;

    // Settings
    case $requestUri === '/settings':
        require __DIR__ . '/pages/settings.php';
        break;

    // System logs
    case $requestUri === '/logs':
        require __DIR__ . '/pages/logs.php';
        break;

    // Logout
    case $requestUri === '/logout':
        session_destroy();
        header('Location: /login');
        exit();

    // Handlers (setup, verification, etc.)
    case strpos($requestUri, '/handlers/') === 0:
        $handler = basename($requestUri);
        $handlerFile = __DIR__ . '/handlers/' . $handler . '.php';
        if (file_exists($handlerFile)) {
            require $handlerFile;
        } else {
            http_response_code(404);
            echo json_encode(['error' => 'Handler not found']);
        }
        break;

    // API endpoints
    case strpos($requestUri, '/api/') === 0:
        require __DIR__ . '/api/router.php';
        break;

    // Static assets from shared assets directory
    case strpos($requestUri, '/services/assets/') === 0:
    case strpos($requestUri, '/assets/') === 0:
        $assetPath = $requestUri;
        // Normalize path - both /services/assets/ and /assets/ point to same location
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
            'authenticated' => isset($_SESSION['admin_logged_in']),
            '2fa_verified' => isset($_SESSION['admin_2fa_verified']) && $_SESSION['admin_2fa_verified'],
            'timestamp' => date('c')
        ]);
        exit();

    // 404
    default:
        http_response_code(404);
        require __DIR__ . '/pages/404.php';
        break;
}

