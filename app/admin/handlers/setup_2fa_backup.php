<?php
/********************************************
 * 2FA Setup Page - AdSphere v2.0
 * TOTP 2FA with working code generation
 * Updated with test_2fa.php working logic
 ********************************************/
session_start();

// Check if this is mandatory setup (first-time login)
$isMandatory = isset($_GET['mandatory']) && $_GET['mandatory'] === '1';

// For mandatory setup, check pending_2fa_setup session
if ($isMandatory) {
    if (!isset($_SESSION['pending_2fa_setup'])) {
        header("Location: ../login.php");
        exit();
    }

    // Timeout check (10 minutes for setup)
    if (time() - $_SESSION['pending_2fa_setup']['time'] > 600) {
        unset($_SESSION['pending_2fa_setup']);
        header("Location: ../login.php?error=setup_timeout");
        exit();
    }

    $username = $_SESSION['pending_2fa_setup']['username'];
    $ip = $_SESSION['pending_2fa_setup']['ip'];
} else {
    // Optional setup (already logged in)
    if (!isset($_SESSION['admin_logged_in']) || $_SESSION['admin_logged_in'] !== true) {
        header("Location: ../login.php");
        exit();
    }

    $username = $_SESSION['admin_username'];
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'Unknown';
}

// Include TOTP functions
require_once __DIR__ . '/twoauth.php';

// Load admin data
$adminsFile = __DIR__ . "/../../config/admins.json";
$admins = json_decode(file_get_contents($adminsFile), true) ?? [];
$admin = $admins[$username] ?? null;

if (!$admin) {
    die("Admin not found");
}

$errorMsg = "";
$successMsg = "";

// Generate new secret if not exists or requested
if (!isset($_GET['action']) || $_GET['action'] === 'generate') {
    $secret = generateSecret();
    $_SESSION['temp_2fa_secret'] = $secret;
} else {
    $secret = $_SESSION['temp_2fa_secret'] ?? generateSecret();
    $_SESSION['temp_2fa_secret'] = $secret;
}

// Generate TOTP codes using the WORKING logic from test_2fa.php
$currentTimeSlice = floor(time() / 30);
$currentCode = generateTOTP($secret, $currentTimeSlice);

// Generate all valid codes (±3 for Google Authenticator compatibility)
$validCodes = [];
for ($i = -3; $i <= 3; $i++) {
    $timeSlice = $currentTimeSlice + $i;
    $code = generateTOTP($secret, $timeSlice);
    $offsetSeconds = $i * 30;
    $label = $i === 0 ? 'NOW (Current)' : ($i < 0 ? "{$offsetSeconds}s ago" : "+{$offsetSeconds}s");
    $validCodes[] = [
        'offset' => $i,
        'label' => $label,
        'timeSlice' => $timeSlice,
        'code' => $code,
        'offsetSeconds' => $offsetSeconds,
        'isCurrent' => ($i === 0)
    ];
}

// Generate QR code URL
$issuer = urlencode("AdSphere Admin");
$otpAuthUrl = "otpauth://totp/{$issuer}:{$username}?secret={$secret}&issuer={$issuer}";

// Use QR Server API (more reliable than deprecated Google Chart API)
$qrUrl = "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=" . urlencode($otpAuthUrl);


// Generate backup codes
$backupCodes = [];
for ($i = 0; $i < 10; $i++) {
    $backupCodes[] = strtoupper(bin2hex(random_bytes(4)));
}

