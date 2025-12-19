<?php
/********************************************
 * TOTP Diagnostic Tool
 * Check if TOTP generation is working correctly
 ********************************************/

// Test secret (use a known one for testing)
$testSecret = 'JBSWY3DPEHPK3PXP'; // "Hello!" in Base32

require_once __DIR__ . '/twoauth.php';

echo "<pre style='background: #1a1a2e; color: #00ff00; padding: 20px; font-family: monospace;'>";
echo "=== TOTP DIAGNOSTIC TOOL ===\n\n";

// Test 1: Base32 Decoding
echo "TEST 1: Base32 Decoding\n";
echo "------------------------\n";
echo "Test Secret: $testSecret\n";
$decoded = base32_decode($testSecret);
echo "Decoded: " . ($decoded !== false ? "SUCCESS" : "FAILED") . "\n";
if ($decoded !== false) {
    echo "Decoded Length: " . strlen($decoded) . " bytes\n";
    echo "Decoded Hex: " . bin2hex($decoded) . "\n";
    echo "Expected Hex: 48656c6c6f21 (for 'Hello!')\n";
}
echo "\n";

// Test 2: TOTP Generation with Known Secret
echo "TEST 2: TOTP Generation\n";
echo "------------------------\n";
$timeSlice = floor(time() / 30);
echo "Current Unix Time: " . time() . "\n";
echo "Current TimeSlice: $timeSlice\n";
$code = generateTOTP($testSecret, $timeSlice);
echo "Generated Code: $code\n";
echo "Code Length: " . strlen($code) . " (should be 6)\n";
echo "Code Format: " . (preg_match('/^[0-9]{6}$/', $code) ? "VALID" : "INVALID") . "\n";
echo "\n";

// Test 3: Verification Test
echo "TEST 3: Verification\n";
echo "------------------------\n";
$isValid = verifyTOTP($testSecret, $code, true);
echo "Self-Verification: " . ($isValid ? "PASSED ✅" : "FAILED ❌") . "\n";
echo "\n";

// Test 4: Time Window Test
echo "TEST 4: Time Windows (±3)\n";
echo "------------------------\n";
for ($i = -3; $i <= 3; $i++) {
    $offset = $i * 30;
    $offsetLabel = $i === 0 ? 'NOW' : sprintf('%+ds', $offset);
    $windowCode = generateTOTP($testSecret, $timeSlice + $i);
    echo sprintf("%-10s : %s\n", $offsetLabel, $windowCode);
}
echo "\n";

// Test 5: Your Actual Secret (from session/config)
echo "TEST 5: Your Actual Secret\n";
echo "------------------------\n";

// Try to load from admins.json
$adminsFile = __DIR__ . "/../../config/admins.json";
if (file_exists($adminsFile)) {
    $admins = json_decode(file_get_contents($adminsFile), true);

    foreach ($admins as $username => $admin) {
        if (isset($admin['2fa_secret']) && !empty($admin['2fa_secret'])) {
            $userSecret = $admin['2fa_secret'];
            echo "Username: $username\n";
            echo "Secret: $userSecret\n";
            echo "Secret Length: " . strlen($userSecret) . " chars\n";

            $userDecoded = base32_decode($userSecret);
            echo "Base32 Decode: " . ($userDecoded !== false ? "SUCCESS" : "FAILED ❌") . "\n";

            if ($userDecoded !== false) {
                echo "Decoded Length: " . strlen($userDecoded) . " bytes\n";
                $userCode = generateTOTP($userSecret, $timeSlice);
                echo "Current Code: $userCode\n";

                echo "\nAll Valid Codes (±3):\n";
                for ($i = -3; $i <= 3; $i++) {
                    $offset = $i * 30;
                    $offsetLabel = $i === 0 ? 'NOW' : sprintf('%+ds', $offset);
                    $windowCode = generateTOTP($userSecret, $timeSlice + $i);
                    $highlight = $i === 0 ? ' ← CURRENT' : '';
                    echo sprintf("  %-10s : %s%s\n", $offsetLabel, $windowCode, $highlight);
                }
            }
            echo "\n";
        }
    }
} else {
    echo "❌ admins.json not found\n";
}

// Test 6: Character Set Validation
echo "TEST 6: Character Set Validation\n";
echo "------------------------\n";
$validChars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
echo "Valid Base32 Characters: $validChars\n";
echo "Testing your secret(s)...\n";

if (file_exists($adminsFile)) {
    $admins = json_decode(file_get_contents($adminsFile), true);
    foreach ($admins as $username => $admin) {
        if (isset($admin['2fa_secret'])) {
            $secret = $admin['2fa_secret'];
            $invalidChars = [];
            foreach (str_split($secret) as $char) {
                if (strpos($validChars, $char) === false) {
                    $invalidChars[] = $char;
                }
            }

            if (empty($invalidChars)) {
                echo "  $username: ✅ All characters valid\n";
            } else {
                echo "  $username: ❌ Invalid characters found: " . implode(', ', array_unique($invalidChars)) . "\n";
            }
        }
    }
}
echo "\n";

// Test 7: Server Time Check
echo "TEST 7: Server Time\n";
echo "------------------------\n";
echo "Server Date/Time: " . date('Y-m-d H:i:s') . "\n";
echo "Server Timezone: " . date_default_timezone_get() . "\n";
echo "Unix Timestamp: " . time() . "\n";
echo "TimeSlice (time/30): " . floor(time() / 30) . "\n";
echo "\n";

echo "=== DIAGNOSTIC COMPLETE ===\n";
echo "\nIf all tests pass but codes still don't match:\n";
echo "1. Check if your phone time is synced\n";
echo "2. Verify you're using the correct secret\n";
echo "3. Try deleting and re-scanning the QR code\n";
echo "4. Check server logs for errors\n";

echo "</pre>";
?>

