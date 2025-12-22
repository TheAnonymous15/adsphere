<?php
/**
 * ============================================================================
 * SHARED BOOTSTRAP - Common utilities for all services
 * ============================================================================
 */

// Error reporting (adjust for production)
error_reporting(E_ALL);
ini_set('display_errors', 0);
ini_set('log_errors', 1);

// Timezone
date_default_timezone_set('Africa/Nairobi');

// Define paths if not already defined
if (!defined('BASE_PATH')) {
    define('BASE_PATH', dirname(dirname(__DIR__)));
}

// Autoload database class
require_once BASE_PATH . '/services/shared/database/Database.php';

// Common functions
require_once __DIR__ . '/functions.php';

// CORS headers for API
if (strpos($_SERVER['REQUEST_URI'] ?? '', '/api/') !== false) {
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With');

    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        http_response_code(200);
        exit();
    }
}

// Security headers
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: SAMEORIGIN');
header('X-XSS-Protection: 1; mode=block');

// Service discovery
function getServiceUrl(string $service): string {
    $services = [
        'public' => 'http://localhost:8001',
        'admin' => 'http://localhost:8002',
        'company' => 'http://localhost:8003',
        'moderation' => 'http://localhost:8004',
    ];

    return $services[$service] ?? '';
}

// JSON response helper
function jsonResponse(array $data, int $statusCode = 200): void {
    http_response_code($statusCode);
    header('Content-Type: application/json');
    echo json_encode($data);
    exit();
}

// Error response helper
function errorResponse(string $message, int $statusCode = 400): void {
    jsonResponse(['success' => false, 'error' => $message], $statusCode);
}

// Success response helper
function successResponse(array $data = [], string $message = 'Success'): void {
    jsonResponse(['success' => true, 'message' => $message, 'data' => $data]);
}

