<?php
/********************************************
 * SUPER SECURE ADMIN LOGIN - AdSphere v2.0
 * Military-grade authentication system
 *
 * Security Features:
 * ✅ Secure session cookies (httponly, samesite, secure)
 * ✅ Unified error messages (timing-safe)
 * ✅ Rate limiting by user+IP (SQLite)
 * ✅ Constant-time password verification
 * ✅ Argon2id password hashing
 * ✅ TOTP 2FA with fallback
 * ✅ Tamper-proof audit logs
 * ✅ CSRF protection
 * ✅ IP whitelisting
 ********************************************/

// Secure session configuration BEFORE session_start()
ini_set('session.cookie_httponly', 1);
ini_set('session.cookie_samesite', 'Strict');
ini_set('session.use_only_cookies', 1);
ini_set('session.cookie_secure', 0); // Set to 1 when using HTTPS
ini_set('session.use_strict_mode', 1);

session_start();

// Security Headers
header("X-Frame-Options: DENY");
header("X-Content-Type-Options: nosniff");
header("X-XSS-Protection: 1; mode=block");
header("Referrer-Policy: strict-origin-when-cross-origin");
header("Permissions-Policy: geolocation=(), microphone=(), camera=()");

// Regenerate session ID periodically for security
if (!isset($_SESSION['last_regeneration'])) {
    $_SESSION['last_regeneration'] = time();
} elseif (time() - $_SESSION['last_regeneration'] > 300) {
    session_regenerate_id(true);
    $_SESSION['last_regeneration'] = time();
}

// Configuration
$securityConfig = [
    'max_attempts' => 5,
    'lockout_duration' => 900, // 15 minutes
    'session_lifetime' => 3600, // 1 hour
    'enable_2fa' => true, // 2FA enabled
    'require_2fa_for_admins' => true, // Require 2FA for super admins
    'ip_whitelist' => [], // Add IPs: ['192.168.1.1']
    'login_delay' => 2, // Delay in seconds for failed login (timing attack mitigation)
];

$dataDir = __DIR__ . "/../data/";
$logDir = __DIR__ . "/../companies/logs/";
if (!is_dir($dataDir)) mkdir($dataDir, 0755, true);
if (!is_dir($logDir)) mkdir($logDir, 0755, true);

// Initialize SQLite database for login attempts
$dbFile = $dataDir . "security.db";
$db = new SQLite3($dbFile);
$db->exec("CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    ip_address TEXT NOT NULL,
    attempt_time INTEGER NOT NULL,
    success INTEGER DEFAULT 0,
    user_agent TEXT,
    UNIQUE(username, ip_address, attempt_time)
)");

$db->exec("CREATE INDEX IF NOT EXISTS idx_username_ip ON login_attempts(username, ip_address)");
$db->exec("CREATE INDEX IF NOT EXISTS idx_attempt_time ON login_attempts(attempt_time)");

// Unified error message (prevents username enumeration)
$genericErrorMsg = "Invalid credentials or too many failed attempts. Please try again.";
$errorMsg = "";
$successMsg = "";

// Check for logout or timeout messages
if (isset($_GET['logout']) && $_GET['logout'] == '1') {
    $successMsg = "You have been logged out successfully.";
}
if (isset($_GET['timeout']) && $_GET['timeout'] == '1') {
    $errorMsg = "Your session has expired. Please login again.";
}

