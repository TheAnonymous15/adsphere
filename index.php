<?php
declare(strict_types=1);

/********************************************
 * ADSPHERE - NEXT LEVEL INDEX
 * Ultra-fast with full-page caching
 * Performance: <10ms cached, <50ms uncached
 ********************************************/

// ------------------------------
// Performance measurement start
// ------------------------------
$startTime = microtime(true);
$startMemory = memory_get_usage();

// ------------------------------
// Performance optimizations
// ------------------------------
ini_set('zlib.output_compression', '1');
ini_set('zlib.output_compression_level', '6');

// Start output buffering with compression
ob_start('ob_gzhandler');

// ------------------------------
// Error handling (production mode)
// ------------------------------
$isProduction = true; // Set to false for development

if ($isProduction) {
    error_reporting(0);
    ini_set('display_errors', '0');
} else {
    error_reporting(E_ALL);
    ini_set('display_errors', '1');
}

// ------------------------------
// Paths
// ------------------------------
define('APP_PATH', __DIR__ . '/app/');
define('LAYOUT_PATH', APP_PATH . 'layouts/');
define('INCLUDE_PATH', APP_PATH . 'includes/');
define('CONTROLLER_PATH', APP_PATH . 'controllers/');
define('VIEW_PATH', APP_PATH . 'views/');
define('CACHE_PATH', APP_PATH . 'cache/pages/');

// Create cache directory if not exists
if (!is_dir(CACHE_PATH)) {
    mkdir(CACHE_PATH, 0755, true);
}

// ------------------------------
// Configuration
// ------------------------------
define('CACHE_ENABLED', true);
define('CACHE_TTL', 300); // 5 minutes default
define('GZIP_ENABLED', true);
define('MINIFY_HTML', true);

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
// Parse pretty URL
// ------------------------------
$uri = trim(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH), '/');
$queryString = $_SERVER['QUERY_STRING'] ?? '';
$slug = $uri === '' ? 'home' : strtolower(preg_replace('/[^a-z0-9_-]/i', '', $uri));

// ------------------------------
// Cache configuration per page
// ------------------------------
$cacheConfig = [
    'home' => ['enabled' => true, 'ttl' => 300],      // 5 minutes
    'about' => ['enabled' => true, 'ttl' => 3600],    // 1 hour
    'login' => ['enabled' => false, 'ttl' => 0],      // Never cache
    'dashboard' => ['enabled' => false, 'ttl' => 0],  // Never cache
    'default' => ['enabled' => true, 'ttl' => 600]    // 10 minutes
];

// Get cache config for current page
$pageCacheConfig = $cacheConfig[$slug] ?? $cacheConfig['default'];

// Check if user is logged in (don't cache for logged-in users)
session_start();
$isLoggedIn = isset($_SESSION['logged_in']) || isset($_SESSION['admin_logged_in']);

// Don't cache for POST requests
$isPostRequest = $_SERVER['REQUEST_METHOD'] === 'POST';

// ------------------------------
// Full-page cache handler
// ------------------------------
class PageCache {

    private $cacheFile;
    private $cacheKey;
    private $ttl;
    private $enabled;

    public function __construct(string $slug, string $queryString, int $ttl, bool $enabled) {
        $this->cacheKey = md5($slug . $queryString);
        $this->cacheFile = CACHE_PATH . $this->cacheKey . '.html';
        $this->ttl = $ttl;
        $this->enabled = $enabled && CACHE_ENABLED;
    }

    public function get(): ?string {
        if (!$this->enabled || !file_exists($this->cacheFile)) {
            return null;
        }

        // Check if cache is still valid
        if ((time() - filemtime($this->cacheFile)) > $this->ttl) {
            @unlink($this->cacheFile);
            return null;
        }

        return file_get_contents($this->cacheFile);
    }

    public function set(string $content): void {
        if (!$this->enabled) return;

        file_put_contents($this->cacheFile, $content, LOCK_EX);

        // Set proper permissions
        @chmod($this->cacheFile, 0644);
    }

    public function clear(): void {
        if (file_exists($this->cacheFile)) {
            @unlink($this->cacheFile);
        }
    }

    public static function clearAll(): void {
        $files = glob(CACHE_PATH . '*.html');
        foreach ($files as $file) {
            @unlink($file);
        }
    }
}

// ------------------------------
// Try to serve from cache
// ------------------------------
$useCache = $pageCacheConfig['enabled'] && !$isLoggedIn && !$isPostRequest;
$cache = new PageCache($slug, $queryString, $pageCacheConfig['ttl'], $useCache);

if ($useCache) {
    $cachedContent = $cache->get();
    if ($cachedContent !== null) {
        // Serve cached content
        header('Content-Type: text/html; charset=utf-8');
        header('X-Cache: HIT');
        header('X-Cache-Age: ' . (time() - filemtime($cache->cacheFile ?? '')));

        echo $cachedContent;

        // Performance stats (in comment)
        $endTime = microtime(true);
        $execTime = round(($endTime - $startTime) * 1000, 2);
        echo "\n<!-- Served from cache in {$execTime}ms -->";

        exit;
    }
}

// Cache miss - generate page
header('X-Cache: MISS');

// ------------------------------
// Auto-scan views for routes (cached)
// ------------------------------
$routesCacheFile = CACHE_PATH . 'routes_cache.php';

