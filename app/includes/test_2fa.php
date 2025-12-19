<?php
/********************************************
 * 2FA Debug Test Page
 * Test TOTP generation with your secret
 ********************************************/

// Your secret from the console
$secret = 'XT4FJ5J7RH4R6Q5NJVJ7TCFUTKW62XR7';

// Include TOTP functions
require_once __DIR__ . '/twoauth.php';

$currentTimeSlice = floor(time() / 30);
$currentCode = generateTOTP($secret, $currentTimeSlice);

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
    </style>
    <meta http-equiv="refresh" content="10">
</head>
<body class="bg-gradient-to-br from-blue-900 to-indigo-900 min-h-screen p-8 text-white">

    <div class="max-w-4xl mx-auto">

        <div class="text-center mb-8">
            <h1 class="text-4xl font-bold mb-2">🔐 2FA Test Page</h1>
            <p class="text-blue-300">This page auto-refreshes every 10 seconds</p>
        </div>

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

        <!-- Current Expected Code (BIG) -->
        <div class="bg-gradient-to-br from-green-600 to-emerald-700 rounded-2xl p-8 mb-6 text-center shadow-2xl">
            <p class="text-green-200 text-lg mb-2">
                <i class="fas fa-check-circle mr-2"></i>
                CURRENT EXPECTED CODE
            </p>
            <p class="text-6xl font-mono font-bold tracking-wider mb-4"><?= $currentCode ?></p>
            <p class="text-green-200 text-sm">
                ✅ This is what your authenticator app should show RIGHT NOW
            </p>
            <p class="text-green-300 text-xs mt-2">
                Refreshes automatically every 30 seconds
            </p>
        </div>

        <!-- All Time Windows -->
        <div class="bg-white/10 backdrop-blur rounded-xl p-6 mb-6">
            <h2 class="text-2xl font-bold mb-4">📊 All Valid Time Windows (±3 / 90 seconds)</h2>
            <p class="text-blue-300 text-sm mb-4">Any of these 7 codes will be accepted (optimized for Google Authenticator)</p>

            <div class="space-y-3">
                <?php foreach($codes as $codeInfo): ?>
                    <div class="flex items-center justify-between p-4 rounded-lg <?= $codeInfo['offset'] === 0 ? 'bg-green-600/30 border-2 border-green-500' : 'bg-white/5' ?>">
                        <div>
                            <p class="font-semibold <?= $codeInfo['offset'] === 0 ? 'text-green-300' : '' ?>">
                                <?= $codeInfo['label'] ?>
                            </p>
                            <p class="text-xs text-blue-300">TimeSlice: <?= $codeInfo['timeSlice'] ?></p>
                        </div>
                        <div class="text-3xl font-mono font-bold <?= $codeInfo['offset'] === 0 ? 'text-green-300' : '' ?>">
                            <?= $codeInfo['code'] ?>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>
        </div>

        <!-- Your Secret -->
        <div class="bg-white/10 backdrop-blur rounded-xl p-6 mb-6">
            <h2 class="text-2xl font-bold mb-4">🔑 Your Secret Key</h2>
            <div class="bg-black/30 p-4 rounded-lg font-mono break-all text-lg">
                <?= $secret ?>
            </div>
            <div class="mt-3 flex gap-2">
                <button onclick="copySecret()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition">
                    <i class="fas fa-copy mr-2"></i>Copy Secret
                </button>
                <button onclick="validateSecret()" class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition">
                    <i class="fas fa-check mr-2"></i>Validate Secret
                </button>
            </div>

            <!-- Base32 Validation -->
            <?php
            $decodedSecret = base32_decode($secret);
            $isValidBase32 = $decodedSecret !== false && !empty($decodedSecret);
            ?>
            <div class="mt-4 p-3 rounded-lg <?= $isValidBase32 ? 'bg-green-600/20 border border-green-500' : 'bg-red-600/20 border border-red-500' ?>">
                <p class="font-bold <?= $isValidBase32 ? 'text-green-300' : 'text-red-300' ?>">
                    <?= $isValidBase32 ? '✅' : '❌' ?> Base32 Decoding: <?= $isValidBase32 ? 'VALID' : 'FAILED' ?>
                </p>
                <?php if ($isValidBase32): ?>
                    <p class="text-green-200 text-sm mt-1">
                        Secret decoded successfully (<?= strlen($decodedSecret) ?> bytes)
                    </p>
                    <p class="text-green-200 text-xs mt-1 font-mono">
                        Hex: <?= bin2hex($decodedSecret) ?>
                    </p>
                <?php else: ?>
                    <p class="text-red-200 text-sm mt-1">
                        ⚠️ Secret could not be decoded! This will cause verification to fail.
                    </p>
                <?php endif; ?>
            </div>
        </div>

        <!-- Google Authenticator Time Sync Warning -->
        <div class="bg-red-600/20 border-2 border-red-500/50 rounded-xl p-6 mb-6">
            <h2 class="text-2xl font-bold mb-4 text-red-300">
                <i class="fas fa-exclamation-triangle mr-2"></i>
                GOOGLE AUTHENTICATOR USERS: Sync Time First!
            </h2>
            <p class="text-red-200 mb-3">
                Google Authenticator is very strict with time synchronization. If codes don't match, sync time:
            </p>
            <div class="bg-black/30 p-4 rounded-lg space-y-3">
                <div>
                    <p class="font-bold text-red-200 mb-1">📱 In Google Authenticator:</p>
                    <ol class="text-sm text-red-100 space-y-1 ml-6 list-decimal">
                        <li>Tap the 3-dot menu (⋮) in top-right corner</li>
                        <li>Tap "Settings"</li>
                        <li>Tap "Time correction for codes"</li>
                        <li>Tap "Sync now"</li>
                        <li>Return to app and check if code matches</li>
                    </ol>
                </div>
                <div>
                    <p class="font-bold text-red-200 mb-1">⏰ Also ensure automatic time is enabled:</p>
                    <ul class="text-sm text-red-100 space-y-1 ml-6 list-disc">
                        <li><strong>iOS:</strong> Settings → General → Date & Time → Set Automatically ✅</li>
                        <li><strong>Android:</strong> Settings → System → Date & Time → Use network-provided time ✅</li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- Instructions -->
        <div class="bg-yellow-600/20 border border-yellow-500/50 rounded-xl p-6">
            <h2 class="text-2xl font-bold mb-4">📱 How to Test</h2>
            <ol class="space-y-2">
                <li class="flex gap-3">
                    <span class="font-bold">1.</span>
                    <span><strong>Google Authenticator users:</strong> SYNC TIME FIRST (see red box above) ⬆️</span>
                </li>
                <li class="flex gap-3">
                    <span class="font-bold">2.</span>
                    <span>Look at your authenticator app for "AdSphere Admin: admin"</span>
                </li>
                <li class="flex gap-3">
                    <span class="font-bold">3.</span>
                    <span>Compare the code in your app with the BIG GREEN CODE above</span>
                </li>
                <li class="flex gap-3">
                    <span class="font-bold">4.</span>
                    <span>If they MATCH ✅ → Enter that code in the setup page</span>
                </li>
                <li class="flex gap-3">
                    <span class="font-bold">5.</span>
                    <span>If they DON'T MATCH ❌ → Check if your code matches ANY of the 7 codes above</span>
                </li>
                <li class="flex gap-3">
                    <span class="font-bold">6.</span>
                    <span>Still no match? → Delete from app, sync time, and re-scan QR code</span>
                </li>
            </ol>
        </div>

        <!-- Test Form -->
        <div class="bg-white/10 backdrop-blur rounded-xl p-6 mt-6">
            <h2 class="text-2xl font-bold mb-4">🧪 Test Verification Here</h2>
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
                    <i class="fas fa-check mr-2"></i>Test This Code
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

    </div>

    <script>
        function copySecret() {
            const secret = '<?= $secret ?>';
            navigator.clipboard.writeText(secret).then(() => {
                alert('✅ Secret copied to clipboard!\n\nYou can paste this into Google Authenticator manually:\n\n' + secret);
            });
        }

        function validateSecret() {
            const secret = '<?= $secret ?>';

            // Check length
            const lengthOk = secret.length >= 16 && secret.length <= 32;

            // Check valid Base32 characters (A-Z, 2-7)
            const validChars = /^[A-Z2-7]+$/;
            const charsOk = validChars.test(secret);

            let message = '🔍 Secret Validation:\n\n';
            message += 'Length: ' + secret.length + ' characters ' + (lengthOk ? '✅' : '❌') + '\n';
            message += 'Valid Base32: ' + (charsOk ? '✅' : '❌') + '\n';
            message += '\nSecret: ' + secret + '\n';

            if (!charsOk) {
                message += '\n⚠️ Invalid characters detected! Should only contain:\n';
                message += 'A-Z and 2-7\n';
            }

            if (lengthOk && charsOk) {
                message += '\n✅ Secret is VALID!';
            } else {
                message += '\n❌ Secret has issues!';
            }

            alert(message);
        }

        // Countdown timer
        function updateCountdown() {
            const seconds = 30 - (Math.floor(Date.now() / 1000) % 30);
            // Page auto-refreshes, so just show countdown
        }
        setInterval(updateCountdown, 1000);

        // Console debugging
        console.log('=== 2FA Test Page Debug ===');
        console.log('Secret:', '<?= $secret ?>');
        console.log('Secret Length:', <?= strlen($secret) ?>);
        console.log('Current Code:', '<?= $currentCode ?>');
        console.log('Base32 Valid:', <?= $isValidBase32 ? 'true' : 'false' ?>);
    </script>

</body>
</html>

