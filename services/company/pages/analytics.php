<?php
/**
 * COMPANY SERVICE - Analytics
 * Port 8003 - View company analytics
 */

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

if (!defined('BASE_PATH')) {
    define('BASE_PATH', dirname(dirname(dirname(__DIR__))));
}

if (!isset($_SESSION['company']) || !isset($_SESSION['company_logged_in'])) {
    header('Location: /login');
    exit();
}

$companySlug = $_SESSION['company'];
$companyName = $_SESSION['company_name'] ?? ucfirst($companySlug);

// Include the existing company_analytics.php from app/companies
require BASE_PATH . 'BASE_PATH . '/services/company/home/company_analytics.php'';

