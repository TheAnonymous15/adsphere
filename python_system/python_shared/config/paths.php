<?php
/**
 * Path Configuration for Python System
 *
 * This file defines all base paths used throughout the python_system ecosystem.
 * All paths are relative to the python_system root directory.
 *
 * Date: December 24, 2025
 */

// Python System Root - the main python_system directory
define('PYTHON_SYSTEM_ROOT', dirname(dirname(dirname(__FILE__))));

// Base path - points to python_system root for backward compatibility
define('BASE_PATH', PYTHON_SYSTEM_ROOT);

// Shared resources path
define('SHARED_PATH', PYTHON_SYSTEM_ROOT . '/python_shared');

// Database path - within python_shared
define('DB_PATH', SHARED_PATH . '/database');

// Logs path - within python_shared
define('LOGS_PATH', SHARED_PATH . '/logs');

// Data path - within python_shared for company data
define('DATA_PATH', SHARED_PATH . '/data');

// Companies data path
define('COMPANIES_PATH', DATA_PATH . '/companies');

// Moderator services path
define('MODERATOR_SERVICES_PATH', PYTHON_SYSTEM_ROOT . '/moderator_services');

// Template paths
define('TEMPLATES_PATH', PYTHON_SYSTEM_ROOT . '/templates');

// Static assets path
define('STATIC_PATH', PYTHON_SYSTEM_ROOT . '/static');

// Public path for company portal
define('PUBLIC_COMPANY_PATH', PYTHON_SYSTEM_ROOT . '/python_company');

// Admin path
define('ADMIN_PATH', PYTHON_SYSTEM_ROOT . '/python_admin');

// Ensure required directories exist
$requiredDirs = [
    DB_PATH,
    LOGS_PATH,
    DATA_PATH,
    COMPANIES_PATH
];

foreach ($requiredDirs as $dir) {
    if (!is_dir($dir)) {
        mkdir($dir, 0755, true);
    }
}

