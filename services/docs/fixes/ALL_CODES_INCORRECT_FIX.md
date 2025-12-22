# 🔍 ALL CODES INCORRECT - DIAGNOSTIC SOLUTION

## 🚨 CRITICAL ISSUE

You reported: **"All codes shown in setup_2fa are incorrect even in other authenticator apps"**

This means there's likely a fundamental issue with:
1. TOTP generation algorithm
2. Base32 decoding
3. Secret key corruption
4. Server time misconfiguration

---

## ✅ IMMEDIATE ACTION - RUN DIAGNOSTIC

I've created a comprehensive diagnostic tool to identify the exact problem.

### **Step 1: Run the Diagnostic**

**URL:**
```
http://localhost/app/admin/handlers/diagnostic.php
```

This will show:
- ✅ Base32 decoding test
- ✅ TOTP generation test
- ✅ Self-verification test
- ✅ Time window codes
- ✅ Your actual secret validation
- ✅ Character set validation
- ✅ Server time check

### **Step 2: Read the Output**

The diagnostic will tell you EXACTLY what's wrong:

**Example outputs:**

#### **✅ If Everything Works:**
```
TEST 1: Base32 Decoding
Decoded: SUCCESS
Decoded Length: 6 bytes

TEST 2: TOTP Generation
Generated Code: 123456
Code Format: VALID

TEST 3: Verification
Self-Verification: PASSED ✅

TEST 5: Your Actual Secret
Username: admin
Secret: XT4FJ5J7RH4R6Q5NJVJ7TCFUTKW62XR7
Base32 Decode: SUCCESS
Current Code: 789012

All Valid Codes (±3):
  -90s      : 123456
  -60s      : 234567
  -30s      : 345678
  NOW       : 789012 ← CURRENT
  +30s      : 890123
  +60s      : 901234
  +90s      : 012345
```

#### **❌ If Base32 Fails:**
```
TEST 1: Base32 Decoding
Decoded: FAILED

TEST 5: Your Actual Secret
Base32 Decode: FAILED ❌
```
**Solution:** Secret is corrupted, need to generate new one

#### **❌ If Invalid Characters:**
```
TEST 6: Character Set Validation
admin: ❌ Invalid characters found: 0, 1, 8, 9
```
**Solution:** Secret contains invalid Base32 characters (0, 1, 8, 9 are not valid)

---

## 🔧 FIXES I IMPLEMENTED

### **1. Updated verify_2fa.php**

**Added:**
- ✅ Debug mode (`?debug=1`) shows all 7 valid codes
- ✅ Enhanced error messages show expected vs actual
- ✅ Google Authenticator sync reminder
- ✅ Link to test page
- ✅ Better logging with actual vs expected codes

**Usage:**
```
/app/admin/handlers/verify_2fa.php?debug=1
```

### **2. Created diagnostic.php**

**Tests:**
- Base32 decoding functionality
- TOTP generation algorithm
- Time window calculations
- Your actual secrets from admins.json
- Character set validation
- Server time configuration

---

## 🎯 COMMON CAUSES & SOLUTIONS

### **Issue 1: Corrupted Secret**

**Symptoms:**
- All codes fail
- Works in test but not in real apps
- Base32 decode fails in diagnostic

**Solution:**
1. Go to setup page with `?action=generate`
2. This generates a FRESH secret
3. Delete old account from authenticator apps
4. Scan new QR code
5. Test immediately

**URL:**
```
/app/admin/handlers/setup_2fa.php?mandatory=1&action=generate
```

### **Issue 2: Wrong Secret in Authenticator**

**Symptoms:**
- Codes don't match any of the 7 valid codes
- Different secret scanned than server has

**Solution:**
1. Check diagnostic output for your secret
2. In authenticator app, edit account
3. Compare secrets - should match exactly
4. If different, delete and re-scan

### **Issue 3: Invalid Base32 Characters**

**Symptoms:**
- Secret contains 0, 1, 8, or 9
- Diagnostic shows "Invalid characters found"

**Cause:** Secret generator used wrong character set

**Solution:**
1. Edit `/app/admin/handlers/twoauth.php`
2. Verify `generateSecret()` function uses:
   ```php
   $chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
   ```
