<?php
/**
 * ADMIN SERVICE - 2FA Verification Page
 * Port 8002
 */

// Session already started by index.php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

// Define BASE_PATH if not defined
if (!defined('BASE_PATH')) {
    define('BASE_PATH', dirname(dirname(dirname(__DIR__))));
}

// Check for pending 2FA setup (from login - password verified but 2FA not set up)
$isPendingSetup = isset($_SESSION['pending_2fa_setup']);
// Check for pending 2FA verification (from login - password verified, 2FA is set up, needs code)
$isPendingVerify = isset($_SESSION['pending_2fa']);
// Check if already fully logged in
$isLoggedIn = isset($_SESSION['admin_logged_in']) && $_SESSION['admin_logged_in'] === true;

// Must have one of these to access this page
if (!$isLoggedIn && !$isPendingSetup && !$isPendingVerify) {
    header('Location: /login');
    exit();
}

// Redirect if already 2FA verified
if (isset($_SESSION['admin_2fa_verified']) && $_SESSION['admin_2fa_verified'] === true) {
    header('Location: /dashboard');
    exit();
}

// Get username from the appropriate session variable
if ($isPendingSetup) {
    $username = $_SESSION['pending_2fa_setup']['username'] ?? '';
} elseif ($isPendingVerify) {
    $username = $_SESSION['pending_2fa']['username'] ?? '';
} else {
    $username = $_SESSION['admin_username'] ?? '';
}

if (empty($username)) {
    header('Location: /login');
    exit();
}

$error = '';
$showSetup = false;

// Check if user has 2FA setup - use local config directory first, fallback to app
$secretsFile = __DIR__ . '/../config/2fa_secrets.json';
if (!file_exists($secretsFile)) {
    $secretsFile = BASE_PATH . '/services/admin/handlers/2fa_secrets.json';
}

$secrets = [];
if (file_exists($secretsFile)) {
    $secrets = json_decode(file_get_contents($secretsFile), true) ?: [];
}

$userSecret = $secrets[$username] ?? null;

if (!$userSecret) {
    // Need to setup 2FA
    $showSetup = true;

    // Generate new secret if not in session
    if (!isset($_SESSION['temp_2fa_secret'])) {
        $chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
        $secret = '';
        for ($i = 0; $i < 32; $i++) {
            $secret .= $chars[random_int(0, strlen($chars) - 1)];
        }
        $_SESSION['temp_2fa_secret'] = $secret;
    }
    $secret = $_SESSION['temp_2fa_secret'];
    $otpAuthUrl = "otpauth://totp/AdSphere%20Admin:{$username}?secret={$secret}&issuer=AdSphere%20Admin";
}

// Handle verification
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $code = preg_replace('/\s+/', '', $_POST['code'] ?? '');

    $secretToVerify = $userSecret ?: $_SESSION['temp_2fa_secret'] ?? '';

    if ($secretToVerify && verifyTOTP($secretToVerify, $code)) {
        // Save secret if this was setup
        if (!$userSecret && isset($_SESSION['temp_2fa_secret'])) {
            $secrets[$username] = $_SESSION['temp_2fa_secret'];
            file_put_contents($secretsFile, json_encode($secrets, JSON_PRETTY_PRINT));

            // Also update admins.json to mark 2FA as enabled
            $adminsFile = __DIR__ . '/../config/admins.json';
            if (file_exists($adminsFile)) {
                $admins = json_decode(file_get_contents($adminsFile), true) ?: [];
                if (isset($admins[$username])) {
                    $admins[$username]['2fa_enabled'] = true;
                    $admins[$username]['2fa_secret'] = $_SESSION['temp_2fa_secret'];
                    file_put_contents($adminsFile, json_encode($admins, JSON_PRETTY_PRINT));
                }
            }

            unset($_SESSION['temp_2fa_secret']);
        }

        // Complete the login - set ALL required session variables
        $_SESSION['admin_logged_in'] = true;
        $_SESSION['admin_username'] = $username;
        $_SESSION['admin_role'] = 'super_admin';
        $_SESSION['admin_2fa_verified'] = true;
        $_SESSION['admin_last_activity'] = time();
        $_SESSION['login_time'] = time();

        // Clear pending states
        unset($_SESSION['pending_2fa_setup']);
        unset($_SESSION['pending_2fa']);

        header('Location: /dashboard');
        exit();
    } else {
        $error = 'Invalid verification code. Please try again.';
    }
}

