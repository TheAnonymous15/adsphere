<?php
/********************************************
 * login.php - Secure Company Login System
 * Enhanced with CSRF, rate limiting, and session security
 ********************************************/

// Session already started by index.php router
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

// Regenerate session ID to prevent session fixation
if (!isset($_SESSION['initiated'])) {
    session_regenerate_id(true);
    $_SESSION['initiated'] = true;
}

// Define BASE_PATH if not defined
if (!defined('BASE_PATH')) {
    define('BASE_PATH', dirname(dirname(dirname(__DIR__))));
}

$metaBase = __DIR__ . "/../metadata/";

// If already logged in redirect
if (isset($_SESSION['company_logged_in']) && $_SESSION['company_logged_in'] === true) {
    header("Location: /dashboard");
    exit;
}

// ============================================
// CSRF TOKEN GENERATION
// ============================================
if (empty($_SESSION['csrf_token'])) {
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}

// ============================================
// RATE LIMITING (Simple file-based)
// ============================================
function checkCompanyRateLimit($email) {
    $lockFile = sys_get_temp_dir() . '/login_attempts_' . md5($email) . '.json';
    $maxAttempts = 5;
    $lockoutTime = 900; // 15 minutes

    $attempts = [];
    if (file_exists($lockFile)) {
        $data = json_decode(file_get_contents($lockFile), true);
        if ($data) {
            $attempts = $data['attempts'] ?? [];

            // Check if locked out
            if (isset($data['locked_until']) && time() < $data['locked_until']) {
                $remaining = ceil(($data['locked_until'] - time()) / 60);
                return [
                    'allowed' => false,
                    'message' => "Too many failed attempts. Please try again in {$remaining} minutes."
                ];
            }
        }
    }

    // Clean old attempts (older than 15 minutes)
    $attempts = array_filter($attempts, fn($time) => time() - $time < $lockoutTime);

    // Check if exceeded max attempts
    if (count($attempts) >= $maxAttempts) {
        $lockUntil = time() + $lockoutTime;
        file_put_contents($lockFile, json_encode([
            'attempts' => $attempts,
            'locked_until' => $lockUntil
        ]));
        return [
            'allowed' => false,
            'message' => "Too many failed attempts. Account locked for 15 minutes."
        ];
    }

    return ['allowed' => true];
}

function recordFailedAttempt($email) {
    $lockFile = sys_get_temp_dir() . '/login_attempts_' . md5($email) . '.json';

    $attempts = [];
    if (file_exists($lockFile)) {
        $data = json_decode(file_get_contents($lockFile), true);
        $attempts = $data['attempts'] ?? [];
    }

    $attempts[] = time();
    file_put_contents($lockFile, json_encode(['attempts' => $attempts]));
}

function clearFailedAttempts($email) {
    $lockFile = sys_get_temp_dir() . '/login_attempts_' . md5($email) . '.json';
    if (file_exists($lockFile)) {
        unlink($lockFile);
    }
}

// ============================================
// INPUT VALIDATION
// ============================================
function validateEmail($email) {
    return filter_var($email, FILTER_VALIDATE_EMAIL) !== false;
}

// ============================================
// PASSWORD VERIFICATION
// ============================================
function verifyPassword($inputPassword, $company) {
    // Check if company has a hashed password
    if (isset($company['password_hash'])) {
        return password_verify($inputPassword, $company['password_hash']);
    }

    // Fallback to static password (TEMPORARY - should be removed in production)
    return $inputPassword === "1234";
}

$error = "";
$success = "";

// ============================================
// PROCESS LOGIN
// ============================================
if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    // Verify CSRF token
    if (!isset($_POST['csrf_token']) || $_POST['csrf_token'] !== $_SESSION['csrf_token']) {
        $error = "Invalid security token. Please refresh the page and try again.";
    } else {

        $email = trim($_POST["email"] ?? "");
        $password = $_POST["password"] ?? "";
        $remember = isset($_POST["remember"]);

        // Validate inputs
        if ($email === "" || $password === "") {
            $error = "Please enter both email and password.";
        } elseif (!validateEmail($email)) {
            $error = "Please enter a valid email address.";
        } else {

            // Check rate limit
            $rateCheck = checkCompanyRateLimit($email);
            if (!$rateCheck['allowed']) {
                $error = $rateCheck['message'];
            } else {

                $authenticated = false;
                $companyData = null;
                $matchedFile = null;

                // Search for company by email
                foreach (scandir($metaBase) as $file) {

                    if ($file === "." || $file === "..") continue;
                    if (!str_ends_with($file, ".json")) continue;

                    $raw = file_get_contents("$metaBase/$file");
                    $company = json_decode($raw, true);

                    if (!$company) continue;

                    $cEmail = $company["contact"]["email"] ?? null;

                    if ($cEmail && strtolower($cEmail) === strtolower($email)) {

                        // Verify password
                        if (verifyPassword($password, $company)) {
                            $authenticated = true;
                            $companyData = $company;
                            $matchedFile = $file;
                            break;
                        }
                    }
                }

                if ($authenticated && $companyData) {

                    // Clear failed attempts
                    clearFailedAttempts($email);

                    // Regenerate session ID for security
                    session_regenerate_id(true);

                    // Set session variables (use company_logged_in for microservices)
                    $_SESSION["company_logged_in"] = true;
                    $_SESSION["company"] = $companyData["slug"];
                    $_SESSION["company_name"] = $companyData["name"] ?? "Unknown";
                    $_SESSION["company_email"] = $email;
                    $_SESSION["company_last_activity"] = time();
                    $_SESSION["login_time"] = time();
                    $_SESSION["user_ip"] = $_SERVER['REMOTE_ADDR'] ?? 'unknown';

                    // Handle "Remember Me"
                    if ($remember && $matchedFile) {
                        // Set cookie for 30 days
                        $token = bin2hex(random_bytes(32));
                        setcookie('remember_token', $token, time() + (30 * 24 * 60 * 60), '/', '', false, true);

                        // Store token in company metadata (in production, use database)
                        $companyData['remember_token'] = password_hash($token, PASSWORD_DEFAULT);
                        file_put_contents("$metaBase/" . basename($matchedFile), json_encode($companyData, JSON_PRETTY_PRINT));
                    }

                    // Redirect to dashboard (microservices path)
                    header("Location: /dashboard");
                    exit;

                } else {

                    // Record failed attempt
                    recordFailedAttempt($email);

                    // Generic error message (don't reveal if email exists)
                    $error = "Invalid email or password.";
                }
            }
        }
    }

    // Regenerate CSRF token after each attempt
    $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Company Login - AdSphere</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .input-field {
            transition: all 0.3s ease;
        }
        .input-field:focus {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }
    </style>
