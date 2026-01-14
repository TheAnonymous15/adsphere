<?php
/**
 * ============================================================================
 * SHARED FUNCTIONS - Common utilities for all services
 * ============================================================================
 */

/**
 * Sanitize input
 */
function sanitize(string $input): string {
    return htmlspecialchars(trim($input), ENT_QUOTES, 'UTF-8');
}

/**
 * Generate CSRF token
 */
function generateCsrfToken(): string {
    if (!isset($_SESSION['csrf_token'])) {
        $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf_token'];
}

/**
 * Verify CSRF token
 */
function verifyCsrfToken(string $token): bool {
    return isset($_SESSION['csrf_token']) && hash_equals($_SESSION['csrf_token'], $token);
}

/**
 * Get current user type
 */
function getCurrentUserType(): ?string {
    if (isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in']) {
        return 'admin';
    }
    if (isset($_SESSION['company']) && $_SESSION['company']) {
        return 'company';
    }
    return null;
}

/**
 * Check if user is admin
 */
function isAdmin(): bool {
    return isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in'] === true;
}

/**
 * Check if user is company
 */
function isCompany(): bool {
    return isset($_SESSION['company']) && !empty($_SESSION['company']);
}

/**
 * Format date for display
 */
function formatDate(int $timestamp): string {
    return date('M j, Y g:i A', $timestamp);
}

/**
 * Format relative time
 */
function timeAgo(int $timestamp): string {
    $diff = time() - $timestamp;

    if ($diff < 60) return 'Just now';
    if ($diff < 3600) return floor($diff / 60) . 'm ago';
    if ($diff < 86400) return floor($diff / 3600) . 'h ago';
    if ($diff < 604800) return floor($diff / 86400) . 'd ago';
    if ($diff < 2592000) return floor($diff / 604800) . 'w ago';

    return date('M j, Y', $timestamp);
}

/**
 * Generate random ID
 */
function generateId(string $prefix = ''): string {
    return $prefix . date('Ym-His') . '.' . substr(uniqid(), -3) . '-' . substr(str_shuffle('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 0, 5);
}

/**
 * Redirect with flash message
 */
function redirect(string $url, ?string $message = null, string $type = 'info'): void {
    if ($message) {
        $_SESSION['flash'] = ['message' => $message, 'type' => $type];
    }
    header("Location: $url");
    exit();
}

/**
 * Get and clear flash message
 */
function getFlash(): ?array {
    if (isset($_SESSION['flash'])) {
        $flash = $_SESSION['flash'];
        unset($_SESSION['flash']);
        return $flash;
    }
    return null;
}

/**
 * Log activity
 */
function logActivity(string $action, array $details = []): void {
    $logFile = LOGS_PATH . '/activity_' . date('Y-m-d') . '.log';
    $logEntry = [
        'timestamp' => date('c'),
        'action' => $action,
        'user_type' => getCurrentUserType(),
        'user' => $_SESSION['admin_username'] ?? $_SESSION['company'] ?? 'anonymous',
        'ip' => $_SERVER['REMOTE_ADDR'] ?? 'unknown',
        'details' => $details
    ];

    @file_put_contents($logFile, json_encode($logEntry) . "\n", FILE_APPEND | LOCK_EX);
}

/**
 * Validate required fields
 */
function validateRequired(array $data, array $required): array {
    $errors = [];
    foreach ($required as $field) {
        if (!isset($data[$field]) || trim($data[$field]) === '') {
            $errors[$field] = ucfirst(str_replace('_', ' ', $field)) . ' is required';
        }
    }
    return $errors;
}

/**
 * Rate limiting
 */
function checkRateLimit(string $key, int $maxRequests = 60, int $windowSeconds = 60): bool {
    $cacheFile = sys_get_temp_dir() . '/rate_limit_' . md5($key) . '.json';

    $data = [];
    if (file_exists($cacheFile)) {
        $data = json_decode(file_get_contents($cacheFile), true) ?: [];
    }

    $now = time();
    $windowStart = $now - $windowSeconds;

    // Clean old entries
    $data = array_filter($data, fn($t) => $t > $windowStart);

    if (count($data) >= $maxRequests) {
        return false;
    }

    $data[] = $now;
    file_put_contents($cacheFile, json_encode($data));

    return true;
}

