<?php
/****************************************************
 * twofactor.php
 * Standalone TOTP 2FA implementation (Google Auth)
 *
 * NOTE: This file is included by other files that already
 * manage sessions. Do not call session_start() here.
 ****************************************************/

// Session is already started by the parent file (setup_2fa.php, verify_2fa.php, etc.)
// No session_start() needed here

// This file provides reusable TOTP functions:
// - generateSecret()
// - verifyTOTP()
// - generateTOTP()
// - base32_decode()

/****************************************************
 * GENERATE A 32-character Base32 secret
 ****************************************************/
function generateSecret($length = 32) {
    $chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
    $secret = '';
    for ($i = 0; $i < $length; $i++) {
        $secret .= $chars[random_int(0, strlen($chars) - 1)];
    }
    return $secret;
}

/****************************************************
 * VERIFY TOTP CODE
 * Allows ±3 time windows (90 seconds drift tolerance)
 * Optimized for Google Authenticator compatibility
 ****************************************************/
function verifyTOTP($secret, $code) {

    // Remove any spaces from code
    $code = str_replace(' ', '', trim($code));

    // Validate code format (6 digits only)
    if (!preg_match('/^[0-9]{6}$/', $code)) {
        return false;
    }

    $timeSlice = floor(time() / 30);

    // Allow ±3 time drift (90 seconds tolerance)
    // Google Authenticator can be strict with time sync
    for ($i = -3; $i <= 3; $i++) {
        $calculatedCode = generateTOTP($secret, $timeSlice + $i);

        // Use timing-safe comparison
        if (hash_equals($calculatedCode, $code)) {
            return true;
        }
    }


    return false;
}

function generateTOTP($secret, $timeSlice) {

    $secretKey = base32_decode($secret);
    $time = pack("N*", 0) . pack("N*", $timeSlice);

    $hash = hash_hmac("sha1", $time, $secretKey, true);

    $offset = ord(substr($hash, -1)) & 0xF;
    $code = unpack("N", substr($hash, $offset, 4))[1] & 0x7fffffff;

    return str_pad($code % 1000000, 6, "0", STR_PAD_LEFT);
}

/****************************************************
 * BASE32 decode (RFC 4648 compliant)
 * Compatible with Google Authenticator
 ****************************************************/
function base32_decode($secret) {
    if (empty($secret)) {
        return '';
    }

    // Remove spaces and convert to uppercase
    $secret = strtoupper(str_replace(' ', '', $secret));

    $base32chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
    $base32charsFlipped = array_flip(str_split($base32chars));

    // Remove padding
    $secret = rtrim($secret, '=');

    $binaryString = '';

    // Convert each character to 5-bit binary
    foreach (str_split($secret) as $char) {
        if (!isset($base32charsFlipped[$char])) {
            return false;
        }
        $binaryString .= str_pad(decbin($base32charsFlipped[$char]), 5, '0', STR_PAD_LEFT);
    }

    // Split into 8-bit chunks and convert to characters
    $decoded = '';
    $chunks = str_split($binaryString, 8);

    foreach ($chunks as $chunk) {
        // Only process complete 8-bit chunks
        if (strlen($chunk) == 8) {
            $decoded .= chr(bindec($chunk));
        }
    }

    if (empty($decoded)) {
        return false;
    }

    return $decoded;
}

/****************************************************
 * END OF TOTP LIBRARY FUNCTIONS
 *
 * This file only provides reusable functions.
 * The UI and session management is handled by:
 * - setup_2fa.php (for initial setup)
 * - verify_2fa.php (for login verification)
 ****************************************************/
