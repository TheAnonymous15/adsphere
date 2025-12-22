<?php
declare(strict_types=1);

/********************************************
 * ADSPHERE PUBLIC SERVICE - INDEX
 * Port 8001 - Public ad browsing
 ********************************************/

// ------------------------------
// Performance measurement start
// ------------------------------
$startTime = microtime(true);
$startMemory = memory_get_usage();

// ------------------------------
// Output compression
// ------------------------------
if (!ini_get('zlib.output_compression')) {
    ini_set('zlib.output_compression', '1');
    ini_set('zlib.output_compression_level', '6');
}

// ------------------------------
// Error handling
// ------------------------------
$isProduction = false;

if ($isProduction) {
    error_reporting(0);
    ini_set('display_errors', '0');
} else {
    error_reporting(E_ALL);
    ini_set('display_errors', '1');
}

// ------------------------------
// Paths - Fixed for services/public structure
// ------------------------------
define('BASE_PATH', dirname(dirname(__DIR__))); // /adsphere
define('SERVICE_PATH', __DIR__); // /adsphere/services/public
define('INCLUDE_PATH', SERVICE_PATH . '/includes/');
define('PAGES_PATH', SERVICE_PATH . '/pages/');
define('CACHE_PATH', SERVICE_PATH . '/app/cache/pages/');
define('ASSETS_PATH', '/services/assets/');

if (!is_dir(CACHE_PATH)) {
    @mkdir(CACHE_PATH, 0755, true);
}

// ------------------------------
// Config
// ------------------------------
define('CACHE_ENABLED', true);
define('CACHE_TTL', 300);
define('MINIFY_HTML', true);

session_start();

// ------------------------------
// Maintenance mode
// ------------------------------
$maintenanceMode = 0;

if ($maintenanceMode === 1) {
    http_response_code(503);
    require INCLUDE_PATH . 'maintenance.php';
    exit;
}

// ------------------------------
// URL parse
// ------------------------------
$uri = trim(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH), '/');
$queryString = $_SERVER['QUERY_STRING'] ?? '';

// Handle API requests separately
if (strpos($uri, 'api/') === 0) {
    $apiEndpoint = substr($uri, 4); // Remove 'api/'
    $apiFile = BASE_PATH . '/services/api/' . basename($apiEndpoint) . '.php';
    if (file_exists($apiFile)) {
        require $apiFile;
        exit;
    }
    http_response_code(404);
    header('Content-Type: application/json');
    echo json_encode(['error' => 'API endpoint not found']);
    exit;
}

// Handle static assets (images, videos, css, js, fonts)
if (preg_match('/\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|webp|webm|mp4|mov|mp3|wav|pdf)$/i', $uri)) {
    // Try multiple asset locations
    $assetLocations = [
        BASE_PATH . '/' . $uri,                      // Direct path: /services/assets/...
        BASE_PATH . '/services/assets/' . $uri,      // Prefixed path
        SERVICE_PATH . '/assets/' . $uri,            // Public service assets
        BASE_PATH . '/services/' . $uri,             // Services relative
    ];

    // Remove /services/assets prefix if present in URI
    $cleanUri = preg_replace('#^/?services/assets/#', '', $uri);
    $assetLocations[] = BASE_PATH . '/services/assets/' . $cleanUri;

    foreach ($assetLocations as $assetFile) {
        if (file_exists($assetFile)) {
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
                'webm' => 'video/webm',
                'mp4' => 'video/mp4',
                'mov' => 'video/quicktime',
                'mp3' => 'audio/mpeg',
                'wav' => 'audio/wav',
                'pdf' => 'application/pdf'
            ];
            $ext = strtolower(pathinfo($assetFile, PATHINFO_EXTENSION));
            header('Content-Type: ' . ($mimeTypes[$ext] ?? 'application/octet-stream'));
            header('Cache-Control: public, max-age=86400');
            header('Content-Length: ' . filesize($assetFile));
            readfile($assetFile);
            exit;
        }
    }
    return false; // Let PHP built-in server handle it
}

// Parse slug for page routing
$slug = $uri === '' ? 'home' : strtolower(preg_replace('/[^a-z0-9_-]/i', '', explode('/', $uri)[0]));

// Special routes
$adMatch = [];
if (preg_match('/^ad\/([a-zA-Z0-9\-_]+)$/', $uri, $adMatch)) {
    $slug = 'ad_page';
    $_GET['id'] = $adMatch[1];
}

$categoryMatch = [];
if (preg_match('/^category\/([a-zA-Z0-9\-_]+)$/', $uri, $categoryMatch)) {
    $slug = 'category';
    $_GET['category'] = $categoryMatch[1];
}

if ($uri === 'search' || strpos($uri, 'search') === 0) {
    $slug = 'browse';
}

if ($uri === 'ads' || $uri === 'browse') {
    $slug = 'browse';
}

if ($uri === 'categories') {
    $slug = 'categories';
}

// ------------------------------
// Cache config per page
// ------------------------------
$cacheConfig = [
    'home' => ['enabled' => true, 'ttl' => 300],
    'browse' => ['enabled' => true, 'ttl' => 120],
    'ad_page' => ['enabled' => true, 'ttl' => 180],
    'categories' => ['enabled' => true, 'ttl' => 600],
    'category' => ['enabled' => true, 'ttl' => 300],
    'default' => ['enabled' => true, 'ttl' => 300]
];

