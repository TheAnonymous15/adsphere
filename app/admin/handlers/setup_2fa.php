<?php
/********************************************
 * 2FA Setup Page - AdSphere
 * Complete 2FA enrollment for admin accounts
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
    die("Admin account not found");
}

$errorMsg = "";
$successMsg = "";

// Generate or retrieve secret
if (!isset($_SESSION['temp_2fa_secret']) || isset($_GET['action']) && $_GET['action'] === 'generate') {
    $secret = generateSecret();
    $_SESSION['temp_2fa_secret'] = $secret;
} else {
    $secret = $_SESSION['temp_2fa_secret'];
}

// Generate backup codes
$backupCodes = [];
for ($i = 0; $i < 10; $i++) {
    $backupCodes[] = strtoupper(bin2hex(random_bytes(4)));
}

$currentTimeSlice = floor(time() / 30);
$currentCode = generateTOTP($secret, $currentTimeSlice);

// Handle 2FA verification and activation
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['test_code'])) {
    $testCode = trim($_POST['test_code']);

    // Validate code format
    if (!preg_match('/^[0-9]{6}$/', $testCode)) {
        $errorMsg = "Code must be exactly 6 digits.";
    } else {
        // Verify TOTP code
        $isValid = verifyTOTP($secret, $testCode, true);

        if ($isValid) {
            // Save 2FA secret and backup codes to admin account
            $admins[$username]['2fa_enabled'] = true;
            $admins[$username]['2fa_secret'] = $secret;
            $admins[$username]['backup_codes'] = $backupCodes;
            $admins[$username]['2fa_enabled_at'] = time();

            file_put_contents($adminsFile, json_encode($admins, JSON_PRETTY_PRINT));
            chmod($adminsFile, 0600);

            // Clear temporary secret
            unset($_SESSION['temp_2fa_secret']);

            // Log the event
            $logDir = __DIR__ . "/../../companies/logs/";
            if (!is_dir($logDir)) mkdir($logDir, 0755, true);
            $logFile = $logDir . "security_" . date('Y-m-d') . ".log";
            $timestamp = date('Y-m-d H:i:s');
            $logEntry = "[{$timestamp}] 2FA_ENABLED | User: {$username} | IP: {$ip}\n";
            file_put_contents($logFile, $logEntry, FILE_APPEND | LOCK_EX);

            $successMsg = "Two-Factor Authentication has been successfully enabled!";

            // If this was mandatory setup, complete the login
            if ($isMandatory) {
                unset($_SESSION['pending_2fa_setup']);

                // Complete login
                session_regenerate_id(true);
                $_SESSION['admin_logged_in'] = true;
                $_SESSION['admin_username'] = $username;
                $_SESSION['admin_role'] = 'super_admin';
                $_SESSION['login_time'] = time();
                $_SESSION['last_activity'] = time();
                $_SESSION['ip_address'] = $ip;

                // Redirect will happen after showing backup codes
            }
        } else {
            $errorMsg = "Invalid code. Please try again with the current code from your authenticator app.";
        }
    }
}

// Generate codes for surrounding time windows (±3 for Google Authenticator)
$codes = [];
for ($i = -3; $i <= 3; $i++) {
    $timeSlice = $currentTimeSlice + $i;
    $code = generateTOTP($secret, $timeSlice);
    $offsetSeconds = $i * 30;
    $label = $i === 0 ? 'NOW (Current)' : ($i < 0 ? "{$offsetSeconds}s ago" : "+{$offsetSeconds}s");
    $codes[] = [
        'offset' => $i,
        'label' => $label,
        'timeSlice' => $timeSlice,
        'code' => $code,
        'offsetSeconds' => $offsetSeconds
    ];
}

?>
<!DOCTYPE html>
<html>
<head>
    <title>2FA Test - TOTP Code Generator</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .pulse { animation: pulse 2s infinite; }

        .updating {
            opacity: 0.7;
            transition: opacity 0.3s ease;
        }
    </style>
</head>
<body class="bg-gradient-to-br from-blue-900 to-indigo-900 min-h-screen p-8 text-white">

    <div class="max-w-4xl mx-auto">

        <?php if ($successMsg): ?>
            <!-- SUCCESS STATE - Show Backup Codes -->
            <div class="text-center mb-8">
                <div class="w-20 h-20 bg-green-600/30 rounded-full flex items-center justify-center mx-auto mb-4 border-2 border-green-500/50">
                    <i class="fas fa-check-circle text-green-400 text-4xl"></i>
                </div>
                <h1 class="text-4xl font-bold mb-2 text-green-400">✅ 2FA Setup Complete!</h1>
                <p class="text-green-300"><?= htmlspecialchars($successMsg) ?></p>
            </div>

            <!-- Backup Codes -->
            <div class="bg-yellow-600/20 border-2 border-yellow-500/30 rounded-xl p-6 mb-6">
                <h2 class="text-2xl font-bold text-yellow-200 mb-4 flex items-center gap-2">
                    <i class="fas fa-exclamation-triangle"></i>
                    Save Your Backup Recovery Codes
                </h2>
                <p class="text-yellow-300 mb-4 text-sm">
                    <strong>⚠️ IMPORTANT:</strong> Each code can be used once if you lose access to your authenticator app.
                    <strong>Print or save these codes now!</strong> You won't see them again.
                </p>
                <div class="grid grid-cols-2 gap-3 mb-4">
                    <?php foreach($backupCodes as $code): ?>
                        <div class="bg-yellow-900/40 p-3 rounded-lg font-mono text-yellow-200 text-center text-lg border border-yellow-500/30">
                            <?= $code ?>
                        </div>
                    <?php endforeach; ?>
                </div>
                <div class="flex gap-3 justify-center">
                    <button onclick="window.print()" class="px-6 py-3 bg-yellow-600 hover:bg-yellow-700 rounded-lg font-bold text-white transition">
                        <i class="fas fa-print mr-2"></i>Print Backup Codes
                    </button>
                    <button onclick="copyBackupCodes()" id="copyBackupBtn" class="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-bold text-white transition">
                        <i class="fas fa-copy mr-2"></i>Copy All Codes
                    </button>
                </div>
            </div>

            <!-- Redirect to Dashboard -->
            <div class="bg-white/10 backdrop-blur rounded-xl p-6 text-center">
                <p class="text-lg mb-4">You will be redirected to the dashboard in <span id="countdown" class="font-bold text-cyan-400">10</span> seconds...</p>
                <a href="../admin_dashboard.php" class="inline-block px-8 py-4 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 rounded-xl font-bold text-white text-lg transition-all transform hover:scale-105">
                    <i class="fas fa-arrow-right mr-2"></i>Go to Dashboard Now
                </a>
            </div>

        <?php else: ?>
            <!-- SETUP STATE - Show QR and Verification Form -->
            <div class="text-center mb-8">
                <h1 class="text-4xl font-bold mb-2">🔐 Setup Two-Factor Authentication</h1>
                <p class="text-blue-300">
                    <?php if ($isMandatory): ?>
                        <span class="text-yellow-300">⚠️ REQUIRED:</span> Two-Factor Authentication is mandatory for all admin accounts
                    <?php else: ?>
                        Secure your account with TOTP (Time-based One-Time Password)
                    <?php endif; ?>
                </p>
            </div>

            <?php if ($errorMsg): ?>
                <div class="mb-6 p-4 bg-red-600/20 border border-red-600/50 rounded-xl">
                    <div class="flex items-start gap-3">
                        <i class="fas fa-exclamation-triangle text-red-400 text-xl"></i>
                        <p class="text-red-400 font-semibold"><?= htmlspecialchars($errorMsg) ?></p>
                    </div>
                </div>
            <?php endif; ?>

        <!-- Current Time Info -->
        <div class="bg-white/10 backdrop-blur rounded-xl p-6 mb-6">
            <h2 class="text-2xl font-bold mb-4">⏰ Server Time Information</h2>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <p class="text-blue-300 text-sm">Current Server Time</p>
                    <p class="text-2xl font-mono"><?= date('Y-m-d H:i:s') ?></p>
                </div>
                <div>
                    <p class="text-blue-300 text-sm">Unix Timestamp</p>
                    <p class="text-2xl font-mono"><?= time() ?></p>
                </div>
                <div>
                    <p class="text-blue-300 text-sm">Current TimeSlice</p>
                    <p class="text-2xl font-mono"><?= $currentTimeSlice ?></p>
                </div>
                <div>
                    <p class="text-blue-300 text-sm">Seconds Until Next Code</p>
                    <p class="text-2xl font-mono pulse"><?= 30 - (time() % 30) ?>s</p>
                </div>
            </div>
        </div>


        <!-- QR CODE GENERATION -->
        <?php
        // Generate OTP Auth URL for QR code
        $issuer = urlencode("AdSphere Admin");
        $accountName = "admin"; // You can make this dynamic
        $otpAuthUrl = "otpauth://totp/{$issuer}:{$accountName}?secret={$secret}&issuer={$issuer}";

        // Multiple QR code URLs (fallbacks)
        $qrUrl1 = "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=" . urlencode($otpAuthUrl);
        $qrUrl2 = "https://quickchart.io/qr?text=" . urlencode($otpAuthUrl) . "&size=300";
        $qrUrl3 = "https://chart.googleapis.com/chart?chs=300x300&cht=qr&chl=" . urlencode($otpAuthUrl);
        ?>

        <div class="bg-white/10 backdrop-blur rounded-xl p-6 mb-6">
            <h2 class="text-2xl font-bold mb-4">📱 QR Code for Setup</h2>
            <p class="text-blue-300 text-sm mb-4">Scan this QR code with your authenticator app to set up 2FA</p>

            <div class="flex flex-col items-center gap-4">
                <!-- QR Code Display with Error Handling -->
                <div class="bg-white p-6 rounded-xl relative" id="qrCodeContainer">
                    <img
                        src="<?= $qrUrl1 ?>"
                        alt="2FA QR Code"
                        class="w-72 h-72"
                        id="qrCodeImage"
                        onerror="handleQRError()"
                        onload="handleQRSuccess()">

                    <!-- Loading Indicator -->
                    <div id="qrLoading" class="absolute inset-0 flex items-center justify-center bg-white rounded-xl">
                        <div class="text-center">
                            <i class="fas fa-spinner fa-spin text-blue-600 text-4xl mb-2"></i>
                            <p class="text-gray-600 text-sm">Generating QR Code...</p>
                        </div>
                    </div>

                    <!-- Error Message -->
                    <div id="qrError" class="absolute inset-0 hidden flex-col items-center justify-center bg-red-50 p-4 rounded-xl">
                        <i class="fas fa-exclamation-triangle text-red-600 text-4xl mb-3"></i>
                        <p class="text-red-600 font-bold mb-2">QR Code Failed to Load</p>
                        <p class="text-red-500 text-sm text-center mb-4">Use manual entry below instead</p>
                        <button onclick="retryQR()" class="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm font-bold transition">
                            <i class="fas fa-redo mr-2"></i>Retry
                        </button>
                    </div>
                </div>

                <!-- Setup Instructions -->
                <div class="w-full bg-blue-600/20 border border-blue-500/50 rounded-lg p-4">
                    <p class="text-blue-200 font-semibold mb-2">📱 How to Scan:</p>
                    <ol class="text-blue-300 text-sm space-y-1 ml-6 list-decimal">
                        <li>Open your authenticator app (Google Authenticator, Microsoft Authenticator, etc.)</li>
                        <li>Tap the "+" or "Add" button</li>
                        <li>Choose "Scan QR code"</li>
                        <li>Point camera at the QR code above</li>
                        <li>Verify the account appears as "AdSphere Admin: admin"</li>
                    </ol>
                </div>

                <!-- Alternative QR URLs -->
                <details class="w-full">
                    <summary class="text-xs text-sky-400 cursor-pointer hover:text-sky-300 text-center">
                        🔧 Alternative QR code URLs (if not loading)
                    </summary>
                    <div class="mt-3 space-y-2 text-xs">
                        <div class="bg-blue-900/40 p-2 rounded border border-cyan-500/30">
                            <a href="<?= $qrUrl1 ?>" target="_blank" class="text-cyan-400 hover:text-cyan-300 break-all">
                                🔗 QR Server API
                            </a>
                        </div>
                        <div class="bg-blue-900/40 p-2 rounded border border-cyan-500/30">
                            <a href="<?= $qrUrl2 ?>" target="_blank" class="text-cyan-400 hover:text-cyan-300 break-all">
                                🔗 QuickChart API
                            </a>
                        </div>
                        <div class="bg-blue-900/40 p-2 rounded border border-cyan-500/30">
                            <a href="<?= $qrUrl3 ?>" target="_blank" class="text-cyan-400 hover:text-cyan-300 break-all">
                                🔗 Google Chart API (Legacy)
                            </a>
                        </div>
                    </div>
                </details>
            </div>
        </div>

        <!-- Manual Secret Key -->
        <div class="bg-white/10 backdrop-blur rounded-xl p-6 mb-6">
            <h2 class="text-2xl font-bold mb-3">🔑 Manual Entry Key</h2>
            <p class="text-blue-300 text-sm mb-4">Can't scan? Enter this secret key manually in your authenticator app:</p>

            <div class="bg-black/30 p-4 rounded-lg border border-blue-500/30">
                <div class="flex items-center justify-between gap-4">
                    <div class="flex-1">
                        <p class="text-xs text-blue-400 mb-1">Secret Key:</p>
                        <p class="font-mono text-cyan-300 text-lg break-all" id="secretKey"><?= $secret ?></p>
                    </div>
                    <button
                        onclick="copySecretKey()"
                        id="copyBtn"
                        class="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg text-white font-bold transition-all flex items-center gap-2 whitespace-nowrap">
                        <i class="fas fa-copy"></i>
                        <span>Copy</span>
                    </button>
                </div>
            </div>

            <div class="mt-3 bg-blue-600/20 border border-blue-500/50 rounded-lg p-3">
                <p class="text-blue-200 text-xs font-semibold mb-1">📝 Manual Setup Instructions:</p>
                <ol class="text-blue-300 text-xs space-y-1 ml-4 list-decimal">
                    <li>Open your authenticator app</li>
                    <li>Tap "+" or "Add" button</li>
                    <li>Choose "Enter a setup key" or "Manual entry"</li>
                    <li>Account name: <span class="font-mono text-cyan-300">AdSphere Admin</span></li>
                    <li>Key: Copy the secret above</li>
                    <li>Type: Time-based</li>
                    <li>Tap "Add" or "Save"</li>
                </ol>
            </div>
        </div>

        <!-- Test Form -->
        <div class="bg-white/10 backdrop-blur rounded-xl p-6 mt-6">
            <h2 class="text-2xl font-bold mb-4">🧪Verification Here</h2>
            <form method="POST" class="space-y-4">
                <div>
                    <label class="block mb-2">Enter a code to test:</label>
                    <input
                        type="text"
                        name="test_code"
                        maxlength="6"
                        pattern="[0-9]{6}"
                        class="w-full px-4 py-3 bg-black/30 border border-blue-500/30 rounded-lg text-white text-2xl text-center font-mono"
                        placeholder="000000"
                        autofocus>
                </div>
                <button type="submit" class="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-bold transition">
                    <i class="fas fa-check mr-2"></i>Proceed setup
                </button>
            </form>

            <?php
            if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['test_code'])) {
                $testCode = trim($_POST['test_code']);
                $isValid = verifyTOTP($secret, $testCode, true);

                if ($isValid) {
                    echo '<div class="mt-4 p-4 bg-green-600/30 border border-green-500 rounded-lg">';
                    echo '<p class="text-green-300 font-bold"><i class="fas fa-check-circle mr-2"></i>SUCCESS! Code is VALID ✅</p>';
                    echo '<p class="text-green-200 text-sm mt-1">This code would be accepted for login</p>';
                    echo '</div>';
                } else {
                    echo '<div class="mt-4 p-4 bg-red-600/30 border border-red-500 rounded-lg">';
                    echo '<p class="text-red-300 font-bold"><i class="fas fa-times-circle mr-2"></i>FAILED! Code is INVALID ❌</p>';
                    echo '<p class="text-red-200 text-sm mt-1">Expected: ' . $currentCode . ' | You entered: ' . htmlspecialchars($testCode) . '</p>';
                    echo '</div>';
                }
            }
            ?>
        </div>

        <?php endif; ?>

    </div>

    <script>
        // Copy backup codes function
        function copyBackupCodes() {
            const codes = <?= json_encode($backupCodes) ?>;
            const codesText = codes.join('\n');
            const copyBtn = document.getElementById('copyBackupBtn');
            const originalHTML = copyBtn.innerHTML;

            navigator.clipboard.writeText(codesText).then(() => {
                copyBtn.innerHTML = '<i class="fas fa-check mr-2"></i>Copied!';
                copyBtn.classList.remove('bg-blue-600', 'hover:bg-blue-700');
                copyBtn.classList.add('bg-green-600', 'hover:bg-green-700');

                setTimeout(() => {
                    copyBtn.innerHTML = originalHTML;
                    copyBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
                    copyBtn.classList.add('bg-blue-600', 'hover:bg-blue-700');
                }, 2000);
            }).catch(err => {
                console.error('Failed to copy:', err);
                alert('Failed to copy. Please select and copy manually.');
            });
        }

        // Countdown and redirect for success page
        <?php if ($successMsg): ?>
        let countdown = 10;
        const countdownElem = document.getElementById('countdown');

        setInterval(() => {
            countdown--;
            if (countdownElem) {
                countdownElem.textContent = countdown;
            }
            if (countdown <= 0) {
                window.location.href = '../admin_dashboard.php';
            }
        }, 1000);
        <?php endif; ?>

        // QR Code URLs (fallback order)
        const qrUrls = [
            '<?= $qrUrl1 ?>',
            '<?= $qrUrl2 ?>',
            '<?= $qrUrl3 ?>'
        ];
        let currentQRIndex = 0;

        function handleQRSuccess() {
            console.log('✅ QR Code loaded successfully from:', qrUrls[currentQRIndex]);
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

        function copySecretKey() {
            const secret = '<?= $secret ?>';
            const copyBtn = document.getElementById('copyBtn');
            const originalHTML = copyBtn.innerHTML;

            navigator.clipboard.writeText(secret).then(() => {
                // Success feedback
                copyBtn.innerHTML = '<i class="fas fa-check"></i><span>Copied!</span>';
                copyBtn.classList.remove('bg-cyan-600', 'hover:bg-cyan-700');
                copyBtn.classList.add('bg-green-600', 'hover:bg-green-700');

                // Reset after 2 seconds
                setTimeout(() => {
                    copyBtn.innerHTML = originalHTML;
                    copyBtn.classList.remove('bg-green-600', 'hover:bg-green-700');
                    copyBtn.classList.add('bg-cyan-600', 'hover:bg-cyan-700');
                }, 2000);

                console.log('✅ Secret copied to clipboard');
            }).catch(err => {
                // Error feedback
                console.error('❌ Failed to copy:', err);
                copyBtn.innerHTML = '<i class="fas fa-times"></i><span>Failed</span>';
                copyBtn.classList.remove('bg-cyan-600', 'hover:bg-cyan-700');
                copyBtn.classList.add('bg-red-600', 'hover:bg-red-700');

                // Reset after 2 seconds
                setTimeout(() => {
                    copyBtn.innerHTML = originalHTML;
                    copyBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
                    copyBtn.classList.add('bg-cyan-600', 'hover:bg-cyan-700');
                }, 2000);
            });
        }

        // Console debugging
        console.log('=== 2FA Test Page Debug ===');
        console.log('Secret:', '<?= $secret ?>');
        console.log('Secret Length:', <?= strlen($secret) ?>);
        console.log('Current Code:', '<?= $currentCode ?>');
        console.log('OTP Auth URL:', '<?= $otpAuthUrl ?>');
        console.log('QR Code URLs:', qrUrls);

        // Background refresh functionality
        let refreshInterval;

        function updateTimeInfo() {
            const now = new Date();
            const seconds = Math.floor(now.getTime() / 1000);
            const timeSlice = Math.floor(seconds / 30);
            const secondsUntilNext = 30 - (seconds % 30);

            // Update seconds until next code
            const secondsElem = document.querySelector('.pulse');
            if (secondsElem) {
                secondsElem.textContent = secondsUntilNext + 's';
            }

            // Update Unix timestamp
            const timestampElems = document.querySelectorAll('.text-2xl.font-mono');
            if (timestampElems[1]) {
                timestampElems[1].textContent = seconds;
            }

            // Update TimeSlice
            if (timestampElems[2]) {
                timestampElems[2].textContent = timeSlice;
            }

            // Update current time (fetch from server every 10 seconds for accuracy)
            if (seconds % 10 === 0) {
                updateServerTime();
            }
        }

        function updateServerTime() {
            // Add subtle visual feedback
            const timeInfo = document.querySelector('.bg-white\\/10.backdrop-blur.rounded-xl');
            if (timeInfo) {
                timeInfo.classList.add('updating');
            }

            // Fetch current server time without full page reload
            fetch(window.location.href, {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.text())
            .then(html => {
                // Parse the response to extract server time
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                const newTime = doc.querySelector('.text-2xl.font-mono');

                if (newTime) {
                    const currentTimeElem = document.querySelector('.text-2xl.font-mono');
                    if (currentTimeElem) {
                        currentTimeElem.textContent = newTime.textContent;
                    }
                }

                // Remove visual feedback
                if (timeInfo) {
                    timeInfo.classList.remove('updating');
                }

                console.log('🔄 Time info updated from server');
            })
            .catch(err => {
                console.error('❌ Failed to update time info:', err);
                if (timeInfo) {
                    timeInfo.classList.remove('updating');
                }
            });
        }

        // Update every second
        setInterval(updateTimeInfo, 1000);

        // Initial update
        updateTimeInfo();

        // Add visual indicator that auto-refresh is active
        window.addEventListener('DOMContentLoaded', () => {
            const header = document.querySelector('h1');
            if (header) {
                const indicator = document.createElement('span');
                indicator.className = 'text-sm text-green-400 ml-3';
                indicator.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Live';
                header.appendChild(indicator);
            }
        });
    </script>

</body>
</html>

