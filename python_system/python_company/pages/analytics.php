<?php
/**
 * COMPANY SERVICE - Analytics
 * Port 8003 - View company analytics
 */

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

// Load path configuration
require_once dirname(dirname(__DIR__)) . '/python_shared/config/paths.php';

if (!isset($_SESSION['company']) || !isset($_SESSION['company_logged_in'])) {
    header('Location: /login');
    exit();
}

$companySlug = $_SESSION['company'];
$companyName = $_SESSION['company_name'] ?? ucfirst($companySlug);

// Include the existing company_analytics.php
require __DIR__ . '/company_analytics.php';

