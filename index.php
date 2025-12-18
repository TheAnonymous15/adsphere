<?php
declare(strict_types=1);

// ------------------------------
// Headers & error reporting
// ------------------------------
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('Pragma: no-cache');
header('Expires: 0');
error_reporting(E_ALL);
ini_set('display_errors', '1');

// ------------------------------
// Paths
// ------------------------------
define('APP_PATH', __DIR__ . '/app/');
define('LAYOUT_PATH', APP_PATH . 'layouts/');
define('INCLUDE_PATH', APP_PATH . 'includes/');
define('CONTROLLER_PATH', APP_PATH . 'controllers/');
define('VIEW_PATH', APP_PATH . 'views/');

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
$slug = $uri === '' ? 'home' : strtolower(preg_replace('/[^a-z0-9_-]/i', '', $uri));

// ------------------------------
// Auto-scan views for routes
// ------------------------------
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
// Auto-include WhatsApp component
// ------------------------------
$whatsappFile = INCLUDE_PATH . 'whatsapp.php';
if (file_exists($whatsappFile)) require_once $whatsappFile;


// ------------------------------
// Render page
// ------------------------------
render($pageFile, ['title' => $pageTitle, 'data' => $data, 'view' => $pageFile]);
