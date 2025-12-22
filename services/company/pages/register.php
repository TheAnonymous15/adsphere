<?php
/**
 * COMPANY SERVICE - Register New Company
 * Port 8003
 */

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

if (!defined('BASE_PATH')) {
    define('BASE_PATH', dirname(dirname(dirname(__DIR__))));
}

// If already logged in, redirect to dashboard
if (isset($_SESSION['company_logged_in']) && $_SESSION['company_logged_in'] === true) {
    header('Location: /dashboard');
    exit();
}

// Include admin's company registration (which handles the registration)
require BASE_PATH . 'BASE_PATH . '/services/admin/company_register.php'';

