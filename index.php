<?php
declare(strict_types=1);

/********************************************
 * ADSPHERE - FIXED INDEX (SAFE + STABLE)
 ********************************************/

// ------------------------------
// Performance measurement start
// ------------------------------
$startTime = microtime(true);
$startMemory = memory_get_usage();

// ------------------------------
// Output compression
// zlib = ON, so DO NOT use manual gzip
// ------------------------------
ini_set('zlib.output_compression', '1');
ini_set('zlib.output_compression_level', '6');

// 🟢 REMOVE FIRST ob_start() – double buffering issue fixed

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
// paths
// ------------------------------
define('APP_PATH', __DIR__ . '/app/');
define('LAYOUT_PATH', APP_PATH . 'layouts/');
define('INCLUDE_PATH', APP_PATH . 'includes/');
define('CONTROLLER_PATH', APP_PATH . 'controllers/');
define('VIEW_PATH', APP_PATH . 'views/');
define('CACHE_PATH', APP_PATH . 'cache/pages/');

if (!is_dir(CACHE_PATH)) {
    @mkdir(CACHE_PATH, 0755, true);
}

// ------------------------------
// config
// ------------------------------
define('CACHE_ENABLED', true);
define('CACHE_TTL', 300);
define('MINIFY_HTML', true);

session_start();

// ------------------------------
// maintenance
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
$slug = $uri === '' ? 'home' : strtolower(preg_replace('/[^a-z0-9_-]/i', '', $uri));

// ------------------------------
// cache config
// ------------------------------
$cacheConfig = [
    'home' => ['enabled' => true, 'ttl' => 300],
    'about' => ['enabled' => true, 'ttl' => 3600],
    'login' => ['enabled' => false, 'ttl' => 0],
    'dashboard' => ['enabled' => false, 'ttl' => 0],
    'default' => ['enabled' => true, 'ttl' => 600]
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
// cache serve attempt
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
// Load routes cache
// ------------------------------
$routesCacheFile = CACHE_PATH . 'routes_cache.php';

if (file_exists($routesCacheFile) && (time() - filemtime($routesCacheFile)) < 3600) {
    $routes = include $routesCacheFile;
} else {
    $routes = [];

    foreach (glob(VIEW_PATH . '*.php') as $view) {
        $name = strtolower(pathinfo($view, PATHINFO_FILENAME));
        $routes[$name] = $view;
    }

    $routes = array_merge($routes, [
        '404' => INCLUDE_PATH . '404.php',
        '403' => INCLUDE_PATH . '403.php',
        '500' => INCLUDE_PATH . '500.php',
        'home' => INCLUDE_PATH . 'home_unified.php',
        'login' => INCLUDE_PATH . 'login.php',
        'header' => INCLUDE_PATH . 'header.php',
        'footer' => INCLUDE_PATH . 'footer.php'
    ]);

    file_put_contents($routesCacheFile, '<?php return ' . var_export($routes, true) . ';');
}

// ------------------------------
// controller resolve
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
// resolve page
// ------------------------------
$pageFile = $routes[$slug] ?? $routes['404'];

if (!file_exists($pageFile)) {
    http_response_code(500);
    $pageFile = $routes['500'];
}

$pageTitle = ucfirst(str_replace('-', ' ', $slug));

// ------------------------------
// template renderer
// ------------------------------
function render(string $view, array $data = []): void {
    extract($data);
    $layout = LAYOUT_PATH . 'main.php';

    if (file_exists($layout)) include $layout;
    else include $view;
}

// ------------------------------
// HTML minifier safe version
// avoids minifying inside script/style
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
// begin capture
// ------------------------------
ob_start();

header('Content-Type: text/html; charset=utf-8');

if ($useCache) {
    header('Cache-Control: public, max-age=' . $pageCacheConfig['ttl']);
} else {
    header('Cache-Control: no-cache, no-store, must-revalidate');
}

// render page
render($pageFile, ['title' => $pageTitle, 'data' => $data, 'view' => $pageFile]);

$output = ob_get_clean();
$output = minifyHTML($output);

// performance stats
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

// save full page cache
if ($useCache) {
    $cache->set($output);
}

echo $output;

?>