3. NOT 0-9, A-Z (that's Base36, not Base32)
4. Generate new secret

### **Issue 4: Server Time Wrong**

**Symptoms:**
- Codes match occasionally
- Off by 30-60 seconds consistently

**Solution:**
```bash
# Check server time
date

# Sync with NTP (if available)
sudo ntpdate pool.ntp.org

# Or set timezone
sudo timedatectl set-timezone America/New_York
```

### **Issue 5: Session Secret vs Saved Secret Mismatch**

**Symptoms:**
- Works once then fails
- Different codes each time you refresh

**Cause:** Secret in `$_SESSION['temp_2fa_secret']` differs from `admins.json`

**Solution:**
1. Clear sessions: Delete `/tmp/sess_*` files
2. Or logout and start fresh
3. Ensure `$_SESSION['temp_2fa_secret']` is cleared after successful setup

---

## 🧪 TESTING PROCEDURE

### **Step 1: Run Diagnostic**
```
/app/admin/handlers/diagnostic.php
```

**Look for:**
- ✅ All tests PASS
- ✅ Base32 decode SUCCESS
- ✅ Valid codes generated
- ❌ Any FAILED tests

### **Step 2: Check Your Secret**

In diagnostic output, find:
```
TEST 5: Your Actual Secret
Username: admin
Secret: [YOUR_SECRET_HERE]
Current Code: 123456
```

**Write down the secret and current code**

### **Step 3: Compare with Authenticator**

1. Open your authenticator app
2. Find "AdSphere Admin: admin"
3. Tap to see details (if possible)
4. Check if secret matches diagnostic output
5. Compare current code with diagnostic

**Should match exactly!**

### **Step 4: Test on Test Page**
```
/app/admin/handlers/test_2fa.php
```

**Verify:**
- Current code matches diagnostic
- Your authenticator shows same code
- If matches → Secret is correct
- If doesn't → Secret is wrong in app

### **Step 5: Try Setup with Debug**
```
/app/admin/handlers/setup_2fa.php?mandatory=1&debug=1
```

**You'll see:**
- Current expected code (BIG)
- All 7 valid codes
- Your authenticator should match one of them

---

## 🔍 DEBUG MODE URLS

**Verify 2FA (Login verification):**
```
/app/admin/handlers/verify_2fa.php?debug=1
```
Shows all 7 valid codes during login

**Setup 2FA (Initial setup):**
```
/app/admin/handlers/setup_2fa.php?mandatory=1&debug=1
```
Shows all 7 valid codes during setup

**Test Page (Standalone testing):**
```
/app/admin/handlers/test_2fa.php
```
Shows codes with your specific secret

**Diagnostic (System check):**
```
/app/admin/handlers/diagnostic.php
```
Complete system diagnostic

---

## 📊 WHAT TO CHECK IN EACH PAGE

### **diagnostic.php - Look For:**
```
✅ Base32 Decode: SUCCESS
✅ Code Format: VALID
✅ Self-Verification: PASSED ✅
✅ All characters valid
```

### **test_2fa.php - Look For:**
```
✅ Base32 Decoding: VALID
✅ Secret decoded successfully (20 bytes)
✅ Code matches your authenticator
```

### **setup_2fa.php?debug=1 - Look For:**
```
🐛 Debug Mode shows:
  CURRENT CODE: 123456
  
  All 7 valid codes:
  -3×30s    456789
  ...
  NOW       123456  ← highlighted
  ...
```

### **verify_2fa.php?debug=1 - Look For:**
```
🐛 Debug Mode shows:
  CURRENT CODE: 123456
  
  (Same as above)
```

---

## 🚨 EMERGENCY RESET

If nothing works:

### **Option 1: Generate New Secret**

```php
// Go to this URL to force new secret generation:
/app/admin/handlers/setup_2fa.php?mandatory=1&action=generate
```

### **Option 2: Manually Edit admins.json**

1. Edit `/app/config/admins.json`
2. Set `2fa_enabled` to `false`
3. Set `2fa_secret` to `null`
4. Login without 2FA
5. Setup fresh from dashboard

### **Option 3: Disable 2FA Temporarily**

Edit `/app/admin/login.php`:
```php
// Line ~25, change:
'enable_2fa' => true,

// To:
'enable_2fa' => false,
```

---

## 📝 NEXT STEPS

1. **FIRST:** Run diagnostic.php
   ```
   /app/admin/handlers/diagnostic.php
   ```

2. **READ:** All output carefully

3. **IDENTIFY:** Which test fails

4. **FIX:** Based on the failure:
   - Base32 fails → Generate new secret
   - Invalid chars → Fix secret generation
   - Time wrong → Sync server time
   - All pass but codes wrong → Secret mismatch

5. **TEST:** After fix, retest on test_2fa.php

6. **VERIFY:** Try setup_2fa.php with debug mode

7. **SUCCESS:** Complete 2FA setup

---

## 🎯 EXPECTED OUTCOME

After running diagnostic, you'll know:
- ✅ If TOTP generation works
- ✅ If your secret is valid
- ✅ What the current codes should be
- ✅ If there's a character set issue
- ✅ If server time is correct

**Run the diagnostic NOW and share the output!**

```
/app/admin/handlers/diagnostic.php
```

**This will tell us exactly what's wrong!** 🔍