// Handle verification and activation
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['code'])) {
    $code = trim($_POST['code']);

    // Validate code format
    if (!preg_match('/^[0-9]{6}$/', $code)) {
        $errorMsg = "Code must be exactly 6 digits. You entered: " . htmlspecialchars($code);
    } else {

        // Enable debug mode for verification
        $isValid = verifyTOTP($secret, $code, true);

        // Also try current code generation for debugging
        $currentTimeSlice = floor(time() / 30);
        $currentCode = generateTOTP($secret, $currentTimeSlice);

        // Log debug info
        error_log("=== 2FA Setup Debug ===");
        error_log("Secret from session: " . $secret);
        error_log("User entered code: " . $code);
        error_log("Current expected code: " . $currentCode);
        error_log("Current time: " . date('Y-m-d H:i:s'));
        error_log("TimeSlice: " . $currentTimeSlice);
        error_log("Verification result: " . ($isValid ? 'SUCCESS' : 'FAILED'));

        if ($isValid) {
            // Save 2FA secret and backup codes
            $admins[$username]['2fa_enabled'] = true;
            $admins[$username]['2fa_secret'] = $secret;
            $admins[$username]['backup_codes'] = $backupCodes;

            file_put_contents($adminsFile, json_encode($admins, JSON_PRETTY_PRINT));
            chmod($adminsFile, 0600);

            unset($_SESSION['temp_2fa_secret']);

            $successMsg = "Two-Factor Authentication has been successfully enabled!";

            // Log the event
            $logDir = __DIR__ . "/../../companies/logs/";
            $logFile = $logDir . "security_" . date('Y-m-d') . ".log";
            $timestamp = date('Y-m-d H:i:s');
            $logEntry = "[{$timestamp}] 2FA_ENABLED | User: {$username} | IP: {$ip}\n";
            file_put_contents($logFile, $logEntry, FILE_APPEND | LOCK_EX);

            // If this was mandatory setup, complete the login
            if ($isMandatory) {
                unset($_SESSION['pending_2fa_setup']);

                // Complete login using the login.php function
                require_once __DIR__ . '/../login.php';
                completeLogin($username, $ip, $logDir);
            }

        } else {
            // Generate all valid codes for better error message
            $validCodes = [];
            for ($i = -3; $i <= 3; $i++) {
                $validCodes[] = generateTOTP($secret, $currentTimeSlice + $i);
            }

            $errorMsg = "Invalid code. The code you entered ($code) doesn't match any valid code. ";
            $errorMsg .= "Current expected code: $currentCode. ";
            $errorMsg .= "Valid codes right now: " . implode(', ', $validCodes) . ". ";
            $errorMsg .= "<br><br><strong>Google Authenticator users:</strong> Sync time in app (Menu → Settings → Time correction → Sync now), then try again with a fresh code.";
        }
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Setup 2FA - AdSphere</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
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
            box-shadow: 0 8px 32px 0 rgba(59, 130, 246, 0.2);
        }

        @media print {
            .no-print { display: none; }
        }
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">

    <div class="max-w-4xl mx-auto">

        <?php if ($isMandatory): ?>
        <!-- Mandatory Setup Warning -->
        <div class="mb-6 bg-yellow-600/20 border-2 border-yellow-500/50 rounded-2xl p-6 text-center">
            <div class="flex items-center justify-center gap-3 mb-3">
                <i class="fas fa-exclamation-triangle text-yellow-400 text-3xl"></i>
                <h2 class="text-2xl font-bold text-yellow-300">Security Requirement</h2>
            </div>
            <p class="text-yellow-200 text-lg mb-2">
                Two-Factor Authentication is now <strong>MANDATORY</strong> for all administrator accounts.
            </p>
            <p class="text-yellow-300/70 text-sm">
                You must complete this setup to access the admin dashboard. This adds an extra layer of security to your account.
            </p>
        </div>
        <?php endif; ?>

        <!-- Header -->
        <div class="text-center mb-8">
            <div class="w-20 h-20 bg-indigo-600/30 rounded-full flex items-center justify-center mx-auto mb-4 border-2 border-indigo-500/50">
                <i class="fas fa-shield-alt text-indigo-400 text-3xl"></i>
            </div>
            <h1 class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-sky-300 mb-2">
                <?php if ($isMandatory): ?>
                    <i class="fas fa-exclamation-circle text-yellow-400"></i>
                    Setup Two-Factor Authentication
                <?php else: ?>
                    Setup Two-Factor Authentication
                <?php endif; ?>
            </h1>
            <p class="text-sky-300/70">
                <?php if ($isMandatory): ?>
                    <strong class="text-yellow-300">⚠️ REQUIRED:</strong> Two-Factor Authentication is mandatory for all admin accounts
                <?php else: ?>
                    Secure your account with TOTP (Time-based One-Time Password)
                <?php endif; ?>
            </p>
        </div>

        <?php if ($successMsg): ?>

            <!-- Success Screen -->
            <div class="glass-card rounded-2xl p-8 mb-6">
                <div class="text-center mb-6">
                    <div class="w-16 h-16 bg-green-600/30 rounded-full flex items-center justify-center mx-auto mb-4">
                        <i class="fas fa-check-circle text-green-400 text-3xl"></i>
                    </div>
                    <h2 class="text-2xl font-bold text-green-400 mb-2"><?= $successMsg ?></h2>
                    <p class="text-sky-300/70">Save your backup codes and keep them in a secure place</p>
                </div>

                <!-- Backup Codes -->
                <div class="bg-yellow-600/20 border-2 border-yellow-500/30 rounded-xl p-6 mb-6">
                    <h3 class="text-xl font-bold text-yellow-200 mb-4 flex items-center gap-2">
                        <i class="fas fa-exclamation-triangle"></i>
                        Backup Recovery Codes
                    </h3>
                    <p class="text-yellow-300/70 mb-4 text-sm">
                        Each code can be used once if you lose access to your authenticator app.
                        <strong>Print or save these codes now!</strong>
                    </p>
                    <div class="grid grid-cols-2 gap-3">
                        <?php foreach($backupCodes as $code): ?>
                            <div class="bg-yellow-900/40 p-3 rounded-lg font-mono text-yellow-200 text-center text-lg border border-yellow-500/30">
                                <?= $code ?>
                            </div>
                        <?php endforeach; ?>
                    </div>
                </div>

                <div class="flex gap-4 justify-center">
                    <button onclick="window.print()" class="no-print px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-bold text-white transition">
                        <i class="fas fa-print mr-2"></i>Print Backup Codes
                    </button>
                    <a href="../admin_dashboard.php" class="no-print px-6 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 rounded-lg font-bold text-white transition">
                        <i class="fas fa-arrow-right mr-2"></i>Go to Dashboard
                    </a>
                </div>
            </div>

        <?php else: ?>

            <!-- Setup Steps -->
            <div class="space-y-6">

                <!-- Step 1: Download Authenticator App -->
                <div class="glass-card rounded-2xl p-6">
                    <div class="flex items-start gap-4">
                        <div class="w-12 h-12 bg-blue-600/30 rounded-full flex items-center justify-center flex-shrink-0">
                            <span class="text-2xl font-bold text-blue-400">1</span>
                        </div>
                        <div class="flex-1">
                            <h2 class="text-2xl font-bold text-sky-200 mb-3">Download an Authenticator App</h2>
                            <p class="text-sky-300/70 mb-4">Choose one of these apps for your smartphone:</p>
                            <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
                                <div class="bg-blue-900/30 p-3 rounded-lg text-center border border-blue-500/30">
                                    <i class="fab fa-google text-2xl text-blue-400 mb-2"></i>
                                    <p class="text-sm text-sky-200">Google Authenticator</p>
                                </div>
                                <div class="bg-blue-900/30 p-3 rounded-lg text-center border border-blue-500/30">
                                    <i class="fab fa-microsoft text-2xl text-cyan-400 mb-2"></i>
                                    <p class="text-sm text-sky-200">Microsoft Authenticator</p>
                                </div>
                                <div class="bg-blue-900/30 p-3 rounded-lg text-center border border-blue-500/30">
                                    <i class="fas fa-shield-alt text-2xl text-purple-400 mb-2"></i>
                                    <p class="text-sm text-sky-200">Authy</p>
                                </div>
                                <div class="bg-blue-900/30 p-3 rounded-lg text-center border border-blue-500/30">
                                    <i class="fas fa-key text-2xl text-green-400 mb-2"></i>
                                    <p class="text-sm text-sky-200">1Password</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Step 2: Scan QR Code -->
                <div class="glass-card rounded-2xl p-6">
                    <div class="flex items-start gap-4">
                        <div class="w-12 h-12 bg-purple-600/30 rounded-full flex items-center justify-center flex-shrink-0">
                            <span class="text-2xl font-bold text-purple-400">2</span>
                        </div>
                        <div class="flex-1">
                            <h2 class="text-2xl font-bold text-sky-200 mb-3">Scan the QR Code</h2>
                            <p class="text-sky-300/70 mb-4">Open your authenticator app and scan this QR code:</p>

                            <!-- QR Code Display with Fallbacks -->
                            <div class="bg-white p-6 rounded-xl inline-block relative" id="qrCodeContainer">
                                <img
                                    src="<?= $qrUrl ?>"
                                    alt="2FA QR Code"
                                    class="w-64 h-64"
                                    id="qrCodeImage"
                                    onerror="handleQRError()"
                                    onload="handleQRSuccess()">

                                <!-- Loading Indicator -->
                                <div id="qrLoading" class="absolute inset-0 flex items-center justify-center bg-white">
                                    <div class="text-center">
                                        <i class="fas fa-spinner fa-spin text-blue-600 text-4xl mb-2"></i>
                                        <p class="text-gray-600 text-sm">Generating QR Code...</p>
                                    </div>
                                </div>

                                <!-- Error Message -->
                                <div id="qrError" class="absolute inset-0 hidden flex-col items-center justify-center bg-red-50 p-4">
                                    <i class="fas fa-exclamation-triangle text-red-600 text-4xl mb-3"></i>
                                    <p class="text-red-600 font-bold mb-2">QR Code Failed to Load</p>
                                    <p class="text-red-500 text-sm text-center mb-4">Please use the manual entry method below instead</p>
                                    <button onclick="retryQR()" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-bold transition">
                                        <i class="fas fa-redo mr-2"></i>Retry
                                    </button>
                                </div>
                            </div>

                            <!-- Alternative QR URLs for Manual Testing -->
                            <details class="mt-4">
                                <summary class="text-xs text-sky-400/70 cursor-pointer hover:text-sky-300">Show alternative QR code URLs</summary>
                                <div class="mt-2 space-y-2 text-xs">
                                    <p class="text-sky-300/70">Try these if QR code doesn't load:</p>
                                    <div class="bg-blue-900/40 p-2 rounded border border-cyan-500/30">
                                        <a href="https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=<?= urlencode($otpAuthUrl) ?>" target="_blank" class="text-cyan-400 hover:text-cyan-300 break-all">
                                            QR Server API
                                        </a>
                                    </div>
                                    <div class="bg-blue-900/40 p-2 rounded border border-cyan-500/30">
                                        <a href="https://quickchart.io/qr?text=<?= urlencode($otpAuthUrl) ?>&size=300" target="_blank" class="text-cyan-400 hover:text-cyan-300 break-all">
                                            QuickChart API
                                        </a>
                                    </div>
                                    <div class="bg-blue-900/40 p-2 rounded border border-cyan-500/30">
                                        <a href="https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=<?= urlencode($otpAuthUrl) ?>" target="_blank" class="text-cyan-400 hover:text-cyan-300 break-all">
                                            Google Chart API (Legacy)
                                        </a>
                                    </div>
                                </div>
                            </details>
                        </div>
                    </div>
                </div>

                <!-- Step 3: Manual Entry (Optional) -->
                <div class="glass-card rounded-2xl p-6">
                    <div class="flex items-start gap-4">
                        <div class="w-12 h-12 bg-cyan-600/30 rounded-full flex items-center justify-center flex-shrink-0">
                            <span class="text-2xl font-bold text-cyan-400">3</span>
                        </div>
                        <div class="flex-1">
                            <h2 class="text-2xl font-bold text-sky-200 mb-3">Or Enter Secret Manually</h2>
                            <p class="text-sky-300/70 mb-3">Can't scan? Enter this secret key in your app:</p>
                            <div class="bg-blue-900/40 p-4 rounded-lg border-2 border-cyan-500/30">
                                <div class="flex items-center justify-between">
                                    <span class="font-mono text-cyan-300 text-xl tracking-wider"><?= $secret ?></span>
                                    <button onclick="copySecret()" class="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg text-sm font-bold transition">
                                        <i class="fas fa-copy mr-2"></i>Copy
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Step 4: Verify Code -->
                <div class="glass-card rounded-2xl p-6">
                    <div class="flex items-start gap-4">
                        <div class="w-12 h-12 bg-green-600/30 rounded-full flex items-center justify-center flex-shrink-0">
                            <span class="text-2xl font-bold text-green-400">4</span>
                        </div>
                        <div class="flex-1">
                            <h2 class="text-2xl font-bold text-sky-200 mb-3">Verify & Enable</h2>
                            <p class="text-sky-300/70 mb-4">Compare the code in your authenticator app with the codes below, then enter it:</p>

                            <!-- CURRENT EXPECTED CODE - BIG DISPLAY (from working test_2fa.php) -->
                            <div class="mb-6 bg-gradient-to-br from-green-600 to-emerald-700 rounded-2xl p-6 text-center shadow-2xl">
                                <p class="text-green-200 text-sm mb-2">
                                    <i class="fas fa-check-circle mr-2"></i>
                                    CURRENT EXPECTED CODE
                                </p>
                                <p class="text-6xl font-mono font-bold tracking-wider mb-3"><?= $currentCode ?></p>
                                <p class="text-green-200 text-xs">
                                    ✅ Your authenticator app should show this code RIGHT NOW
                                </p>
                                <p class="text-green-300 text-xs mt-1">
                                    Code refreshes every 30 seconds | Time until next: <span class="pulse"><?= 30 - (time() % 30) ?>s</span>
                                </p>
                            </div>

                            <!-- ALL VALID CODES (from working test_2fa.php) -->
                            <div class="mb-4 bg-white/10 backdrop-blur rounded-xl p-4">
                                <h3 class="text-lg font-bold text-sky-200 mb-3">📊 All 7 Valid Codes (±90 seconds)</h3>
                                <p class="text-blue-300 text-xs mb-3">Any of these codes will work:</p>
                                <div class="space-y-2">
                                    <?php foreach($validCodes as $codeInfo): ?>
                                        <div class="flex items-center justify-between p-3 rounded-lg <?= $codeInfo['isCurrent'] ? 'bg-green-600/30 border-2 border-green-500' : 'bg-white/5' ?>">
                                            <div>
                                                <p class="font-semibold <?= $codeInfo['isCurrent'] ? 'text-green-300' : 'text-sky-200' ?>">
                                                    <?= $codeInfo['label'] ?> <?= $codeInfo['isCurrent'] ? '← CURRENT' : '' ?>
                                                </p>
                                                <p class="text-xs text-blue-300">TimeSlice: <?= $codeInfo['timeSlice'] ?></p>
                                            </div>
                                            <div class="text-3xl font-mono font-bold <?= $codeInfo['isCurrent'] ? 'text-green-300' : 'text-sky-200' ?>">
                                                <?= $codeInfo['code'] ?>
                                            </div>
                                        </div>
                                    <?php endforeach; ?>
                                </div>
                            </div>

                            <!-- Google Authenticator Time Sync Notice -->
                            <div class="mb-4 p-3 bg-blue-600/20 border border-blue-500/50 rounded-lg">
                                <div class="flex items-start gap-2">
                                    <i class="fas fa-info-circle text-blue-400 text-sm mt-1"></i>
                                    <div class="text-xs">
                                        <p class="text-blue-200 font-semibold mb-1">
                                            Google Authenticator: Sync time first!
                                        </p>
                                        <p class="text-blue-300">Menu (⋮) → Settings → Time correction → Sync now</p>
                                    </div>
                                </div>
                            </div>

                            <?php if ($errorMsg): ?>
                                <div class="mb-4 p-4 bg-red-600/20 border border-red-600/50 rounded-xl">
                                    <div class="flex items-start gap-3">
                                        <i class="fas fa-exclamation-triangle text-red-400 text-xl mt-1"></i>
                                        <div class="text-red-400 text-sm">
                                            <?= $errorMsg ?>
                                        </div>
                                    </div>
                                </div>
                            <?php endif; ?>


                            <form method="POST" class="space-y-4">
                                <input
                                    type="text"
                                    name="code"
                                    maxlength="6"
                                    pattern="[0-9]{6}"
                                    inputmode="numeric"
                                    class="w-full px-6 py-4 bg-blue-900/40 border-2 border-cyan-500/30 rounded-xl text-white text-3xl text-center font-mono tracking-widest focus:outline-none focus:border-cyan-400 transition"
                                    placeholder="000000"
                                    autofocus
                                    required>

                                <button type="submit" class="w-full py-4 bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 hover:from-green-700 hover:via-emerald-700 hover:to-teal-700 rounded-xl font-bold text-white text-lg transition-all transform hover:scale-105">
                                    <i class="fas fa-check-circle mr-2"></i>Enable Two-Factor Authentication
                                </button>
                            </form>

                            <?php if (!$isMandatory): ?>
                            <div class="mt-4 text-center">
                                <a href="../admin_dashboard.php" class="text-sky-400 hover:text-sky-300 text-sm transition">
                                    <i class="fas fa-times mr-2"></i>Cancel
                                </a>
                            </div>
                            <?php else: ?>
                            <div class="mt-4 text-center">
                                <p class="text-xs text-yellow-300/70">
                                    <i class="fas fa-lock mr-1"></i>
                                    You must complete 2FA setup to access your account
                                </p>
                            </div>
                            <?php endif; ?>
                        </div>
                    </div>
                </div>

            </div>

        <?php endif; ?>

    </div>

    <script>
        // QR Code URLs (fallback order)
        const qrUrls = [
            'https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=<?= urlencode($otpAuthUrl) ?>',
            'https://quickchart.io/qr?text=<?= urlencode($otpAuthUrl) ?>&size=300',
            'https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=<?= urlencode($otpAuthUrl) ?>'
        ];
        let currentQRIndex = 0;

        function handleQRSuccess() {
            console.log('✅ QR Code loaded successfully');
            document.getElementById('qrLoading').style.display = 'none';
        }

        function handleQRError() {
            console.error('❌ QR Code failed to load from:', qrUrls[currentQRIndex]);

            currentQRIndex++;

            // Try next URL
            if (currentQRIndex < qrUrls.length) {
                console.log('🔄 Trying fallback QR URL:', qrUrls[currentQRIndex]);
                const img = document.getElementById('qrCodeImage');
                img.src = qrUrls[currentQRIndex];
            } else {
                // All URLs failed - show error
                console.error('❌ All QR code URLs failed');
                document.getElementById('qrLoading').style.display = 'none';
                const errorDiv = document.getElementById('qrError');
                errorDiv.style.display = 'flex';
            }
        }

        function retryQR() {
            // Reset and try first URL again
            currentQRIndex = 0;
            const img = document.getElementById('qrCodeImage');
            const errorDiv = document.getElementById('qrError');
            const loadingDiv = document.getElementById('qrLoading');

            errorDiv.style.display = 'none';
            loadingDiv.style.display = 'flex';

            // Force reload by adding timestamp
            img.src = qrUrls[0] + '&t=' + Date.now();

            console.log('🔄 Retrying QR code generation...');
        }

        function copySecret() {
            const secret = '<?= $secret ?>';
            navigator.clipboard.writeText(secret).then(() => {
                const btn = event.target.closest('button');
                const originalHTML = btn.innerHTML;
                btn.innerHTML = '<i class="fas fa-check mr-2"></i>Copied!';
                btn.classList.add('bg-green-600');
                btn.classList.remove('bg-cyan-600');
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.classList.remove('bg-green-600');
                    btn.classList.add('bg-cyan-600');
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
                alert('Failed to copy. Please select and copy manually.');
            });
        }

        // Debug: Log QR code data on page load
        console.log('🔑 2FA Secret:', '<?= $secret ?>');
        console.log('🔗 OTP Auth URL:', '<?= $otpAuthUrl ?>');
        console.log('📱 QR Code URLs:', qrUrls);
    </script>

</body>
</html>

