# 🔐 2FA Implementation Guide - TOTP (Recommended)

## ✅ Blue Theme Applied + 2FA Ready!

Your login page now has a **superior bluish color scheme** with deep ocean blues, cyan accents, and sky tones!

---

## 🎨 Blue Theme Changes

### **Color Palette:**
- **Background:** Deep blue gradient (`#0a1628` → `#1e3a8a` → `#1e40af`)
- **Cards:** Blue glass morphism with cyan borders
- **Text:** Sky blue (`#e0f2fe`, `#7dd3fc`, `#bae6fd`)
- **Accents:** Cyan (`#06b6d4`) and light blue (`#3b82f6`)
- **Buttons:** Blue-cyan gradient
- **Glows:** Blue shadows and focus effects

### **Visual Elements:**
- ✨ Blue animated background orbs
- 💎 Glass cards with blue tint
- ⚡ Cyan scan lines
- 🌊 Blue grid pattern
- 💙 Blue focus glows
- 🔵 Blue security badges

---

## 🔐 2FA Implementation Recommendation

### **Best Method: TOTP (Time-Based One-Time Password)**

**Why TOTP is Best:**
- ✅ **No SMS costs** - No carrier fees
- ✅ **Works offline** - No internet required after setup
- ✅ **Most secure** - Industry standard
- ✅ **User-friendly** - Popular apps available
- ✅ **No dependencies** - No external services
- ✅ **FIDO2 compliant** - Future-proof

**Compatible Apps:**
- Google Authenticator (iOS/Android)
- Microsoft Authenticator (iOS/Android)
- Authy (iOS/Android/Desktop)
- 1Password (Cross-platform)
- LastPass Authenticator

---

## 📦 Required Library

**PHP Library:** `spomky-labs/otphp`

### **Installation:**

**Via Composer (Recommended):**
```bash
cd /Users/danielkinyua/Downloads/projects/ad/adsphere
composer require spomky-labs/otphp
```

**Manual Installation (If no Composer):**
```bash
# Download from GitHub
wget https://github.com/Spomky-Labs/otphp/archive/refs/heads/main.zip
unzip main.zip
mv otphp-main/src app/lib/otphp
```

---

## 🔧 Implementation Steps

### **Step 1: Database/Config Setup**

Update `/app/config/admins.json` to include 2FA fields:

```json
{
    "admin": {
        "username": "admin",
        "password": "$2y$10$...",
        "email": "admin@adsphere.com",
        "role": "super_admin",
        "created_at": 1702998400,
        "2fa_enabled": true,
        "2fa_secret": "BASE32SECRETKEY",
        "backup_codes": [
            "12345678",
            "87654321",
            "11223344"
        ]
    }
}
```

### **Step 2: Create 2FA Setup Page**

**File:** `/app/admin/setup_2fa.php`

