<?php
/********************************************
 * Admin Logout - AdSphere
 * Secure logout with session destruction
 ********************************************/
session_start();

// Log logout event
if (isset($_SESSION['admin_username'])) {
    $logDir = __DIR__ . "/../companies/logs/";
    if (!is_dir($logDir)) mkdir($logDir, 0755, true);

    $logFile = $logDir . "security_" . date('Y-m-d') . ".log";
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'Unknown';
    $timestamp = date('Y-m-d H:i:s');
    $username = $_SESSION['admin_username'];

    $logEntry = "[{$timestamp}] LOGOUT | User: {$username} | IP: {$ip} | Status: SUCCESS\n";
    file_put_contents($logFile, $logEntry, FILE_APPEND);
}

// Destroy all session data
$_SESSION = array();

// Delete session cookie
if (isset($_COOKIE[session_name()])) {
    setcookie(session_name(), '', time() - 3600, '/');
}

// Destroy the session
session_destroy();

// Redirect to login page with logout message
header("Location: login.php?logout=1");
exit();
?>