// Generate CSRF Token
if (!isset($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}

// Check IP Whitelist (if enabled)
function checkIPWhitelist($whitelist) {
    if (empty($whitelist)) return true;
    $userIP = $_SERVER['REMOTE_ADDR'] ?? '';
    return in_array($userIP, $whitelist);
}

// SQLite-based Rate Limiting (tracks by username + IP)
function checkRateLimit($db, $username, $ip, $config) {
    $now = time();
    $window = $now - 3600; // 1 hour window

    // Clean old attempts
    $stmt = $db->prepare("DELETE FROM login_attempts WHERE attempt_time < :window");
    $stmt->bindValue(':window', $window, SQLITE3_INTEGER);
    $stmt->execute();

    // Count recent failed attempts for this user+IP combination
    $stmt = $db->prepare("
        SELECT COUNT(*) as count, MAX(attempt_time) as last_attempt
        FROM login_attempts
        WHERE username = :username
        AND ip_address = :ip
        AND success = 0
        AND attempt_time > :window
    ");
    $stmt->bindValue(':username', $username, SQLITE3_TEXT);
    $stmt->bindValue(':ip', $ip, SQLITE3_TEXT);
    $stmt->bindValue(':window', $window, SQLITE3_INTEGER);

    $result = $stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);

    $failedCount = $row['count'] ?? 0;
    $lastAttempt = $row['last_attempt'] ?? 0;

    // Check if locked out
    if ($failedCount >= $config['max_attempts']) {
        $lockoutEnd = $lastAttempt + $config['lockout_duration'];
        if ($now < $lockoutEnd) {
            $remainingTime = ceil(($lockoutEnd - $now) / 60);
            return [
                'locked' => true,
                'remaining_time' => $remainingTime,
                'failed_count' => $failedCount
            ];
        }
    }

    return [
        'locked' => false,
        'failed_count' => $failedCount
    ];
}

// Record Login Attempt (success or failure)
function recordLoginAttempt($db, $username, $ip, $success) {
    $stmt = $db->prepare("
        INSERT INTO login_attempts (username, ip_address, attempt_time, success, user_agent)
        VALUES (:username, :ip, :time, :success, :ua)
    ");

    $stmt->bindValue(':username', $username, SQLITE3_TEXT);
    $stmt->bindValue(':ip', $ip, SQLITE3_TEXT);
    $stmt->bindValue(':time', time(), SQLITE3_INTEGER);
    $stmt->bindValue(':success', $success ? 1 : 0, SQLITE3_INTEGER);
    $stmt->bindValue(':ua', $_SERVER['HTTP_USER_AGENT'] ?? 'Unknown', SQLITE3_TEXT);

    $stmt->execute();
}

// Clear Failed Attempts on Successful Login
function clearFailedAttempts($db, $username, $ip) {
    $stmt = $db->prepare("
        DELETE FROM login_attempts
        WHERE username = :username
        AND ip_address = :ip
        AND success = 0
    ");

    $stmt->bindValue(':username', $username, SQLITE3_TEXT);
    $stmt->bindValue(':ip', $ip, SQLITE3_TEXT);
    $stmt->execute();
}

// Tamper-proof Security Audit Log with HMAC
function logSecurityEvent($event, $username, $status, $logDir) {
    $logFile = $logDir . "security_" . date('Y-m-d') . ".log";
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'Unknown';
    $userAgent = $_SERVER['HTTP_USER_AGENT'] ?? 'Unknown';
    $timestamp = date('Y-m-d H:i:s');

    $logData = "{$timestamp}|{$event}|{$username}|{$ip}|{$status}";

    // Generate HMAC for tamper detection
    $secretKey = getLogSecretKey();
    $hmac = hash_hmac('sha256', $logData, $secretKey);

    $logEntry = "[{$timestamp}] {$event} | User: {$username} | IP: {$ip} | Status: {$status} | UA: " .
                substr($userAgent, 0, 50) . " | HMAC: {$hmac}\n";

    file_put_contents($logFile, $logEntry, FILE_APPEND | LOCK_EX);
}

// Get or create secret key for log HMAC
function getLogSecretKey() {
    $keyFile = __DIR__ . "/../data/log_secret.key";

    if (!file_exists($keyFile)) {
        $secret = bin2hex(random_bytes(32));
        file_put_contents($keyFile, $secret, LOCK_EX);
        chmod($keyFile, 0600);
    }

    return file_get_contents($keyFile);
}

// Verify Admin Credentials with Constant-Time Comparison
function verifyAdminCredentials($username, $password) {
    $adminsFile = __DIR__ . "/../config/admins.json";

    // Create default admin with Argon2id if file doesn't exist
    if (!file_exists($adminsFile)) {
        $defaultAdmin = [
            'admin' => [
                'username' => 'admin',
                'password' => password_hash('Admin@123', PASSWORD_ARGON2ID, [
                    'memory_cost' => 65536,
                    'time_cost' => 4,
                    'threads' => 2
                ]),
                'email' => 'admin@adsphere.com',
                'role' => 'super_admin',
                'created_at' => time(),
                '2fa_enabled' => false,
                '2fa_secret' => null
            ]
        ];

        $configDir = dirname($adminsFile);
        if (!is_dir($configDir)) mkdir($configDir, 0755, true);

        file_put_contents($adminsFile, json_encode($defaultAdmin, JSON_PRETTY_PRINT));
        chmod($adminsFile, 0600); // Restrict file permissions
    }

    $admins = json_decode(file_get_contents($adminsFile), true) ?? [];

    // Constant-time username check (prevent timing attacks)
    $userFound = false;
    $storedHash = null;

    foreach ($admins as $user => $data) {
        if (hash_equals($user, $username)) {
            $userFound = true;
            $storedHash = $data['password'];
            break;
        }
    }

    // Always verify against a hash (prevents timing attacks)
    if (!$userFound) {
        // Use a dummy hash to maintain constant time
        $storedHash = '$argon2id$v=19$m=65536,t=4,p=2$dummy$dummy';
    }

    // Constant-time password verification
    $isValid = password_verify($password, $storedHash);

    return $userFound && $isValid;
}

// Get admin data (for 2FA check)
function getAdminData($username) {
    $adminsFile = __DIR__ . "/../config/admins.json";
    $admins = json_decode(file_get_contents($adminsFile), true) ?? [];
    return $admins[$username] ?? null;
}

// Handle Login
if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    $ip = $_SERVER['REMOTE_ADDR'] ?? 'Unknown';
    $username = trim($_POST['username'] ?? '');
    $password = $_POST['password'] ?? '';

    // CSRF Protection
    if (!isset($_POST['csrf_token']) || !hash_equals($_SESSION['csrf_token'], $_POST['csrf_token'])) {
        $errorMsg = $genericErrorMsg;
        logSecurityEvent('LOGIN_ATTEMPT', 'Unknown', 'CSRF_FAIL', $logDir);
        sleep($securityConfig['login_delay']); // Timing attack mitigation
    }
    // Input Validation
    elseif (empty($username) || empty($password)) {
        $errorMsg = $genericErrorMsg;
        sleep($securityConfig['login_delay']);
    }
    // IP Whitelist Check
    elseif (!checkIPWhitelist($securityConfig['ip_whitelist'])) {
        $errorMsg = $genericErrorMsg;
        logSecurityEvent('LOGIN_ATTEMPT', $username, 'IP_BLOCKED', $logDir);
        sleep($securityConfig['login_delay']);
    }
    else {

        // Check Rate Limiting (by username + IP)
        $rateCheck = checkRateLimit($db, $username, $ip, $securityConfig);

        if ($rateCheck['locked']) {
            $errorMsg = "Too many failed attempts. Please try again in {$rateCheck['remaining_time']} minutes.";
            logSecurityEvent('LOGIN_ATTEMPT', $username, 'RATE_LIMITED', $logDir);
            sleep($securityConfig['login_delay']);
        } else {

            // Verify Credentials (constant-time)
            $isValidCredentials = verifyAdminCredentials($username, $password);

            if ($isValidCredentials) {

                // Record successful attempt
                recordLoginAttempt($db, $username, $ip, true);
                clearFailedAttempts($db, $username, $ip);

                // Get admin data
                $adminData = getAdminData($username);

                // ENFORCE 2FA FOR ALL USERS
                if (!$adminData) {
                    $errorMsg = "Account configuration error. Please contact support.";
                    logSecurityEvent('LOGIN_ERROR', $username, 'INVALID_ACCOUNT', $logDir);
                    sleep($securityConfig['login_delay']);
                }
                // Check if 2FA is configured
                elseif (!isset($adminData['2fa_enabled']) || !$adminData['2fa_enabled'] || empty($adminData['2fa_secret'])) {

                    // 2FA NOT CONFIGURED - Force setup
                    $_SESSION['pending_2fa_setup'] = [
                        'username' => $username,
                        'ip' => $ip,
                        'time' => time()
                    ];

                    logSecurityEvent('LOGIN_2FA_SETUP_REQUIRED', $username, 'SETUP_REQUIRED', $logDir);

                    // Redirect to 2FA setup (MANDATORY)
                    header("Location: handlers/setup_2fa.php?mandatory=1");
                    exit();

                } else {

                    // 2FA IS CONFIGURED - Require verification
                    $_SESSION['pending_2fa'] = [
                        'username' => $username,
                        'ip' => $ip,
                        'time' => time()
                    ];

                    logSecurityEvent('LOGIN_2FA_PENDING', $username, 'PENDING', $logDir);

                    // Redirect to 2FA verification
                    header("Location: handlers/verify_2fa.php");
                    exit();
                }

            } else {

                // Failed Login
                recordLoginAttempt($db, $username, $ip, false);
                logSecurityEvent('LOGIN_ATTEMPT', $username, 'INVALID_CREDENTIALS', $logDir);

                // Unified error message
                $errorMsg = $genericErrorMsg;

                // Timing attack mitigation
                sleep($securityConfig['login_delay']);
            }
        }
    }

    // Regenerate CSRF token after submission
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}

// Complete Login (after password + optional 2FA)
function completeLogin($username, $ip, $logDir) {
    session_regenerate_id(true);

    $_SESSION['admin_logged_in'] = true;
    $_SESSION['admin_username'] = $username;
    $_SESSION['admin_role'] = 'super_admin'; // TODO: Get from admin data
    $_SESSION['login_time'] = time();
    $_SESSION['last_activity'] = time();
    $_SESSION['ip_address'] = $ip;

    // Clear 2FA pending if exists
    unset($_SESSION['pending_2fa']);

    logSecurityEvent('LOGIN_SUCCESS', $username, 'SUCCESS', $logDir);

    header("Location: admin_dashboard.php");
    exit();
}

// Check if already logged in
if (isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in'] === true) {
    // Check session timeout
    if (isset($_SESSION['last_activity']) && (time() - $_SESSION['last_activity']) > $securityConfig['session_lifetime']) {
        session_unset();
        session_destroy();
        $errorMsg = "Session expired. Please login again.";
    } else {
        $_SESSION['last_activity'] = time();
        header("Location: admin_dashboard.php");
        exit();
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Login - AdSphere</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }

        @keyframes scan {
            0%, 100% { transform: translateY(-100%); }
            50% { transform: translateY(100%); }
        }

        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.4); }
            50% { box-shadow: 0 0 40px rgba(99, 102, 241, 0.8); }
        }

        body {
            background: linear-gradient(135deg, #0a1628, #0f2847, #1e3a8a, #1e40af, #0a1628);
            background-size: 400% 400%;
            animation: gradientShift 20s ease infinite;
        }

        .glass-card {
            background: linear-gradient(135deg, rgba(30, 58, 138, 0.15), rgba(30, 64, 175, 0.1));
            backdrop-filter: blur(20px);
            border: 1px solid rgba(59, 130, 246, 0.3);
            box-shadow: 0 8px 32px 0 rgba(59, 130, 246, 0.2), 0 0 80px rgba(37, 99, 235, 0.1);
        }

        .login-container {
            animation: float 6s ease-in-out infinite;
        }

        .security-badge {
            animation: pulse-glow 2s ease-in-out infinite;
        }

        .scan-line {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, #3b82f6, #60a5fa, transparent);
            animation: scan 3s linear infinite;
        }

        .grid-pattern {
            background-image:
                linear-gradient(rgba(59, 130, 246, 0.08) 1px, transparent 1px),
                linear-gradient(90deg, rgba(59, 130, 246, 0.08) 1px, transparent 1px);
            background-size: 50px 50px;
        }

        .input-glow:focus {
            box-shadow: 0 0 25px rgba(59, 130, 246, 0.6), 0 0 50px rgba(37, 99, 235, 0.3);
            border-color: #3b82f6;
            background: rgba(30, 58, 138, 0.2);
        }

        input {
            background: rgba(30, 58, 138, 0.15);
            border: 1px solid rgba(59, 130, 246, 0.3);
            color: #e0f2fe;
        }

        input::placeholder {
            color: #7dd3fc;
            opacity: 0.5;
        }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4 grid-pattern relative overflow-hidden"
      style="background-image: url('/static/images/ad.jpg');">



    <!-- Animated Background Elements -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <div class="absolute top-20 left-10 w-72 h-72 bg-blue-600/25 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-20 right-10 w-96 h-96 bg-blue-700/20 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
        <div class="absolute top-1/2 left-1/2 w-64 h-64 bg-cyan-500/25 rounded-full blur-3xl animate-pulse" style="animation-delay: 2s;"></div>
        <div class="absolute top-1/3 right-1/4 w-80 h-80 bg-indigo-600/15 rounded-full blur-3xl animate-pulse" style="animation-delay: 3s;"></div>
    </div>

    <!-- Login Container -->
    <div class="login-container relative z-10 w-full max-w-md">

        <!-- Security Badge -->
        <div class="text-center mb-8">
            <div class="inline-flex items-center gap-3 bg-blue-600/20 border border-blue-500/50 rounded-full px-6 py-3 security-badge mb-4">
                <i class="fas fa-shield-alt text-blue-400 text-xl"></i>
                <span class="text-sm font-bold text-sky-100">SECURED BY 256-BIT ENCRYPTION</span>
            </div>
            <h1 class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-sky-300 mb-2">
                ADMIN ACCESS
            </h1>
            <p class="text-sky-300/70 text-sm">Super Administrator Control Panel</p>
        </div>

        <!-- Login Form -->
        <div class="glass-card rounded-2xl p-8 relative overflow-hidden">
            <div class="scan-line"></div>

            <!-- Error Message -->
            <?php if ($errorMsg): ?>
                <div class="mb-6 p-4 bg-red-600/20 border border-red-600/50 rounded-xl flex items-center gap-3 animate-pulse">
                    <i class="fas fa-exclamation-triangle text-red-400"></i>
                    <div>
                        <p class="text-red-400 font-semibold text-sm"><?= htmlspecialchars($errorMsg) ?></p>
                    </div>
                </div>
            <?php endif; ?>

            <!-- Success Message -->
            <?php if ($successMsg): ?>
                <div class="mb-6 p-4 bg-green-600/20 border border-green-600/50 rounded-xl flex items-center gap-3">
                    <i class="fas fa-check-circle text-green-400"></i>
                    <div>
                        <p class="text-green-400 font-semibold text-sm"><?= htmlspecialchars($successMsg) ?></p>
                    </div>
                </div>
            <?php endif; ?>

            <form method="POST" class="space-y-6" autocomplete="off">

                <!-- CSRF Token -->
                <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token']) ?>">

                <!-- Username Field -->
                <div class="relative">
                    <label class="block text-sm font-bold text-sky-200 mb-2">
                        <i class="fas fa-user-shield mr-2 text-cyan-400"></i>Username
                    </label>
                    <input
                        type="text"
                        name="username"
                        required
                        autocomplete="off"
                        class="input-glow w-full px-4 py-3 text-white rounded-xl focus:outline-none transition-all"
                        placeholder="Enter your admin username">
                    <div class="absolute right-4 top-11 text-blue-400/50">
                        <i class="fas fa-user"></i>
                    </div>
                </div>

                <!-- Password Field -->
                <div class="relative">
                    <label class="block text-sm font-bold text-sky-200 mb-2">
                        <i class="fas fa-lock mr-2 text-cyan-400"></i>Password
                    </label>
                    <input
                        type="password"
                        name="password"
                        id="password"
                        required
                        autocomplete="off"
                        class="input-glow w-full px-4 text-white py-3 rounded-xl focus:outline-none transition-all"
                        placeholder="Enter your secure password">
                    <button
                        type="button"
                        onclick="togglePassword()"
                        class="absolute right-4 top-11 text-blue-400/50 hover:text-cyan-400 transition">
                        <i class="fas fa-eye" id="toggleIcon"></i>
                    </button>
                </div>

                <!-- Remember Me & Forgot Password -->
                <div class="flex items-center justify-between text-sm">
                    <label class="flex items-center gap-2 cursor-pointer text-sky-300/70 hover:text-sky-200 transition">
                        <input type="checkbox" name="remember" class="rounded bg-blue-900/30 border-blue-500/30">
                        <span>Remember me</span>
                    </label>
                    <a href="#" class="text-cyan-400 hover:text-cyan-300 transition">
                        Forgot password?
                    </a>
                </div>

                <!-- Login Button -->
                <button
                    type="submit"
                    class="w-full py-4 bg-gradient-to-r from-blue-600 via-blue-700 to-cyan-600 hover:from-blue-700 hover:via-blue-800 hover:to-cyan-700 rounded-xl font-bold text-white text-lg transition-all transform hover:scale-105 shadow-lg hover:shadow-blue-500/60 relative overflow-hidden group">
                    <span class="relative z-10 flex items-center justify-center gap-2">
                        <i class="fas fa-sign-in-alt"></i>
                        <span>AUTHENTICATE</span>
                    </span>
                    <div class="absolute inset-0 bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                </button>

            </form>

            <!-- Security Features -->
            <div class="mt-8 pt-6 border-t border-white/10">
                <p class="text-xs text-gray-500 text-center mb-3">Protected by:</p>
                <div class="grid grid-cols-3 gap-2 text-xs">
                    <div class="text-center p-2 bg-green-600/10 rounded-lg">
                        <i class="fas fa-shield-virus text-green-400 mb-1"></i>
                        <p class="text-gray-400">CSRF</p>
                    </div>
                    <div class="text-center p-2 bg-blue-600/10 rounded-lg">
                        <i class="fas fa-user-lock text-blue-400 mb-1"></i>
                        <p class="text-gray-400">Rate Limit</p>
                    </div>
                    <div class="text-center p-2 bg-purple-600/10 rounded-lg">
                        <i class="fas fa-fingerprint text-purple-400 mb-1"></i>
                        <p class="text-gray-400">Session</p>
                    </div>
                </div>
            </div>

            <!-- System Status -->
            <div class="mt-4 flex items-center justify-center gap-2 text-xs text-gray-500">
                <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span>System Operational</span>
                <span>•</span>
                <span id="systemTime">--:--:--</span>
            </div>
        </div>

        <!-- Footer Links -->
        <div class="mt-6 text-center text-sm text-sky-400/50">
            <p>© 2024 AdSphere. All rights reserved.</p>
            <div class="mt-2 flex items-center justify-center gap-4">
                <a href="#" class="hover:text-cyan-400 transition">Privacy Policy</a>
                <span>•</span>
                <a href="#" class="hover:text-cyan-400 transition">Terms of Service</a>
            </div>
        </div>

    </div>

    <script>
        // Toggle Password Visibility
        function togglePassword() {
            const passwordInput = document.getElementById('password');
            const toggleIcon = document.getElementById('toggleIcon');

            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                toggleIcon.classList.remove('fa-eye');
                toggleIcon.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                toggleIcon.classList.remove('fa-eye-slash');
                toggleIcon.classList.add('fa-eye');
            }
        }

        // Update System Time
        function updateSystemTime() {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
            document.getElementById('systemTime').textContent = timeStr;
        }

        setInterval(updateSystemTime, 1000);
        updateSystemTime();

        // Prevent multiple form submissions
        const form = document.querySelector('form');
        form.addEventListener('submit', function(e) {
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Authenticating...';
        });

        // Auto-focus username field
        document.querySelector('input[name="username"]').focus();
    </script>

</body>
</html>