```php
<?php
session_start();
require __DIR__ . '/../../vendor/autoload.php'; // If using Composer
// OR
// require __DIR__ . '/../lib/otphp/TOTP.php'; // If manual

use OTPHP\TOTP;

if(!isset($_SESSION['admin_logged_in'])) {
    header("Location: login.php");
    exit();
}

// Generate secret
$totp = TOTP::create();
$totp->setLabel($_SESSION['admin_username']);
$totp->setIssuer('AdSphere Admin');

$secret = $totp->getSecret();
$qrCodeUrl = $totp->getQrCodeUri(
    'https://api.qrserver.com/v1/create-qr-code/',
    '&size=300x300'
);

// Save secret to user config
$adminsFile = __DIR__ . "/../config/admins.json";
$admins = json_decode(file_get_contents($adminsFile), true);
$admins[$_SESSION['admin_username']]['2fa_secret'] = $secret;
$admins[$_SESSION['admin_username']]['2fa_enabled'] = false; // Not active until verified

file_put_contents($adminsFile, json_encode($admins, JSON_PRETTY_PRINT));

// Generate backup codes
$backupCodes = [];
for($i = 0; $i < 10; $i++) {
    $backupCodes[] = strtoupper(bin2hex(random_bytes(4)));
}
$admins[$_SESSION['admin_username']]['backup_codes'] = $backupCodes;
file_put_contents($adminsFile, json_encode($admins, JSON_PRETTY_PRINT));
?>

<!DOCTYPE html>
<html>
<head>
    <title>Setup 2FA</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gradient-to-br from-blue-900 to-indigo-900 min-h-screen p-8">
    <div class="max-w-2xl mx-auto bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-blue-500/30">
        <h1 class="text-3xl font-bold text-white mb-6">
            <i class="fas fa-shield-alt text-cyan-400 mr-3"></i>
            Enable Two-Factor Authentication
        </h1>

        <div class="space-y-6">
            <!-- Step 1 -->
            <div class="bg-blue-600/20 p-6 rounded-xl border border-blue-500/30">
                <h2 class="text-xl font-bold text-sky-200 mb-3">
                    Step 1: Scan QR Code
                </h2>
                <p class="text-sky-300/70 mb-4">
                    Open your authenticator app and scan this QR code:
                </p>
                <div class="bg-white p-4 rounded-lg inline-block">
                    <img src="<?= $qrCodeUrl ?>" alt="QR Code">
                </div>
            </div>

            <!-- Step 2 -->
            <div class="bg-blue-600/20 p-6 rounded-xl border border-blue-500/30">
                <h2 class="text-xl font-bold text-sky-200 mb-3">
                    Step 2: Manual Entry (Optional)
                </h2>
                <p class="text-sky-300/70 mb-2">
                    Or enter this secret key manually:
                </p>
                <div class="bg-blue-900/40 p-4 rounded-lg font-mono text-cyan-300 text-lg text-center border border-cyan-500/30">
                    <?= $secret ?>
                </div>
            </div>

            <!-- Step 3 -->
            <div class="bg-blue-600/20 p-6 rounded-xl border border-blue-500/30">
                <h2 class="text-xl font-bold text-sky-200 mb-3">
                    Step 3: Verify Code
                </h2>
                <form method="POST" action="verify_2fa.php">
                    <label class="text-sky-300/70 mb-2 block">
                        Enter the 6-digit code from your app:
                    </label>
                    <input 
                        type="text" 
                        name="code" 
                        maxlength="6" 
                        pattern="[0-9]{6}"
                        class="w-full px-6 py-4 bg-blue-900/40 border border-cyan-500/30 rounded-lg text-white text-2xl text-center font-mono focus:outline-none focus:border-cyan-400"
                        placeholder="000000"
                        required>
                    <button class="w-full mt-4 py-3 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg font-bold text-white hover:from-cyan-700 hover:to-blue-700 transition">
                        <i class="fas fa-check mr-2"></i>Verify & Enable 2FA
                    </button>
                </form>
            </div>

            <!-- Backup Codes -->
            <div class="bg-yellow-600/20 p-6 rounded-xl border border-yellow-500/30">
                <h2 class="text-xl font-bold text-yellow-200 mb-3">
                    <i class="fas fa-exclamation-triangle mr-2"></i>
                    Backup Codes
                </h2>
                <p class="text-yellow-300/70 mb-4">
                    Save these codes in a secure place. Each can be used once if you lose access to your authenticator:
                </p>
                <div class="grid grid-cols-2 gap-2">
                    <?php foreach($backupCodes as $code): ?>
                        <div class="bg-yellow-900/40 p-3 rounded-lg font-mono text-yellow-200 text-center border border-yellow-500/30">
                            <?= $code ?>
                        </div>
                    <?php endforeach; ?>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
```

### **Step 3: Create Verification Handler**

**File:** `/app/admin/verify_2fa.php`

```php
<?php
session_start();
require __DIR__ . '/../../vendor/autoload.php';

use OTPHP\TOTP;

if(!isset($_SESSION['admin_logged_in'])) {
    header("Location: login.php");
    exit();
}

$code = $_POST['code'] ?? '';

// Load admin config
$adminsFile = __DIR__ . "/../config/admins.json";
$admins = json_decode(file_get_contents($adminsFile), true);
$admin = $admins[$_SESSION['admin_username']];

// Verify code
$totp = TOTP::create($admin['2fa_secret']);
$totp->setLabel($_SESSION['admin_username']);

if($totp->verify($code, null, 2)) {
    // Code is valid - enable 2FA
    $admins[$_SESSION['admin_username']]['2fa_enabled'] = true;
    file_put_contents($adminsFile, json_encode($admins, JSON_PRETTY_PRINT));
    
    header("Location: admin_dashboard.php?2fa=enabled");
    exit();
} else {
    header("Location: setup_2fa.php?error=invalid_code");
    exit();
}
?>
```