$pageCacheConfig = $cacheConfig[$slug] ?? $cacheConfig['default'];

$isLoggedIn = !empty($_SESSION['logged_in']) || !empty($_SESSION['admin_logged_in']);
$isPostRequest = $_SERVER['REQUEST_METHOD'] === 'POST';

// ------------------------------
// Full page cache handler
// ------------------------------
class PageCache {
    private string $cacheFile;
    private int $ttl;
    private bool $enabled;

    public function __construct(string $slug, string $queryString, int $ttl, bool $enabled) {
        $cacheKey = md5($slug . $queryString);
        $this->cacheFile = CACHE_PATH . $cacheKey . '.html';
        $this->ttl = $ttl;
        $this->enabled = $enabled && CACHE_ENABLED;
    }

    public function get(): ?string {
        if (!$this->enabled || !file_exists($this->cacheFile)) return null;

        if ((time() - filemtime($this->cacheFile)) > $this->ttl) {
            @unlink($this->cacheFile);
            return null;
        }

        return file_get_contents($this->cacheFile);
    }

    public function set(string $content): void {
        if (!$this->enabled) return;
        file_put_contents($this->cacheFile, $content, LOCK_EX);
        @chmod($this->cacheFile, 0644);
    }

    public function lastModified(): ?int {
        return file_exists($this->cacheFile) ? filemtime($this->cacheFile) : null;
    }
}

// ------------------------------
// Cache serve attempt
// ------------------------------
$useCache = $pageCacheConfig['enabled'] && !$isLoggedIn && !$isPostRequest;
$cache = new PageCache($slug, $queryString, $pageCacheConfig['ttl'], $useCache);

if ($useCache) {
    $cachedContent = $cache->get();

    if ($cachedContent !== null) {
        header('Content-Type: text/html; charset=utf-8');
        header('X-Cache: HIT');
        $age = time() - ($cache->lastModified() ?? time());
        header('X-Cache-Age: ' . $age);
        echo $cachedContent;
        $endTime = microtime(true);
        $execTime = round(($endTime - $startTime) * 1000, 2);
        echo "\n<!-- Served from cache in {$execTime}ms -->";
        exit;
    }
}

header('X-Cache: MISS');

// ------------------------------
// Route definitions
// ------------------------------
$routes = [
    // Main pages (from includes/)
    'home' => INCLUDE_PATH . 'home.php',
    'ad_page' => INCLUDE_PATH . 'ad_page.php',
    'ads' => INCLUDE_PATH . 'ads.php',

    // Pages (from pages/)
    'browse' => PAGES_PATH . 'browse.php',

    // Error pages
    '404' => INCLUDE_PATH . '404.php',
    '403' => INCLUDE_PATH . '403.php',
    '500' => INCLUDE_PATH . '500.php',

    // Auth pages (redirect to company service)
    'login' => INCLUDE_PATH . 'login.php',

    // Components
    'header' => INCLUDE_PATH . 'header.php',
    'footer' => INCLUDE_PATH . 'footer.php',

    // Terms
    'terms' => INCLUDE_PATH . 'terms_of_service.php',
];

// ------------------------------
// Resolve page file
// ------------------------------
$pageFile = $routes[$slug] ?? null;

// Check pages directory if not in routes
if (!$pageFile || !file_exists($pageFile)) {
    $pageFile = PAGES_PATH . $slug . '.php';
}

// Check includes directory
if (!file_exists($pageFile)) {
    $pageFile = INCLUDE_PATH . $slug . '.php';
}

// Fallback to 404
if (!file_exists($pageFile)) {
    http_response_code(404);
    $pageFile = $routes['404'];
}

$pageTitle = ucfirst(str_replace(['-', '_'], ' ', $slug)) . ' - AdSphere';

// ------------------------------
// HTML minifier
// ------------------------------
function minifyHTML(string $html): string {
    if (!MINIFY_HTML) return $html;

    return preg_replace_callback(
        '#<(script|style)\b[^>]*>.*?</\1>|<!--.*?-->|[^<]+#si',
        function ($m) {
            if ($m[0][0] !== '<') {
                return preg_replace('/\s+/', ' ', $m[0]);
            }
            return $m[0];
        },
        $html
    );
}

// ------------------------------
// Begin capture and render
// ------------------------------
ob_start();

header('Content-Type: text/html; charset=utf-8');

if ($useCache) {
    header('Cache-Control: public, max-age=' . $pageCacheConfig['ttl']);
} else {
    header('Cache-Control: no-cache, no-store, must-revalidate');
}

// Include the page
require $pageFile;

$output = ob_get_clean();
$output = minifyHTML($output);

// Performance stats
$endTime = microtime(true);
$execTime = round(($endTime - $startTime) * 1000, 2);
$memoryUsed = round((memory_get_usage() - $startMemory) / 1024 / 1024, 2);
$peakMemory = round(memory_get_peak_usage() / 1024 / 1024, 2);

$output .= "\n\n<!--
Perf:
Exec: {$execTime}ms
Memory: {$memoryUsed}MB
Peak: {$peakMemory}MB
Cache: " . ($useCache ? 'ENABLED' : 'DISABLED') . "
Time: " . date('Y-m-d H:i:s') . "
-->";

// Save to cache
if ($useCache) {
    $cache->set($output);
}

echo $output;

?>
