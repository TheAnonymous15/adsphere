<?php
/********************************************
 * 2FA Verification Handler - AdSphere
 * Integrates with TOTP authentication
 ********************************************/
session_start();

// Check if 2FA is pending
if (!isset($_SESSION['pending_2fa'])) {
    header("Location: ../login.php");
    exit();
}

// Timeout check (5 minutes)
if (time() - $_SESSION['pending_2fa']['time'] > 300) {
    unset($_SESSION['pending_2fa']);
    header("Location: ../login.php?error=2fa_timeout");
    exit();
}

$username = $_SESSION['pending_2fa']['username'];
$ip = $_SESSION['pending_2fa']['ip'];

// Include TOTP functions from twoauth.php
require_once __DIR__ . '/twoauth.php';

// Load admin data
$adminsFile = __DIR__ . "/../../config/admins.json";
$admins = json_decode(file_get_contents($adminsFile), true) ?? [];
$admin = $admins[$username] ?? null;

if (!$admin || !isset($admin['2fa_secret'])) {
    unset($_SESSION['pending_2fa']);
    header("Location: ../login.php?error=2fa_not_configured");
    exit();
}

$logDir = __DIR__ . "/../../companies/logs/";
$errorMsg = "";

// Handle 2FA verification
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $code = trim($_POST['code'] ?? '');

    if (empty($code) || !preg_match('/^[0-9]{6}$/', $code)) {
        $errorMsg = "Invalid code format. Please enter 6 digits.";
    } else {

        // Verify TOTP code (without debug logging)
        if (verifyTOTP($admin['2fa_secret'], $code)) {

            // 2FA Successful
            require_once __DIR__ . '/../login.php';
            completeLogin($username, $ip, $logDir);

        } else {

            // Check backup codes if available
            $backupUsed = false;
            if (isset($admin['backup_codes']) && is_array($admin['backup_codes'])) {
                $backupIndex = array_search($code, $admin['backup_codes'], true);
                if ($backupIndex !== false) {
                    // Valid backup code - remove it
                    $admins[$username]['backup_codes'] = array_values(
                        array_diff($admin['backup_codes'], [$code])
                    );
                    file_put_contents($adminsFile, json_encode($admins, JSON_PRETTY_PRINT));
                    $backupUsed = true;

                    // Complete login
                    require_once __DIR__ . '/../login.php';
                    completeLogin($username, $ip, $logDir);
                }
            }

            if (!$backupUsed) {
                $errorMsg = "Invalid authentication code. Please try again.";

                // Log failed 2FA attempt (without exposing codes)
                $logFile = $logDir . "security_" . date('Y-m-d') . ".log";
                $timestamp = date('Y-m-d H:i:s');
                $logEntry = "[{$timestamp}] 2FA_FAILED | User: {$username} | IP: {$ip}\n";
                file_put_contents($logFile, $logEntry, FILE_APPEND | LOCK_EX);
            }
        }
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2FA Verification - AdSphere</title>
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

        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button {
            -webkit-appearance: none;
            margin: 0;
        }
        input[type=number] {
            -moz-appearance: textfield;
        }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4">

    <div class="w-full max-w-md">
        <div class="text-center mb-8">
            <div class="w-20 h-20 bg-cyan-600/30 rounded-full flex items-center justify-center mx-auto mb-4 border-2 border-cyan-500/50">
                <i class="fas fa-mobile-alt text-cyan-400 text-3xl"></i>
            </div>
            <h1 class="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 via-cyan-400 to-sky-300 mb-2">
                Two-Factor Authentication
            </h1>
            <p class="text-sky-300/70">Enter the 6-digit code from your authenticator app</p>
        </div>

        <div class="glass-card rounded-2xl p-8">

            <!-- Google Authenticator Sync Notice -->
            <div class="mb-4 p-4 bg-blue-600/20 border border-blue-500/50 rounded-xl">
                <div class="flex items-start gap-3">
                    <i class="fas fa-info-circle text-blue-400"></i>
                    <div class="text-sm">
                        <p class="text-blue-200 font-semibold mb-1">Google Authenticator users: Sync time first!</p>
                        <p class="text-blue-300 text-xs">Menu (⋮) → Settings → Time correction → Sync now</p>
                    </div>
                </div>
            </div>


            <?php if ($errorMsg): ?>
                <div class="mb-6 p-4 bg-red-600/20 border border-red-600/50 rounded-xl">
                    <div class="flex items-start gap-3">
                        <i class="fas fa-exclamation-triangle text-red-400"></i>
                        <div class="text-red-400 text-sm"><?= $errorMsg ?></div>
                    </div>
                </div>
            <?php endif; ?>

            <form method="POST" class="space-y-6" id="2faForm">
                <div>
                    <label class="block text-sky-200 text-sm font-bold mb-3 text-center">
                        <i class="fas fa-key text-cyan-400 mr-2"></i>
                        Authentication Code
                    </label>
                    <input
                        type="text"
                        name="code"
                        id="codeInput"
                        maxlength="6"
                        pattern="[0-9]{6}"
                        inputmode="numeric"
                        class="w-full px-6 py-4 bg-blue-900/40 border-2 border-cyan-500/30 rounded-xl text-white text-3xl text-center font-mono tracking-widest focus:outline-none focus:border-cyan-400 transition"
                        placeholder="000000"
                        autofocus
                        required>
                </div>

                <button
                    type="submit"
                    class="w-full py-4 bg-gradient-to-r from-blue-600 via-blue-700 to-cyan-600 hover:from-blue-700 hover:via-blue-800 hover:to-cyan-700 rounded-xl font-bold text-white text-lg transition-all transform hover:scale-105">
                    <i class="fas fa-check-circle mr-2"></i>Verify Code
                </button>

                <div class="text-center">
                    <a href="../login.php" class="text-cyan-400 hover:text-cyan-300 text-sm transition">
                        <i class="fas fa-arrow-left mr-2"></i>Back to Login
                    </a>
                </div>
            </form>

            <div class="mt-6 pt-6 border-t border-white/10">
                <p class="text-xs text-sky-300/50 text-center mb-3">
                    <i class="fas fa-info-circle mr-1"></i>
                    Lost your device? Use a backup code or contact support
                </p>
                <div class="text-center">
                    <button onclick="showBackupCodeInput()" class="text-xs text-cyan-400 hover:text-cyan-300 transition">
                        Enter backup code instead
                    </button>
                </div>
            </div>

        </div>

        <!-- Session Timeout Warning -->
        <div class="mt-4 text-center text-xs text-sky-400/50">
            <i class="fas fa-clock mr-1"></i>
            This session will expire in <span id="countdown">5:00</span>
        </div>
    </div>

    <script>
        const codeInput = document.getElementById('codeInput');
        let isBackupMode = false;

        // Handle input based on mode (TOTP or Backup)
        codeInput.addEventListener('input', function(e) {
            if (isBackupMode) {
                // Backup code mode: alphanumeric, auto-uppercase
                this.value = this.value.replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
            } else {
                // TOTP mode: numbers only, auto-submit at 6 digits
                this.value = this.value.replace(/[^0-9]/g, '');
                if(this.value.length === 6) {
                    document.getElementById('2faForm').submit();
                }
            }
        });

        // Session countdown timer
        let timeLeft = 300; // 5 minutes
        const countdownElem = document.getElementById('countdown');

        setInterval(() => {
            timeLeft--;
            if (timeLeft <= 0) {
                window.location.href = '../login.php?error=2fa_timeout';
            }
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            countdownElem.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);

        // Show backup code input
        function showBackupCodeInput() {
            isBackupMode = true;
            codeInput.placeholder = "BACKUP-CODE";
            codeInput.maxLength = 16;
            codeInput.pattern = "[A-Z0-9]{8,16}";
            codeInput.value = "";
            codeInput.type = "text";
            codeInput.focus();
        }
    </script>

</body>
</html>