// TOTP verification function
function verifyTOTP($secret, $code, $window = 1) {
    $timeSlice = floor(time() / 30);

    for ($i = -$window; $i <= $window; $i++) {
        $calculatedCode = getTOTPCode($secret, $timeSlice + $i);
        if (hash_equals($calculatedCode, str_pad($code, 6, '0', STR_PAD_LEFT))) {
            return true;
        }
    }
    return false;
}

function getTOTPCode($secret, $timeSlice) {
    $secretKey = base32Decode($secret);
    $time = pack('N*', 0, $timeSlice);
    $hash = hash_hmac('sha1', $time, $secretKey, true);
    $offset = ord(substr($hash, -1)) & 0x0F;
    $code = (
        ((ord($hash[$offset]) & 0x7F) << 24) |
        ((ord($hash[$offset + 1]) & 0xFF) << 16) |
        ((ord($hash[$offset + 2]) & 0xFF) << 8) |
        (ord($hash[$offset + 3]) & 0xFF)
    ) % 1000000;
    return str_pad($code, 6, '0', STR_PAD_LEFT);
}

function base32Decode($input) {
    $alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
    $output = '';
    $buffer = 0;
    $bitsLeft = 0;

    for ($i = 0; $i < strlen($input); $i++) {
        $val = strpos($alphabet, strtoupper($input[$i]));
        if ($val === false) continue;

        $buffer = ($buffer << 5) | $val;
        $bitsLeft += 5;

        if ($bitsLeft >= 8) {
            $bitsLeft -= 8;
            $output .= chr(($buffer >> $bitsLeft) & 0xFF);
        }
    }
    return $output;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2FA Verification - AdSphere Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        }
        .glass {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4">

<div class="glass rounded-2xl p-8 w-full max-w-md">
    <div class="text-center mb-8">
        <div class="w-20 h-20 bg-gradient-to-br from-green-500 to-teal-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <i class="fas fa-key text-white text-3xl"></i>
        </div>
        <h1 class="text-2xl font-bold text-white">
            <?= $showSetup ? 'Setup 2FA' : 'Verify 2FA' ?>
        </h1>
        <p class="text-gray-400 text-sm">
            <?= $showSetup ? 'Scan the QR code with your authenticator app' : 'Enter the code from your authenticator app' ?>
        </p>
    </div>

    <?php if ($error): ?>
        <div class="bg-red-500/20 border border-red-500/50 text-red-300 px-4 py-3 rounded-lg mb-6 text-sm">
            <i class="fas fa-exclamation-circle mr-2"></i><?= htmlspecialchars($error) ?>
        </div>
    <?php endif; ?>

    <?php if ($showSetup): ?>
        <!-- QR Code for setup -->
        <div class="bg-white p-4 rounded-lg mb-6 text-center">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=<?= urlencode($otpAuthUrl) ?>"
                 alt="QR Code" class="mx-auto">
        </div>

        <div class="bg-white/5 rounded-lg p-4 mb-6">
            <p class="text-gray-400 text-xs mb-2">Manual key:</p>
            <code class="text-green-400 text-sm break-all"><?= $secret ?></code>
        </div>
    <?php endif; ?>

    <form method="POST" class="space-y-6">
        <div>
            <label class="block text-gray-300 text-sm mb-2">Verification Code</label>
            <input type="text" name="code" required maxlength="6" pattern="[0-9]{6}"
                class="w-full bg-white/5 border border-white/10 text-white text-center text-2xl tracking-[0.5em] px-4 py-4 rounded-lg focus:outline-none focus:border-green-500 transition"
                placeholder="000000" autofocus>
        </div>

        <button type="submit" class="w-full bg-gradient-to-r from-green-500 to-teal-600 text-white py-3 rounded-lg font-semibold hover:opacity-90 transition">
            <i class="fas fa-check mr-2"></i>Verify
        </button>
    </form>

    <div class="mt-6 text-center">
        <a href="/logout" class="text-gray-500 hover:text-gray-300 text-sm">
            <i class="fas fa-arrow-left mr-1"></i>Back to login
        </a>
    </div>
</div>

</body>
</html>

