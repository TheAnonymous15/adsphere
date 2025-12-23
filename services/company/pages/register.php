<?php
/**
 * COMPANY REGISTRATION PAGE
 * AdSphere - Modern Digital Advertising Platform
 */
session_start();

// Redirect if already logged in
if (isset($_SESSION['company'])) {
    header('Location: /dashboard');
    exit;
}

$error = '';
$success = '';

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $companyName = trim($_POST['company_name'] ?? '');
    $email = trim($_POST['email'] ?? '');
    $phone = trim($_POST['phone'] ?? '');
    $password = $_POST['password'] ?? '';
    $confirmPassword = $_POST['confirm_password'] ?? '';
    $category = $_POST['category'] ?? '';
    $agreeTerms = isset($_POST['agree_terms']);

    // Validation
    if (empty($companyName) || empty($email) || empty($password)) {
        $error = 'Please fill in all required fields.';
    } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $error = 'Please enter a valid email address.';
    } elseif (strlen($password) < 8) {
        $error = 'Password must be at least 8 characters long.';
    } elseif ($password !== $confirmPassword) {
        $error = 'Passwords do not match.';
    } elseif (!$agreeTerms) {
        $error = 'You must agree to the Terms of Service.';
    } else {
        // Create company slug
        $companySlug = strtolower(preg_replace('/[^a-zA-Z0-9]+/', '-', $companyName));
        $companySlug = trim($companySlug, '-');

        // Check if company already exists
        $companiesPath = dirname(__DIR__) . '/data/companies/';
        $companyPath = $companiesPath . $companySlug;

        if (is_dir($companyPath)) {
            $error = 'A company with this name already exists.';
        } else {
            // Create company directory and files
            if (!is_dir($companiesPath)) {
                mkdir($companiesPath, 0755, true);
            }
            mkdir($companyPath, 0755, true);

            // Create company data
            $companyData = [
                'company_slug' => $companySlug,
                'company_name' => $companyName,
                'email' => $email,
                'phone' => $phone,
                'password' => password_hash($password, PASSWORD_ARGON2ID),
                'category' => $category,
                'status' => 'active',
                'verified' => false,
                'created_at' => date('c'),
                'updated_at' => date('c')
            ];

            // Save company data
            file_put_contents($companyPath . '/company.json', json_encode($companyData, JSON_PRETTY_PRINT));

            // Create subdirectories
            mkdir($companyPath . '/ads', 0755, true);
            mkdir($companyPath . '/analytics', 0755, true);

            // Also save to database if available
            $dbPath = dirname(dirname(__DIR__)) . '/shared/database/adsphere.db';
            if (file_exists($dbPath)) {
                try {
                    $db = new PDO('sqlite:' . $dbPath);
                    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

                    $stmt = $db->prepare("INSERT INTO companies (company_slug, company_name, email, phone, password_hash, category, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'active', datetime('now'))");
                    $stmt->execute([$companySlug, $companyName, $email, $phone, $companyData['password'], $category]);
                } catch (PDOException $e) {
                    error_log('Registration DB error: ' . $e->getMessage());
                }
            }

            $success = 'Registration successful! You can now login.';

            // Optional: Auto-login after registration
            // $_SESSION['company'] = $companySlug;
            // $_SESSION['company_name'] = $companyName;
            // header('Location: /dashboard');
            // exit;
        }
    }
}