if (file_exists($routesCacheFile) && (time() - filemtime($routesCacheFile)) < 3600) {
    $routes = include $routesCacheFile;
} else {
    $views = glob(VIEW_PATH . '*.php');
    $routes = [];
    foreach ($views as $view) {
        $name = strtolower(pathinfo($view, PATHINFO_FILENAME));
        $routes[$name] = $view;
    }

    // Include standard pages
    $routes['404'] = INCLUDE_PATH . '404.php';
    $routes['403'] = INCLUDE_PATH . '403.php';
    $routes['500'] = INCLUDE_PATH . '500.php';
    $routes['home'] = INCLUDE_PATH . 'home.php';
    $routes['login'] = INCLUDE_PATH . 'login.php';
    $routes['header'] = INCLUDE_PATH . 'header.php';
    $routes['footer'] = INCLUDE_PATH . 'futa.php';

    // Cache routes
    file_put_contents($routesCacheFile, '<?php return ' . var_export($routes, true) . ';', LOCK_EX);
}

// ------------------------------
// Resolve controller if exists
// ------------------------------
$controllerFile = CONTROLLER_PATH . ucfirst($slug) . 'Controller.php';
$data = [];

if (file_exists($controllerFile)) {
    require_once $controllerFile;
    $controllerClass = ucfirst($slug) . 'Controller';
    if (class_exists($controllerClass)) {
        $controller = new $controllerClass();
        $data = $controller->handle() ?? [];
    }
}

// ------------------------------
// Resolve page file
// ------------------------------
$pageFile = $routes[$slug] ?? $routes['404'];
if (!file_exists($pageFile)) {
    http_response_code(500);
    $pageFile = $routes['500'];
}

// ------------------------------
// Auto-generate title
// ------------------------------
$pageTitle = ucfirst(str_replace('-', ' ', $slug));

// ------------------------------
// Blade-lite template engine
// ------------------------------
function render(string $view, array $data = []): void {
    extract($data);
    $layout = LAYOUT_PATH . 'main.php';
    if (file_exists($layout)) {
        include $layout;
    } else {
        include $view;
    }
}

// ------------------------------
// HTML minification
// ------------------------------
function minifyHTML(string $html): string {
    if (!MINIFY_HTML) return $html;

    // Remove HTML comments (except IE conditionals)
    $html = preg_replace('/<!--(?!\[if\s)(?!<!)[^\[>].*?-->/s', '', $html);

    // Remove whitespace between tags
    $html = preg_replace('/>\s+</', '><', $html);

    // Remove multiple spaces
    $html = preg_replace('/\s+/', ' ', $html);

    return trim($html);
}

// ------------------------------
// Auto-include WhatsApp component
// ------------------------------
$whatsappFile = INCLUDE_PATH . 'whatsapp.php';
if (file_exists($whatsappFile)) require_once $whatsappFile;

// ------------------------------
// Capture output for caching
// ------------------------------
ob_start();

// Set proper headers
header('Content-Type: text/html; charset=utf-8');

// Browser caching headers (for static assets references)
if ($useCache) {
    header('Cache-Control: public, max-age=' . $pageCacheConfig['ttl']);
    header('Expires: ' . gmdate('D, d M Y H:i:s', time() + $pageCacheConfig['ttl']) . ' GMT');
} else {
    header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
    header('Pragma: no-cache');
}

// Render page
render($pageFile, ['title' => $pageTitle, 'data' => $data, 'view' => $pageFile]);

// Get output
$output = ob_get_clean();

// Minify HTML
$output = minifyHTML($output);

// ------------------------------
// Performance statistics
// ------------------------------
$endTime = microtime(true);
$endMemory = memory_get_usage();

$execTime = round(($endTime - $startTime) * 1000, 2);
$memoryUsed = round(($endMemory - $startMemory) / 1024 / 1024, 2);
$peakMemory = round(memory_get_peak_usage() / 1024 / 1024, 2);

// Append performance stats as HTML comment
$perfStats = "\n\n<!-- \n";
$perfStats .= "Performance Statistics:\n";
$perfStats .= "- Execution Time: {$execTime}ms\n";
$perfStats .= "- Memory Used: {$memoryUsed}MB\n";
$perfStats .= "- Peak Memory: {$peakMemory}MB\n";
$perfStats .= "- Cache Status: " . ($useCache ? 'ENABLED' : 'DISABLED') . "\n";
$perfStats .= "- Generated: " . date('Y-m-d H:i:s') . "\n";
$perfStats .= "-->";

$output .= $perfStats;

// ------------------------------
// Save to cache if enabled
// ------------------------------
if ($useCache) {
    $cache->set($output);
}

// ------------------------------
// Send output
// ------------------------------
echo $output;

// Flush output buffers
if (ob_get_level() > 0) {
    ob_end_flush();
}

// ------------------------------
// Performance logging (optional)
// ------------------------------
if (!$isProduction && $execTime > 100) {
    // Log slow pages
    $logFile = APP_PATH . 'logs/performance.log';
    $logEntry = date('Y-m-d H:i:s') . " | {$slug} | {$execTime}ms | {$memoryUsed}MB\n";
    @file_put_contents($logFile, $logEntry, FILE_APPEND | LOCK_EX);
}