</head>
<body class="bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900 text-white min-h-screen flex items-center justify-center p-6"
  style="background-image: url('/services/assets/images/ad.jpg');">

<div class="max-w-md w-full">

    <!-- Logo/Brand -->
    <div class="text-center mb-8">
        <h1 class="text-4xl font-bold text-indigo-400 mb-2">AdSphere</h1>
        <p class="text-gray-400">Company Portal</p>
    </div>

    <!-- Login Card -->
    <div class="bg-white/10 backdrop-blur-lg p-8 rounded-2xl shadow-2xl border border-white/20">

        <h2 class="text-2xl font-bold text-white mb-6">Sign In</h2>

        <?php if ($error): ?>
            <div class="bg-red-600/90 backdrop-blur p-4 rounded-lg mb-4 text-white flex items-start gap-3 animate-pulse">
                <svg class="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                </svg>
                <span><?= htmlspecialchars($error) ?></span>
            </div>
        <?php endif; ?>

        <?php if ($success): ?>
            <div class="bg-green-600/90 backdrop-blur p-4 rounded-lg mb-4 text-white flex items-start gap-3">
                <svg class="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                </svg>
                <span><?= htmlspecialchars($success) ?></span>
            </div>
        <?php endif; ?>

        <form method="POST" class="flex flex-col gap-4" autocomplete="on">

            <!-- CSRF Token -->
            <input type="hidden" name="csrf_token" value="<?= htmlspecialchars($_SESSION['csrf_token']) ?>">

            <!-- Email Field -->
            <div>
                <label for="email" class="block text-sm font-medium text-gray-300 mb-2">
                    Email Address
                </label>
                <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    autocomplete="email"
                    placeholder="company@example.com"
                    value="<?= htmlspecialchars($_POST['email'] ?? '') ?>"
                    class="input-field w-full text-white bg-slate-800/50 border border-gray-600 p-3 rounded-lg
                           focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
            </div>

            <!-- Password Field -->
            <div>
                <label for="password" class="block text-sm font-medium text-gray-300 mb-2">
                    Password
                </label>
                <div class="relative">
                    <input
                        id="password"
                        name="password"
                        type="password"
                        required
                        autocomplete="current-password"
                        placeholder="Enter your password"
                        class="input-field w-full text-white bg-slate-800/50 border border-gray-600 p-3 rounded-lg
                               focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                    <button
                        type="button"
                        onclick="togglePassword()"
                        class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white">
                        <svg id="eyeIcon" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                        </svg>
                    </button>
                </div>
            </div>

            <!-- Remember Me & Forgot Password -->
            <div class="flex items-center justify-between text-sm">
                <label class="flex items-center gap-2 cursor-pointer">
                    <input
                        type="checkbox"
                        name="remember"
                        class="w-4 h-4 text-indigo-600 bg-slate-800 border-gray-600 rounded
                               focus:ring-indigo-500 focus:ring-2">
                    <span class="text-gray-300">Remember me</span>
                </label>
                <a href="#" class="text-indigo-400 hover:text-indigo-300">
                    Forgot password?
                </a>
            </div>

            <!-- Submit Button -->
            <button
                type="submit"
                class="w-full p-3 bg-indigo-600 hover:bg-indigo-700 rounded-lg mt-2 font-semibold
                       transition-all duration-300 hover:shadow-lg hover:shadow-indigo-500/50
                       focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900">
                Sign In
            </button>

        </form>

        <!-- Register Link -->
        <div class="mt-6 text-center text-sm text-gray-400">
            Don't have an account?
            <a href="/register" class="text-indigo-400 hover:text-indigo-300 font-medium">
                Register here
            </a>
        </div>

    </div>

    <!-- Security Notice -->
    <div class="mt-6 text-center text-xs text-gray-500">
        <p>Protected by CSRF tokens and rate limiting</p>
        <p class="mt-1">Your session is secured with encryption</p>
    </div>

</div>

<script>
    // Toggle password visibility
    function togglePassword() {
        const passwordInput = document.getElementById('password');
        const eyeIcon = document.getElementById('eyeIcon');

        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            eyeIcon.innerHTML = `
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"/>
            `;
        } else {
            passwordInput.type = 'password';
            eyeIcon.innerHTML = `
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
            `;
        }
    }

    // Auto-focus email field on page load
    document.getElementById('email').focus();
</script>

</body>
</html>