// Get categories for dropdown
$categories = ['Electronics', 'Vehicles', 'Property', 'Fashion', 'Furniture', 'Services', 'Jobs', 'Food & Beverages', 'Health & Beauty', 'Sports', 'Education', 'Other'];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Create Account - AdSphere</title>
    <link rel="icon" type="image/png" href="/services/assets/images/adsphere.ico">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" integrity="sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    <style>
        body {
            background: linear-gradient(135deg, #0f172a, #1e3a5f, #4338ca, #6d28d9);
            background-size: 400% 400%;
            animation: gradientShift 20s ease infinite;
            min-height: 100vh;
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        .glass-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .input-field {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }

        .input-field:focus {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(99, 102, 241, 0.5);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }

        .input-field::placeholder {
            color: rgba(255, 255, 255, 0.4);
        }

        .btn-primary {
            background: linear-gradient(135deg, #6366f1, #8b5cf6, #d946ef);
            background-size: 200% 200%;
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            background-position: 100% 50%;
            transform: translateY(-2px);
            box-shadow: 0 10px 40px rgba(99, 102, 241, 0.4);
        }

        .floating-shapes {
            position: fixed;
            width: 100%;
            height: 100%;
            overflow: hidden;
            z-index: 0;
            pointer-events: none;
        }

        .shape {
            position: absolute;
            border-radius: 50%;
            opacity: 0.1;
            animation: float 20s infinite;
        }

        .shape-1 {
            width: 300px;
            height: 300px;
            background: linear-gradient(135deg, #6366f1, #d946ef);
            top: -100px;
            right: -100px;
            animation-delay: 0s;
        }

        .shape-2 {
            width: 200px;
            height: 200px;
            background: linear-gradient(135deg, #8b5cf6, #06b6d4);
            bottom: -50px;
            left: -50px;
            animation-delay: -5s;
        }

        .shape-3 {
            width: 150px;
            height: 150px;
            background: linear-gradient(135deg, #d946ef, #f59e0b);
            top: 50%;
            right: 10%;
            animation-delay: -10s;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            50% { transform: translateY(-30px) rotate(180deg); }
        }

        .password-strength {
            height: 4px;
            border-radius: 2px;
            transition: all 0.3s ease;
        }
    </style>
</head>
<body class="min-h-screen flex items-center justify-center p-4">

<!-- Floating Background Shapes -->
<div class="floating-shapes">
    <div class="shape shape-1"></div>
    <div class="shape shape-2"></div>
    <div class="shape shape-3"></div>
</div>

<!-- Main Container -->
<div class="relative z-10 w-full max-w-lg">

    <!-- Logo & Header -->
    <div class="text-center mb-8">
        <a href="/" class="inline-flex items-center gap-3 mb-4 group">
            <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                <i class="fas fa-bullhorn text-2xl text-white"></i>
            </div>
            <span class="text-3xl font-bold text-white">AdSphere</span>
        </a>
        <h1 class="text-2xl font-bold text-white mb-2">Create Your Account</h1>
        <p class="text-indigo-200/70">Join thousands of advertisers reaching millions</p>
    </div>

    <!-- Registration Card -->
    <div class="glass-card rounded-3xl p-8 shadow-2xl">

        <?php if ($error): ?>
        <div class="mb-6 p-4 rounded-xl bg-red-500/20 border border-red-500/30 text-red-200 flex items-center gap-3">
            <i class="fas fa-exclamation-circle text-red-400"></i>
            <span><?= htmlspecialchars($error) ?></span>
        </div>
        <?php endif; ?>

        <?php if ($success): ?>
        <div class="mb-6 p-4 rounded-xl bg-green-500/20 border border-green-500/30 text-green-200 flex items-center gap-3">
            <i class="fas fa-check-circle text-green-400"></i>
            <div>
                <span><?= htmlspecialchars($success) ?></span>
                <a href="/login" class="block mt-2 text-green-300 hover:text-green-200 font-semibold">
                    <i class="fas fa-sign-in-alt mr-1"></i>Go to Login
                </a>
            </div>
        </div>
        <?php else: ?>

        <form method="POST" action="" class="space-y-5" id="registerForm">

            <!-- Company Name -->
            <div>
                <label class="block text-sm font-medium text-indigo-200 mb-2">
                    <i class="fas fa-building mr-2"></i>Company / Business Name *
                </label>
                <input type="text" name="company_name" required
                    class="input-field w-full px-4 py-3.5 rounded-xl text-white focus:outline-none"
                    placeholder="Enter your company name"
                    value="<?= htmlspecialchars($_POST['company_name'] ?? '') ?>">
            </div>

            <!-- Email -->
            <div>
                <label class="block text-sm font-medium text-indigo-200 mb-2">
                    <i class="fas fa-envelope mr-2"></i>Email Address *
                </label>
                <input type="email" name="email" required
                    class="input-field w-full px-4 py-3.5 rounded-xl text-white focus:outline-none"
                    placeholder="your@email.com"
                    value="<?= htmlspecialchars($_POST['email'] ?? '') ?>">
            </div>

            <!-- Phone -->
            <div>
                <label class="block text-sm font-medium text-indigo-200 mb-2">
                    <i class="fas fa-phone mr-2"></i>Phone Number
                </label>
                <input type="tel" name="phone"
                    class="input-field w-full px-4 py-3.5 rounded-xl text-white focus:outline-none"
                    placeholder="+254 700 000 000"
                    value="<?= htmlspecialchars($_POST['phone'] ?? '') ?>">
            </div>

            <!-- Category -->
            <div>
                <label class="block text-sm font-medium text-indigo-200 mb-2">
                    <i class="fas fa-tags mr-2"></i>Business Category
                </label>
                <select name="category" class="input-field w-full px-4 py-3.5 rounded-xl text-white focus:outline-none">
                    <option value="" class="bg-slate-800">Select a category</option>
                    <?php foreach ($categories as $cat): ?>
                    <option value="<?= strtolower(str_replace(' ', '_', $cat)) ?>" class="bg-slate-800"
                        <?= (($_POST['category'] ?? '') === strtolower(str_replace(' ', '_', $cat))) ? 'selected' : '' ?>>
                        <?= $cat ?>
                    </option>
                    <?php endforeach; ?>
                </select>
            </div>

            <!-- Password -->
            <div>
                <label class="block text-sm font-medium text-indigo-200 mb-2">
                    <i class="fas fa-lock mr-2"></i>Password *
                </label>
                <div class="relative">
                    <input type="password" name="password" id="password" required minlength="8"
                        class="input-field w-full px-4 py-3.5 rounded-xl text-white focus:outline-none pr-12"
                        placeholder="Min. 8 characters">
                    <button type="button" onclick="togglePassword('password')" class="absolute right-4 top-1/2 -translate-y-1/2 text-indigo-300 hover:text-white transition-colors">
                        <i class="fas fa-eye" id="password-icon"></i>
                    </button>
                </div>
                <!-- Password Strength Indicator -->
                <div class="mt-2 flex gap-1">
                    <div class="password-strength flex-1 bg-white/10" id="strength-1"></div>
                    <div class="password-strength flex-1 bg-white/10" id="strength-2"></div>
                    <div class="password-strength flex-1 bg-white/10" id="strength-3"></div>
                    <div class="password-strength flex-1 bg-white/10" id="strength-4"></div>
                </div>
                <p class="text-xs text-indigo-300/60 mt-1" id="password-hint">Use 8+ characters with mix of letters, numbers & symbols</p>
            </div>

            <!-- Confirm Password -->
            <div>
                <label class="block text-sm font-medium text-indigo-200 mb-2">
                    <i class="fas fa-lock mr-2"></i>Confirm Password *
                </label>
                <div class="relative">
                    <input type="password" name="confirm_password" id="confirm_password" required
                        class="input-field w-full px-4 py-3.5 rounded-xl text-white focus:outline-none pr-12"
                        placeholder="Confirm your password">
                    <button type="button" onclick="togglePassword('confirm_password')" class="absolute right-4 top-1/2 -translate-y-1/2 text-indigo-300 hover:text-white transition-colors">
                        <i class="fas fa-eye" id="confirm_password-icon"></i>
                    </button>
                </div>
                <p class="text-xs mt-1 hidden" id="password-match"></p>
            </div>

            <!-- Terms Agreement -->
            <div class="flex items-start gap-3">
                <input type="checkbox" name="agree_terms" id="agree_terms" required
                    class="w-5 h-5 rounded border-white/20 bg-white/5 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-0 mt-0.5">
                <label for="agree_terms" class="text-sm text-indigo-200/80">
                    I agree to the <a href="/terms" class="text-indigo-300 hover:text-white underline">Terms of Service</a>
                    and <a href="/privacy" class="text-indigo-300 hover:text-white underline">Privacy Policy</a>
                </label>
            </div>

            <!-- Submit Button -->
            <button type="submit" class="btn-primary w-full py-4 rounded-xl text-white font-semibold text-lg flex items-center justify-center gap-2 mt-6">
                <i class="fas fa-user-plus"></i>
                <span>Create Account</span>
            </button>

        </form>

        <?php endif; ?>

        <!-- Divider -->
        <div class="relative my-8">
            <div class="absolute inset-0 flex items-center">
                <div class="w-full border-t border-white/10"></div>
            </div>
            <div class="relative flex justify-center text-sm">
                <span class="px-4 bg-transparent text-indigo-300/60">or continue with</span>
            </div>
        </div>

        <!-- Social Login -->
        <div class="grid grid-cols-2 gap-4">
            <button type="button" class="flex items-center justify-center gap-2 py-3 rounded-xl bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-all">
                <i class="fab fa-google text-lg"></i>
                <span>Google</span>
            </button>
            <button type="button" class="flex items-center justify-center gap-2 py-3 rounded-xl bg-white/5 border border-white/10 text-white hover:bg-white/10 transition-all">
                <i class="fab fa-microsoft text-lg"></i>
                <span>Microsoft</span>
            </button>
        </div>

        <!-- Login Link -->
        <p class="text-center text-indigo-200/70 mt-8">
            Already have an account?
            <a href="/login" class="text-white font-semibold hover:text-indigo-300 transition-colors">
                Sign In <i class="fas fa-arrow-right ml-1"></i>
            </a>
        </p>

    </div>

    <!-- Back to Home -->
    <p class="text-center mt-6">
        <a href="http://localhost:8001" class="text-indigo-300/60 hover:text-white transition-colors text-sm">
            <i class="fas fa-arrow-left mr-2"></i>Back to Home
        </a>
    </p>

</div>

<script>
// Toggle password visibility
function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    const icon = document.getElementById(inputId + '-icon');

    if (input.type === 'password') {
        input.type = 'text';
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// Password strength checker
document.getElementById('password')?.addEventListener('input', function(e) {
    const password = e.target.value;
    let strength = 0;

    if (password.length >= 8) strength++;
    if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength++;
    if (password.match(/\d/)) strength++;
    if (password.match(/[^a-zA-Z\d]/)) strength++;

    const colors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-green-500'];
    const hints = ['Weak', 'Fair', 'Good', 'Strong'];

    for (let i = 1; i <= 4; i++) {
        const bar = document.getElementById('strength-' + i);
        bar.className = 'password-strength flex-1 transition-all';
        if (i <= strength) {
            bar.classList.add(colors[strength - 1]);
        } else {
            bar.classList.add('bg-white/10');
        }
    }

    const hint = document.getElementById('password-hint');
    if (password.length > 0) {
        hint.textContent = 'Password strength: ' + (hints[strength - 1] || 'Too weak');
        hint.className = 'text-xs mt-1 ' + (strength >= 3 ? 'text-green-400' : strength >= 2 ? 'text-yellow-400' : 'text-red-400');
    } else {
        hint.textContent = 'Use 8+ characters with mix of letters, numbers & symbols';
        hint.className = 'text-xs text-indigo-300/60 mt-1';
    }
});

// Password match checker
document.getElementById('confirm_password')?.addEventListener('input', function(e) {
    const password = document.getElementById('password').value;
    const confirm = e.target.value;
    const matchEl = document.getElementById('password-match');

    if (confirm.length > 0) {
        matchEl.classList.remove('hidden');
        if (password === confirm) {
            matchEl.textContent = '✓ Passwords match';
            matchEl.className = 'text-xs mt-1 text-green-400';
        } else {
            matchEl.textContent = '✗ Passwords do not match';
            matchEl.className = 'text-xs mt-1 text-red-400';
        }
    } else {
        matchEl.classList.add('hidden');
    }
});

// Form validation
document.getElementById('registerForm')?.addEventListener('submit', function(e) {
    const password = document.getElementById('password').value;
    const confirm = document.getElementById('confirm_password').value;

    if (password !== confirm) {
        e.preventDefault();
        alert('Passwords do not match!');
        return false;
    }

    if (password.length < 8) {
        e.preventDefault();
        alert('Password must be at least 8 characters long!');
        return false;
    }
});
</script>

</body>
</html>