### **Step 4: Update Login.php**

Add 2FA verification after password check:

```php
// After password verification success:
if (verifyAdminCredentials($username, $password)) {
    
    // Check if 2FA is enabled
    $adminsFile = __DIR__ . "/../config/admins.json";
    $admins = json_decode(file_get_contents($adminsFile), true);
    
    if(isset($admins[$username]['2fa_enabled']) && $admins[$username]['2fa_enabled']) {
        // Store username temporarily and redirect to 2FA page
        $_SESSION['pending_2fa_username'] = $username;
        $_SESSION['pending_2fa_time'] = time();
        
        header("Location: verify_2fa_login.php");
        exit();
    }
    
    // No 2FA or not enabled - proceed with normal login
    session_regenerate_id(true);
    $_SESSION['admin_logged_in'] = true;
    // ... rest of login code
}
```

### **Step 5: Create 2FA Login Verification Page**

**File:** `/app/admin/verify_2fa_login.php`

```php
<?php
session_start();
require __DIR__ . '/../../vendor/autoload.php';

use OTPHP\TOTP;

// Check if 2FA verification is pending
if(!isset($_SESSION['pending_2fa_username'])) {
    header("Location: login.php");
    exit();
}

// Timeout after 5 minutes
if(time() - $_SESSION['pending_2fa_time'] > 300) {
    unset($_SESSION['pending_2fa_username']);
    unset($_SESSION['pending_2fa_time']);
    header("Location: login.php?error=2fa_timeout");
    exit();
}

$errorMsg = "";

if($_SERVER['REQUEST_METHOD'] === 'POST') {
    $code = $_POST['code'] ?? '';
    $username = $_SESSION['pending_2fa_username'];
    
    // Load admin config
    $adminsFile = __DIR__ . "/../config/admins.json";
    $admins = json_decode(file_get_contents($adminsFile), true);
    $admin = $admins[$username];
    
    // Try normal code first
    $totp = TOTP::create($admin['2fa_secret']);
    $isValid = $totp->verify($code, null, 2); // Allow 2 periods of variance
    
    // If not valid, try backup codes
    if(!$isValid && isset($admin['backup_codes'])) {
        $backupIndex = array_search($code, $admin['backup_codes']);
        if($backupIndex !== false) {
            $isValid = true;
            // Remove used backup code
            unset($admins[$username]['backup_codes'][$backupIndex]);
            $admins[$username]['backup_codes'] = array_values($admins[$username]['backup_codes']);
            file_put_contents($adminsFile, json_encode($admins, JSON_PRETTY_PRINT));
        }
    }
    
    if($isValid) {
        // 2FA successful - complete login
        unset($_SESSION['pending_2fa_username']);
        unset($_SESSION['pending_2fa_time']);
        
        session_regenerate_id(true);
        $_SESSION['admin_logged_in'] = true;
        $_SESSION['admin_username'] = $username;
        $_SESSION['admin_role'] = 'super_admin';
        $_SESSION['login_time'] = time();
        $_SESSION['last_activity'] = time();
        
        header("Location: admin_dashboard.php");
        exit();
    } else {
        $errorMsg = "Invalid code. Please try again.";
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>2FA Verification</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body class="bg-gradient-to-br from-blue-900 to-indigo-900 min-h-screen flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-white/10 backdrop-blur-lg rounded-2xl p-8 border border-blue-500/30">
        <div class="text-center mb-6">
            <div class="w-16 h-16 bg-cyan-600/30 rounded-full flex items-center justify-center mx-auto mb-4">
                <i class="fas fa-mobile-alt text-cyan-400 text-2xl"></i>
            </div>
            <h1 class="text-2xl font-bold text-white mb-2">Two-Factor Authentication</h1>
            <p class="text-sky-300/70">Enter the code from your authenticator app</p>
        </div>

        <?php if($errorMsg): ?>
            <div class="mb-4 p-3 bg-red-600/20 border border-red-500/50 rounded-lg text-red-400 text-sm">
                <?= htmlspecialchars($errorMsg) ?>
            </div>
        <?php endif; ?>

        <form method="POST" class="space-y-4">
            <div>
                <input 
                    type="text" 
                    name="code" 
                    maxlength="6" 
                    pattern="[0-9]{6}"
                    class="w-full px-6 py-4 bg-blue-900/40 border border-cyan-500/30 rounded-lg text-white text-2xl text-center font-mono focus:outline-none focus:border-cyan-400"
                    placeholder="000000"
                    autofocus
                    required>
            </div>

            <button class="w-full py-3 bg-gradient-to-r from-cyan-600 to-blue-600 rounded-lg font-bold text-white hover:from-cyan-700 hover:to-blue-700 transition">
                <i class="fas fa-check mr-2"></i>Verify
            </button>

            <div class="text-center">
                <a href="login.php" class="text-cyan-400 hover:text-cyan-300 text-sm">
                    <i class="fas fa-arrow-left mr-1"></i>Back to Login
                </a>
            </div>
        </form>

        <div class="mt-6 pt-6 border-t border-white/10">
            <p class="text-xs text-sky-300/50 text-center">
                Lost your device? Contact support or use a backup code
            </p>
        </div>
    </div>

    <script>
        // Auto-submit when 6 digits entered
        const input = document.querySelector('input[name="code"]');
        input.addEventListener('input', function() {
            if(this.value.length === 6) {
                this.form.submit();
            }
        });
    </script>
</body>
</html>
```

---

## 🔄 Alternative 2FA Methods (Not Recommended)

### **Option 2: SMS 2FA**
**Pros:** Familiar to users  
**Cons:** 
- Requires SMS gateway (Twilio, etc.)
- Monthly costs
- Can be intercepted
- Requires internet
- Phone number dependency

### **Option 3: Email 2FA**
**Pros:** No extra apps needed  
**Cons:**
- Less secure (email can be compromised)
- Depends on email service
- Can be delayed
- Not industry standard

### **Option 4: Hardware Keys (U2F/FIDO2)**
**Pros:** Most secure  
**Cons:**
- Users need to buy hardware ($20-50)
- Can be lost
- Complex setup

---

## 📊 Comparison Table

| Method | Security | Cost | User Experience | Offline | Recommended |
|--------|----------|------|----------------|---------|-------------|
| **TOTP** | ⭐⭐⭐⭐⭐ | Free | ⭐⭐⭐⭐ | ✅ Yes | ✅ **YES** |
| SMS | ⭐⭐⭐ | $$$$ | ⭐⭐⭐⭐⭐ | ❌ No | ❌ No |
| Email | ⭐⭐ | Free | ⭐⭐⭐⭐ | ❌ No | ❌ No |
| Hardware Key | ⭐⭐⭐⭐⭐ | $$$ | ⭐⭐⭐ | ✅ Yes | 🟡 Maybe |

---

## 🎯 Implementation Checklist

- [ ] Install OTPHP library
- [ ] Create setup_2fa.php page
- [ ] Create verify_2fa.php handler
- [ ] Update login.php with 2FA check
- [ ] Create verify_2fa_login.php page
- [ ] Test with Google Authenticator
- [ ] Generate backup codes
- [ ] Add "Disable 2FA" option in settings
- [ ] Add "Re-generate backup codes" option
- [ ] Test backup code recovery
- [ ] Document for users

---

## 🔒 Security Best Practices

1. **Backup Codes:**
   - Generate 10 single-use codes
   - Store securely
   - Allow regeneration

2. **Secret Protection:**
   - Never expose secrets
   - Encrypt at rest
   - Rotate periodically

3. **Window Tolerance:**
   - Allow ±2 periods (60 seconds)
   - Prevents clock drift issues

4. **Rate Limiting:**
   - Max 5 attempts per 15 minutes
   - Prevent brute force

5. **Session Security:**
   - Require 2FA on new devices
   - Remember devices (30 days)

---

## 🎉 Result

Your login now features:
- ✅ **Superior blue color scheme**
- ✅ **Deep ocean blue gradients**
- ✅ **Cyan and sky blue accents**
- ✅ **Blue glowing effects**
- ✅ **2FA ready (TOTP recommended)**
- ✅ **Industry-standard security**

**Best 2FA Method: TOTP (Time-Based One-Time Password)**
- No costs
- Works offline
- Most secure
- User-friendly
- Industry standard

Need help implementing the 2FA code? Just ask! 🚀🔐

