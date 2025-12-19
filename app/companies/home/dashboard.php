<?php
/********************************************
 * Company Dashboard - AdSphere
 * Enhanced version with analytics and management
 ********************************************/
session_start();

// Block unauthorized access
if(!isset($_SESSION['company'])) {
    header("Location: /app/companies/handlers/login.php");
    exit();
}

$companySlug = $_SESSION['company'];
$companyName = $_SESSION['company_name'] ?? ucfirst($companySlug);
$companyEmail = $_SESSION['company_email'] ?? '';
$loginTime = $_SESSION['login_time'] ?? time();

// Load company metadata
$metaFile = __DIR__ . "/../metadata/{$companySlug}.json";
$companyData = [];
if (file_exists($metaFile)) {
    $companyData = json_decode(file_get_contents($metaFile), true);
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Dashboard - AdSphere</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
    <style>
        .stat-card {
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .stat-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            transition: left 0.5s;
        }
        .stat-card:hover::before {
            left: 100%;
        }
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(99, 102, 241, 0.3);
        }
        .ad-card {
            transition: all 0.3s ease;
        }
        .ad-card:hover {
            transform: scale(1.02);
        }
        @keyframes pulse-slow {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes fadeInUp {
            from { transform: translateY(20px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }
        @keyframes shimmer {
            0% { background-position: -1000px 0; }
            100% { background-position: 1000px 0; }
        }
        .loading {
            animation: pulse-slow 2s infinite;
        }
        .slide-in {
            animation: slideInRight 0.5s ease-out;
        }
        .fade-in-up {
            animation: fadeInUp 0.6s ease-out;
        }
        .chart-container {
            position: relative;
            height: 300px;
        }
        .glass-effect {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .gradient-text {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .shimmer-loading {
            background: linear-gradient(90deg, #1e293b 0%, #334155 50%, #1e293b 100%);
            background-size: 1000px 100%;
            animation: shimmer 2s infinite;
        }
        .notification-badge {
            animation: pulse-slow 2s infinite;
        }
        .metric-increase {
            color: #10b981;
        }
        .metric-decrease {
            color: #ef4444;
        }
        .scroll-container {
            scrollbar-width: thin;
            scrollbar-color: rgba(99, 102, 241, 0.5) transparent;
        }
        .scroll-container::-webkit-scrollbar {
            width: 6px;
        }
        .scroll-container::-webkit-scrollbar-track {
            background: transparent;
        }
        .scroll-container::-webkit-scrollbar-thumb {
            background: rgba(99, 102, 241, 0.5);
            border-radius: 3px;
        }
    </style>
</head>

<body class="bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900 text-white min-h-screen">

<!-- NAVBAR -->
<nav class="bg-slate-900/80 backdrop-blur-lg border-b border-white/10 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">

            <!-- Logo/Brand -->
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                    <i class="fas fa-ad text-white text-xl"></i>
                </div>
                <div>
                    <h1 class="text-xl font-bold text-white">AdSphere</h1>
                    <p class="text-xs text-gray-400">Company Portal</p>
                </div>
            </div>

            <!-- Desktop Menu -->
            <div class="hidden md:flex items-center gap-6">
                <a href="#overview" class="text-gray-300 hover:text-white transition">
                    <i class="fas fa-home mr-2"></i>Overview
                </a>
                <a href="#my-ads" class="text-gray-300 hover:text-white transition">
                    <i class="fas fa-rectangle-ad mr-2"></i>My Ads
                </a>
                <a href="upload_ad.php" class="text-gray-300 hover:text-white transition">
                    <i class="fas fa-plus-circle mr-2"></i>New Ad
                </a>
                <a href="profile.php" class="text-gray-300 hover:text-white transition">
                    <i class="fas fa-user mr-2"></i>Profile
                </a>
            </div>

            <!-- User Menu -->
            <div class="flex items-center gap-4">
                <div class="hidden sm:block text-right">
                    <p class="text-sm font-medium"><?= htmlspecialchars($companyName) ?></p>
                    <p class="text-xs text-gray-400"><?= htmlspecialchars($companyEmail) ?></p>
                </div>
                <div class="relative">
                    <button id="userMenuBtn" class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-bold hover:shadow-lg transition">
                        <?= strtoupper(substr($companyName, 0, 1)) ?>
                    </button>
                    <!-- Dropdown -->
                    <div id="userMenuDropdown" class="hidden absolute right-0 mt-2 w-48 bg-slate-800 rounded-lg shadow-xl border border-white/10 py-2">
                        <a href="profile.php" class="block px-4 py-2 hover:bg-white/10 transition">
                            <i class="fas fa-user mr-2"></i>Profile
                        </a>
                        <a href="#settings" class="block px-4 py-2 hover:bg-white/10 transition">
                            <i class="fas fa-cog mr-2"></i>Settings
                        </a>
                        <hr class="border-white/10 my-2">
                        <a href="/app/companies/handlers/logout.php" class="block px-4 py-2 hover:bg-red-500/20 text-red-400 transition">
                            <i class="fas fa-sign-out-alt mr-2"></i>Logout
                        </a>
                    </div>
                </div>

                <!-- Mobile Menu Toggle -->
                <button id="mobileMenuBtn" class="md:hidden text-white">
                    <i class="fas fa-bars text-2xl"></i>
                </button>
            </div>
        </div>
    </div>

    <!-- Mobile Menu -->
    <div id="mobileMenu" class="hidden md:hidden bg-slate-800 border-t border-white/10">
        <a href="#overview" class="block px-4 py-3 hover:bg-white/10 transition">
            <i class="fas fa-home mr-2"></i>Overview
        </a>
        <a href="#my-ads" class="block px-4 py-3 hover:bg-white/10 transition">
            <i class="fas fa-rectangle-ad mr-2"></i>My Ads
        </a>
        <a href="upload_ad.php" class="block px-4 py-3 hover:bg-white/10 transition">
            <i class="fas fa-plus-circle mr-2"></i>New Ad
        </a>
        <a href="profile.php" class="block px-4 py-3 hover:bg-white/10 transition">
            <i class="fas fa-user mr-2"></i>Profile
        </a>
    </div>
</nav>


<!-- MAIN CONTENT -->
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

    <!-- WELCOME BANNER -->
    <div id="overview" class="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-2xl p-6 sm:p-8 mb-8 shadow-xl">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div>
                <h1 class="text-3xl sm:text-4xl font-bold mb-2">Welcome back, <?= htmlspecialchars($companyName) ?>!</h1>
                <p class="text-indigo-100">Here's what's happening with your ads today</p>
                <p class="text-xs text-indigo-200 mt-2">
                    <i class="fas fa-clock mr-1"></i>
                    Last login: <?= date('M d, Y \a\t g:i A', $loginTime) ?>
                </p>
            </div>
            <a href="upload_ad.php" class="bg-white text-indigo-600 px-6 py-3 rounded-lg font-semibold hover:shadow-lg transition flex items-center gap-2">
                <i class="fas fa-plus-circle"></i>
                Post New Ad
            </a>
        </div>
    </div>

    <!-- SMART NOTIFICATIONS -->
    <div id="smartNotifications" class="mb-8"></div>

    <!-- STATISTICS CARDS -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">

        <!-- Total Ads Card -->
        <div class="stat-card bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-white/10">
            <div class="flex items-center justify-between mb-4">
                <div class="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
                    <i class="fas fa-rectangle-ad text-blue-400 text-xl"></i>
                </div>
                <span class="text-xs text-gray-400">Total</span>
            </div>
            <h3 class="text-3xl font-bold mb-1" id="totalAds">
                <span class="loading">-</span>
            </h3>
            <p class="text-sm text-gray-400">Active Ads</p>
        </div>

        <!-- Total Views Card -->
        <div class="stat-card bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-white/10">
            <div class="flex items-center justify-between mb-4">
                <div class="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
                    <i class="fas fa-eye text-green-400 text-xl"></i>
                </div>
                <span class="text-xs text-gray-400">This month</span>
            </div>
            <h3 class="text-3xl font-bold mb-1" id="totalViews">
                <span class="loading">-</span>
            </h3>
            <p class="text-sm text-gray-400">Total Views</p>
        </div>

        <!-- Total Contacts Card -->
        <div class="stat-card bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-white/10">
            <div class="flex items-center justify-between mb-4">
                <div class="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center">
                    <i class="fas fa-phone text-purple-400 text-xl"></i>
                </div>
                <span class="text-xs text-gray-400">This week</span>
            </div>
            <h3 class="text-3xl font-bold mb-1" id="totalContacts">
                <span class="loading">-</span>
            </h3>
            <p class="text-sm text-gray-400">Contacts</p>
        </div>

        <!-- Total Favorites Card -->
        <div class="stat-card bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-white/10">
            <div class="flex items-center justify-between mb-4">
                <div class="w-12 h-12 bg-red-500/20 rounded-lg flex items-center justify-center">
                    <i class="fas fa-heart text-red-400 text-xl"></i>
                </div>
                <span class="text-xs text-gray-400">Active</span>
            </div>
            <h3 class="text-3xl font-bold mb-1" id="totalFavorites">
                <span class="loading">-</span>
            </h3>
            <p class="text-sm text-gray-400">Favorites</p>
        </div>

        <!-- Categories Card -->
        <div class="stat-card bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-white/10">
            <div class="flex items-center justify-between mb-4">
                <div class="w-12 h-12 bg-yellow-500/20 rounded-lg flex items-center justify-center">
                    <i class="fas fa-layer-group text-yellow-400 text-xl"></i>
                </div>
                <span class="text-xs text-gray-400">Active</span>
            </div>
            <h3 class="text-3xl font-bold mb-1" id="totalCategories">
                <?= count($companyData['categories'] ?? []) ?>
            </h3>
            <p class="text-sm text-gray-400">Categories</p>
        </div>
    </div>

    <!-- QUICK ACTIONS -->
    <div class="mb-8">
        <h2 class="text-2xl font-bold mb-4">Quick Actions</h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            <a href="upload_ad.php" class="bg-blue-600 hover:bg-blue-700 p-4 rounded-xl text-center transition group">
                <i class="fas fa-plus-circle text-3xl mb-2 group-hover:scale-110 transition"></i>
                <p class="font-semibold">Post Ad</p>
            </a>
            <a href="my_ads.php" class="bg-green-600 hover:bg-green-700 p-4 rounded-xl text-center transition group">
                <i class="fas fa-list text-3xl mb-2 group-hover:scale-110 transition"></i>
                <p class="font-semibold">My Ads</p>
            </a>
            <a href="profile.php" class="bg-purple-600 hover:bg-purple-700 p-4 rounded-xl text-center transition group">
                <i class="fas fa-user-edit text-3xl mb-2 group-hover:scale-110 transition"></i>
                <p class="font-semibold">Edit Profile</p>
            </a>
            <a href="#analytics" class="bg-yellow-600 hover:bg-yellow-700 p-4 rounded-xl text-center transition group">
                <i class="fas fa-chart-line text-3xl mb-2 group-hover:scale-110 transition"></i>
                <p class="font-semibold">Analytics</p>
            </a>
            <a href="#settings" class="bg-gray-700 hover:bg-gray-600 p-4 rounded-xl text-center transition group">
                <i class="fas fa-cog text-3xl mb-2 group-hover:scale-110 transition"></i>
                <p class="font-semibold">Settings</p>
            </a>
        </div>
    </div>

    <!-- AI INSIGHTS & RECOMMENDATIONS -->
    <div class="mb-8 fade-in-up">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-2xl font-bold flex items-center gap-2">
                <i class="fas fa-brain text-purple-400"></i>
                AI Insights
            </h2>
            <span class="text-xs text-gray-400">Powered by Machine Learning</span>
        </div>
        <div id="aiInsights" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <!-- Will be populated by JavaScript -->
            <div class="glass-effect rounded-xl p-4 shimmer-loading h-24"></div>
            <div class="glass-effect rounded-xl p-4 shimmer-loading h-24"></div>
            <div class="glass-effect rounded-xl p-4 shimmer-loading h-24"></div>
        </div>
    </div>

    <!-- LIVE ACTIVITY FEED -->
    <div class="mb-8 fade-in-up">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-2xl font-bold flex items-center gap-2">
                <i class="fas fa-rss text-green-400 animate-pulse"></i>
                Live Activity
            </h2>
            <button onclick="refreshActivityFeed()" class="text-xs text-gray-400 hover:text-white transition flex items-center gap-1">
                <i class="fas fa-sync-alt"></i>
                Refresh
            </button>
        </div>
        <div class="glass-effect rounded-xl p-6 border border-white/10">
            <div id="liveActivityFeed" class="space-y-3 max-h-96 overflow-y-auto scroll-container">
                <!-- Will be populated by JavaScript -->
                <div class="shimmer-loading h-16 rounded-lg"></div>
                <div class="shimmer-loading h-16 rounded-lg"></div>
                <div class="shimmer-loading h-16 rounded-lg"></div>
            </div>
        </div>
    </div>

    <!-- PERFORMANCE CHARTS -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <!-- Views Trend Chart -->
        <div class="glass-effect rounded-xl p-6 border border-white/10">
            <h3 class="text-lg font-bold mb-4 flex items-center gap-2">
                <i class="fas fa-chart-line text-blue-400"></i>
                Views Trend (Last 7 Days)
            </h3>
            <div class="chart-container">
                <canvas id="viewsTrendChart"></canvas>
            </div>
        </div>

        <!-- Contacts Trend Chart -->
        <div class="glass-effect rounded-xl p-6 border border-white/10">
            <h3 class="text-lg font-bold mb-4 flex items-center gap-2">
                <i class="fas fa-phone text-green-400"></i>
                Contacts Trend (Last 7 Days)
            </h3>
            <div class="chart-container">
                <canvas id="contactsTrendChart"></canvas>
            </div>
        </div>
    </div>

    <!-- CONTACT METHODS ANALYTICS -->
    <div class="mb-8">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
            <h2 class="text-2xl font-bold flex items-center gap-2">
                <i class="fas fa-phone-volume text-indigo-400"></i>
                Contact Methods Analytics
            </h2>
            <div class="flex items-center gap-2">
                <span class="text-xs text-gray-400">Date Range:</span>
                <select id="contactDateRange" onchange="updateContactAnalytics()" class="text-xs bg-slate-800 border border-gray-600 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    <option value="7">Last 7 Days</option>
                    <option value="30" selected>Last 30 Days</option>
                    <option value="90">Last 90 Days</option>
                    <option value="365">Last Year</option>
                </select>
            </div>
        </div>

        <!-- Total Engagement Stats -->
        <div class="glass-effect rounded-xl p-5 border border-white/10 mb-6">
            <div class="flex items-center justify-between mb-4">
                <h3 class="font-bold flex items-center gap-2">
                    <i class="fas fa-chart-bar text-yellow-400"></i>
                    Total Engagements
                </h3>
                <span class="text-2xl font-bold text-indigo-400" id="totalEngagements">0</span>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div class="bg-slate-900/50 rounded-lg p-3 text-center">
                    <p class="text-xs text-gray-400 mb-1">WhatsApp</p>
                    <p class="text-xl font-bold text-green-400" id="whatsappTotal">0</p>
                </div>
                <div class="bg-slate-900/50 rounded-lg p-3 text-center">
                    <p class="text-xs text-gray-400 mb-1">Phone Calls</p>
                    <p class="text-xl font-bold text-blue-400" id="callTotal">0</p>
                </div>
                <div class="bg-slate-900/50 rounded-lg p-3 text-center">
                    <p class="text-xs text-gray-400 mb-1">SMS</p>
                    <p class="text-xl font-bold text-purple-400" id="smsTotal">0</p>
                </div>
                <div class="bg-slate-900/50 rounded-lg p-3 text-center">
                    <p class="text-xs text-gray-400 mb-1">Email</p>
                    <p class="text-xl font-bold text-red-400" id="emailTotal">0</p>
                </div>
            </div>
        </div>

        <!-- Contact Method Stats Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div class="glass-effect rounded-xl p-4 border border-white/10 hover:border-green-500/50 transition cursor-pointer" onclick="toggleContactMethod('whatsapp')">
                <div class="flex items-center justify-between mb-2">
                    <i class="fab fa-whatsapp text-green-400 text-2xl"></i>
                    <div class="flex items-center gap-2">
                        <input type="checkbox" id="showWhatsapp" checked class="w-4 h-4 rounded bg-slate-900 border-gray-600 text-green-600 focus:ring-2 focus:ring-green-500">
                        <span class="text-xs text-gray-400">Show</span>
                    </div>
                </div>
                <p class="text-2xl font-bold" id="whatsappCount">0</p>
                <p class="text-xs text-gray-400 mt-1">WhatsApp Contacts</p>
            </div>

            <div class="glass-effect rounded-xl p-4 border border-white/10 hover:border-blue-500/50 transition cursor-pointer" onclick="toggleContactMethod('call')">
                <div class="flex items-center justify-between mb-2">
                    <i class="fas fa-phone text-blue-400 text-2xl"></i>
                    <div class="flex items-center gap-2">
                        <input type="checkbox" id="showCall" checked class="w-4 h-4 rounded bg-slate-900 border-gray-600 text-blue-600 focus:ring-2 focus:ring-blue-500">
                        <span class="text-xs text-gray-400">Show</span>
                    </div>
                </div>
                <p class="text-2xl font-bold" id="callCount">0</p>
                <p class="text-xs text-gray-400 mt-1">Phone Calls</p>
            </div>

            <div class="glass-effect rounded-xl p-4 border border-white/10 hover:border-purple-500/50 transition cursor-pointer" onclick="toggleContactMethod('sms')">
                <div class="flex items-center justify-between mb-2">
                    <i class="fas fa-sms text-purple-400 text-2xl"></i>
                    <div class="flex items-center gap-2">
                        <input type="checkbox" id="showSms" checked class="w-4 h-4 rounded bg-slate-900 border-gray-600 text-purple-600 focus:ring-2 focus:ring-purple-500">
                        <span class="text-xs text-gray-400">Show</span>
                    </div>
                </div>
                <p class="text-2xl font-bold" id="smsCount">0</p>
                <p class="text-xs text-gray-400 mt-1">Text Messages</p>
            </div>

            <div class="glass-effect rounded-xl p-4 border border-white/10 hover:border-red-500/50 transition cursor-pointer" onclick="toggleContactMethod('email')">
                <div class="flex items-center justify-between mb-2">
                    <i class="fas fa-envelope text-red-400 text-2xl"></i>
                    <div class="flex items-center gap-2">
                        <input type="checkbox" id="showEmail" checked class="w-4 h-4 rounded bg-slate-900 border-gray-600 text-red-600 focus:ring-2 focus:ring-red-500">
                        <span class="text-xs text-gray-400">Show</span>
                    </div>
                </div>
                <p class="text-2xl font-bold" id="emailCount">0</p>
                <p class="text-xs text-gray-400 mt-1">Email Contacts</p>
            </div>
        </div>

        <!-- Contact Methods Trend Chart -->
        <div class="glass-effect rounded-xl p-6 border border-white/10">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                <h3 class="text-lg font-bold flex items-center gap-2">
                    <i class="fas fa-chart-line text-indigo-400"></i>
                    Contact Methods Performance
                </h3>
                <div class="flex flex-wrap gap-2">
                    <button onclick="selectAllMethods()" class="text-xs bg-indigo-600 hover:bg-indigo-700 px-3 py-1.5 rounded-lg transition">
                        <i class="fas fa-check-square mr-1"></i>Select All
                    </button>
                    <button onclick="deselectAllMethods()" class="text-xs bg-gray-700 hover:bg-gray-600 px-3 py-1.5 rounded-lg transition">
                        <i class="fas fa-square mr-1"></i>Deselect All
                    </button>
                </div>
            </div>
            <div class="chart-container" style="position: relative; height: 350px;">
                <canvas id="contactMethodsChart"></canvas>
            </div>
        </div>
    </div>

    <!-- AI-POWERED INSIGHTS -->
    <div class="mb-8 fade-in-up">
        <div class="flex justify-between items-center mb-4">
            <h2 class="text-2xl font-bold flex items-center gap-2">
                <i class="fas fa-robot text-purple-400"></i>
                AI-Powered Insights
            </h2>
            <span class="text-xs text-gray-400">Intelligent recommendations</span>
        </div>
        <div id="contactInsights" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <!-- Will be populated by JavaScript -->
            <div class="glass-effect rounded-xl p-4 shimmer-loading h-32"></div>
            <div class="glass-effect rounded-xl p-4 shimmer-loading h-32"></div>
        </div>
    </div>

    <!-- CATEGORY PERFORMANCE & REVENUE TRACKING -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <!-- Category Performance -->
        <div class="glass-effect rounded-xl p-6 border border-white/10">
            <h3 class="text-lg font-bold mb-4 flex items-center gap-2">
                <i class="fas fa-layer-group text-yellow-400"></i>
                Category Performance
            </h3>
            <div class="chart-container">
                <canvas id="categoryChart"></canvas>
            </div>
        </div>

        <!-- Revenue Estimation -->
        <div class="glass-effect rounded-xl p-6 border border-white/10">
            <h3 class="text-lg font-bold mb-4 flex items-center gap-2">
                <i class="fas fa-dollar-sign text-green-400"></i>
                Revenue Estimation
            </h3>
            <div class="space-y-4">
                <div class="bg-slate-900/50 rounded-lg p-4">
                    <p class="text-sm text-gray-400 mb-1">Estimated Lead Value</p>
                    <p class="text-3xl font-bold text-green-400" id="revenueTotal">$0</p>
                    <p class="text-xs text-gray-500 mt-1">Based on industry averages ($5 per lead)</p>
                </div>
                <div class="bg-slate-900/50 rounded-lg p-4">
                    <p class="text-sm text-gray-400 mb-1">Projected Monthly</p>
                    <p class="text-2xl font-bold text-blue-400" id="revenueProjected">$0</p>
                    <p class="text-xs text-gray-500 mt-1">If current trend continues</p>
                </div>
                <div class="bg-gradient-to-r from-green-500/20 to-blue-500/20 rounded-lg p-4 border border-green-500/30">
                    <p class="text-sm font-semibold mb-2 flex items-center gap-2">
                        <i class="fas fa-lightbulb text-yellow-400"></i>
                        Monetization Tip
                    </p>
                    <p class="text-xs text-gray-300">Boost your top-performing ads to increase contact rate by up to 300%</p>
                </div>
            </div>
        </div>
    </div>



    <!-- MY ADS SECTION -->
    <section id="my-ads" class="mb-8">
        <div class="flex justify-between items-center mb-6">
            <h2 class="text-2xl font-bold">Your Ads</h2>
            <a href="my_ads.php" class="text-indigo-400 hover:text-indigo-300 text-sm">
                View All <i class="fas fa-arrow-right ml-1"></i>
            </a>
        </div>

        <!-- Loading State -->
        <div id="adsLoading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <div class="bg-slate-800/50 rounded-xl h-64 animate-pulse"></div>
            <div class="bg-slate-800/50 rounded-xl h-64 animate-pulse"></div>
            <div class="bg-slate-800/50 rounded-xl h-64 animate-pulse"></div>
        </div>

        <!-- Ads Container -->
        <div id="myAdsContainer" class="hidden grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- JS will populate -->
        </div>

        <!-- Empty State -->
        <div id="emptyState" class="hidden bg-slate-800/30 rounded-xl p-12 text-center">
            <i class="fas fa-rectangle-ad text-6xl text-gray-600 mb-4"></i>
            <h3 class="text-xl font-bold mb-2">No ads yet</h3>
            <p class="text-gray-400 mb-6">Start by posting your first advertisement</p>
            <a href="upload_ad.php" class="inline-block bg-indigo-600 hover:bg-indigo-700 px-6 py-3 rounded-lg font-semibold transition">
                <i class="fas fa-plus-circle mr-2"></i>Post Your First Ad
            </a>
        </div>
    </section>



    <!-- ANALYTICS SECTION -->
    <section id="analytics" class="mb-8">
        <h2 class="text-2xl font-bold mb-6">Analytics & Performance</h2>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">

            <!-- Category Performance -->
            <div class="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-white/10">
                <h3 class="text-lg font-bold mb-4">
                    <i class="fas fa-chart-pie text-indigo-400 mr-2"></i>
                    Ads by Category
                </h3>
                <div id="categoryChart" class="space-y-3">
                    <!-- JS will populate -->
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-white/10">
                <h3 class="text-lg font-bold mb-4">
                    <i class="fas fa-clock text-green-400 mr-2"></i>
                    Recent Activity
                </h3>
                <div id="recentActivity" class="space-y-3">
                    <div class="flex items-start gap-3 text-sm">
                        <div class="w-2 h-2 bg-green-400 rounded-full mt-2"></div>
                        <div class="flex-1">
                            <p class="text-gray-300">Account logged in</p>
                            <p class="text-xs text-gray-500"><?= date('M d, Y \a\t g:i A', $loginTime) ?></p>
                        </div>
                    </div>
                    <div id="activityList">
                        <!-- JS will populate -->
                    </div>
                </div>
            </div>

            <!-- Performance Metrics -->
            <div class="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-white/10">
                <h3 class="text-lg font-bold mb-4">
                    <i class="fas fa-tachometer-alt text-yellow-400 mr-2"></i>
                    Performance Metrics
                </h3>
                <div class="space-y-4">
                    <div>
                        <div class="flex justify-between text-sm mb-2">
                            <span>Ad Engagement</span>
                            <span class="text-green-400">+12%</span>
                        </div>
                        <div class="w-full bg-gray-700 rounded-full h-2">
                            <div class="bg-gradient-to-r from-green-400 to-blue-500 h-2 rounded-full" style="width: 75%"></div>
                        </div>
                    </div>
                    <div>
                        <div class="flex justify-between text-sm mb-2">
                            <span>Contact Rate</span>
                            <span class="text-blue-400">+8%</span>
                        </div>
                        <div class="w-full bg-gray-700 rounded-full h-2">
                            <div class="bg-gradient-to-r from-blue-400 to-purple-500 h-2 rounded-full" style="width: 60%"></div>
                        </div>
                    </div>
                    <div>
                        <div class="flex justify-between text-sm mb-2">
                            <span>Profile Views</span>
                            <span class="text-purple-400">+15%</span>
                        </div>
                        <div class="w-full bg-gray-700 rounded-full h-2">
                            <div class="bg-gradient-to-r from-purple-400 to-pink-500 h-2 rounded-full" style="width: 85%"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Top Performing Ads -->
            <div class="bg-slate-800/50 backdrop-blur rounded-xl p-6 border border-white/10">
                <h3 class="text-lg font-bold mb-4">
                    <i class="fas fa-trophy text-yellow-400 mr-2"></i>
                    Top Performing Ads
                </h3>
                <div id="topAds" class="space-y-3">
                    <!-- JS will populate -->
                </div>
            </div>
        </div>
    </section>


</div>

<!-- FOOTER -->
<footer class="bg-slate-900/80 border-t border-white/10 mt-12 py-6">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-gray-400 text-sm">
        <p>&copy; <?= date('Y') ?> AdSphere. All rights reserved.</p>
        <p class="mt-1">Logged in as <strong class="text-white"><?= htmlspecialchars($companyName) ?></strong></p>
    </div>
</footer>

<script>
/********************************************
 * Dashboard JavaScript
 * Handles data loading, statistics, and UI
 ********************************************/

const companySlug = "<?= $companySlug ?>";

// ============================================
// UTILITY FUNCTIONS
// ============================================
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(timestamp) {
    return new Date(timestamp * 1000).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function timeAgo(timestamp) {
    const seconds = Math.floor((Date.now() - (timestamp * 1000)) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' min ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours ago';
    if (seconds < 604800) return Math.floor(seconds / 86400) + ' days ago';
    return formatDate(timestamp);
}

// ============================================
// LOAD ADVANCED DASHBOARD DATA
// ============================================
let dashboardData = null;
let chartsInstances = {};

async function loadDashboardData() {
    try {
        // Fetch both basic ads and advanced stats
        const [adsRes, statsRes] = await Promise.all([
            fetch("/app/api/get_ads.php"),
            fetch("/app/api/dashboard_stats.php")
        ]);

        const adsData = await adsRes.json();
        const statsData = await statsRes.json();

        if (statsData.success) {
            dashboardData = statsData.data;

            // Update all dashboard sections
            updateStatistics();
            updateSmartNotifications();
            updateLiveActivity();
            updateAIInsights();
            loadContactAnalytics();
            renderCharts();
            renderAds(adsData.ads.filter(ad => ad.company === companySlug));
            updateTopPerformers();
            updateRevenue();

            // Update advanced analytics if functions exist
            if (typeof updateMostLiked === 'function') updateMostLiked();
            if (typeof updateMostFavorited === 'function') updateMostFavorited();
            if (typeof updateMostDisliked === 'function') updateMostDisliked();
            if (typeof updateEngagementLeaders === 'function') updateEngagementLeaders();
        }

    } catch (error) {
        console.error("Failed to load dashboard data:", error);
        showError();
    }
}

// ============================================
// SMART NOTIFICATIONS
// ============================================
function updateSmartNotifications() {
    if (!dashboardData) return;

    const container = document.getElementById('smartNotifications');
    if (!container) return;

    const { performance, overview, ai_insights } = dashboardData;
    const notifications = [];

    // Check for boost opportunities
    if (performance.total_views > 100 && performance.conversion_rate < 2) {
        notifications.push({
            type: 'opportunity',
            icon: 'fa-rocket',
            title: 'Boost Opportunity!',
            message: `Your ads have ${performance.total_views} views but low conversion. Boost your best ad now for 2x results!`,
            action: 'Boost Now',
            actionUrl: 'my_ads.php',
            priority: 'high'
        });
    }

    // Performance warnings
    if (performance.total_contacts < 5 && overview.total_ads > 10) {
        notifications.push({
            type: 'warning',
            icon: 'fa-exclamation-triangle',
            title: 'Low Engagement Alert',
            message: `You have ${overview.total_ads} ads but only ${performance.total_contacts} contacts. Improve descriptions and images.`,
            action: 'Get Tips',
            actionUrl: '#',
            priority: 'high'
        });
    }

    // Favorites milestone
    if (performance.current_favorites && performance.current_favorites >= 50) {
        notifications.push({
            type: 'success',
            icon: 'fa-heart',
            title: 'Users Love Your Ads!',
            message: `${performance.current_favorites} users have favorited your ads! Keep it up!`,
            action: 'View Stats',
            actionUrl: 'my_ads.php',
            priority: 'medium'
        });
    }

    // Render notifications
    if (notifications.length === 0) {
        container.innerHTML = '';
        return;
    }

    const notificationStyles = {
        opportunity: 'from-green-500/20 to-blue-500/20 border-green-500/50',
        warning: 'from-red-500/20 to-orange-500/20 border-red-500/50',
        success: 'from-green-500/20 to-emerald-500/20 border-green-500/50',
        info: 'from-blue-500/20 to-indigo-500/20 border-blue-500/50'
    };

    container.innerHTML = `
        <div class="space-y-3">
            ${notifications.map(notif => `
                <div class="notification-card bg-gradient-to-r ${notificationStyles[notif.type]} border rounded-xl p-4 flex items-start gap-4 slide-in">
                    <div class="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
                        <i class="fas ${notif.icon} text-xl"></i>
                    </div>
                    <div class="flex-1">
                        <h4 class="font-bold mb-1">${escapeHtml(notif.title)}</h4>
                        <p class="text-sm text-gray-200 mb-3">${escapeHtml(notif.message)}</p>
                        <div class="flex gap-2">
                            <a href="${notif.actionUrl}" class="text-sm px-4 py-1.5 bg-white/20 hover:bg-white/30 rounded-lg transition inline-block">
                                ${escapeHtml(notif.action)} <i class="fas fa-arrow-right ml-1"></i>
                            </a>
                            <button onclick="dismissNotification(this)" class="text-sm px-3 py-1.5 hover:bg-white/10 rounded-lg transition">
                                Dismiss
                            </button>
                        </div>
                    </div>
                    <button onclick="dismissNotification(this)" class="text-gray-400 hover:text-white transition">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `).join('')}
        </div>
    `;
}

function dismissNotification(btn) {
    const card = btn.closest('.notification-card');
    card.style.opacity = '0';
    card.style.transform = 'translateX(100%)';
    card.style.transition = 'all 0.3s';
    setTimeout(() => card.remove(), 300);
}

// ============================================
// LIVE ACTIVITY FEED
// ============================================
async function updateLiveActivity() {
    try {
        const response = await fetch('/app/api/live_activity.php');
        const data = await response.json();

        if (!data.success || !data.activities) return;

        const container = document.getElementById('liveActivityFeed');
        if (!container) return;

        if (data.activities.length === 0) {
            container.innerHTML = '<p class="text-gray-400 text-center py-4">No recent activity</p>';
            return;
        }

        const activityIcons = {
            'view': 'fa-eye text-blue-400',
            'click': 'fa-mouse-pointer text-purple-400',
            'contact': 'fa-phone text-green-400',
            'like': 'fa-thumbs-up text-yellow-400',
            'favorite': 'fa-heart text-red-400',
            'dislike': 'fa-thumbs-down text-orange-400',
            'favorited': 'fa-heart text-red-400',
            'liked': 'fa-thumbs-up text-yellow-400'
        };

        container.innerHTML = data.activities.map(activity => `
            <div class="flex items-start gap-3 p-3 rounded-lg hover:bg-white/5 transition">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center flex-shrink-0">
                    <i class="fas ${activityIcons[activity.type] || 'fa-circle'} text-sm"></i>
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm">
                        <span class="text-gray-400">${activity.location}</span>
                        <span class="font-medium">${activity.action}</span>
                        <span class="text-gray-400">on</span>
                        <span class="truncate text-indigo-400">${escapeHtml(activity.ad_title)}</span>
                    </p>
                    <p class="text-xs text-gray-500">${activity.time_ago}</p>
                </div>
                <i class="fas fa-circle text-green-400 text-xs animate-pulse"></i>
            </div>
        `).join('');

    } catch (error) {
        console.error('Failed to load activity feed:', error);
    }
}

// Refresh activity feed
async function refreshActivityFeed() {
    await updateLiveActivity();
}

// Auto-refresh every 30 seconds
setInterval(updateLiveActivity, 30000);

// ============================================
// CONTACT METHODS ANALYTICS
// ============================================
let contactMethodsChart = null;
let contactAnalyticsData = null;
let visibleMethods = {
    whatsapp: true,
    call: true,
    sms: true,
    email: true
};

async function loadContactAnalytics() {
    const dateRange = document.getElementById('contactDateRange')?.value || '30';

    try {
        const response = await fetch(`/app/api/contact_analytics.php?days=${dateRange}`);
        const data = await response.json();

        if (!data.success) return;

        contactAnalyticsData = data;

        // Calculate total engagements
        const total = data.contact_methods.whatsapp.count +
                     data.contact_methods.call.count +
                     data.contact_methods.sms.count +
                     data.contact_methods.email.count;

        // Update total engagement
        document.getElementById('totalEngagements').textContent = total.toLocaleString();
        document.getElementById('whatsappTotal').textContent = data.contact_methods.whatsapp.count.toLocaleString();
        document.getElementById('callTotal').textContent = data.contact_methods.call.count.toLocaleString();
        document.getElementById('smsTotal').textContent = data.contact_methods.sms.count.toLocaleString();
        document.getElementById('emailTotal').textContent = data.contact_methods.email.count.toLocaleString();

        // Update contact method counts
        document.getElementById('whatsappCount').textContent = data.contact_methods.whatsapp.count.toLocaleString();
        document.getElementById('callCount').textContent = data.contact_methods.call.count.toLocaleString();
        document.getElementById('smsCount').textContent = data.contact_methods.sms.count.toLocaleString();
        document.getElementById('emailCount').textContent = data.contact_methods.email.count.toLocaleString();

        // Render contact methods line chart
        renderContactMethodsChart(data.contact_methods);

        // Display AI insights
        displayContactInsights(data);

    } catch (error) {
        console.error('Failed to load contact analytics:', error);
    }
}

async function updateContactAnalytics() {
    await loadContactAnalytics();
}

function toggleContactMethod(method) {
    const checkbox = document.getElementById(`show${method.charAt(0).toUpperCase() + method.slice(1)}`);
    if (checkbox) {
        checkbox.checked = !checkbox.checked;
        visibleMethods[method] = checkbox.checked;

        if (contactAnalyticsData) {
            renderContactMethodsChart(contactAnalyticsData.contact_methods);
        }
    }
}

function selectAllMethods() {
    ['whatsapp', 'call', 'sms', 'email'].forEach(method => {
        const checkbox = document.getElementById(`show${method.charAt(0).toUpperCase() + method.slice(1)}`);
        if (checkbox) {
            checkbox.checked = true;
            visibleMethods[method] = true;
        }
    });

    if (contactAnalyticsData) {
        renderContactMethodsChart(contactAnalyticsData.contact_methods);
    }
}

function deselectAllMethods() {
    ['whatsapp', 'call', 'sms', 'email'].forEach(method => {
        const checkbox = document.getElementById(`show${method.charAt(0).toUpperCase() + method.slice(1)}`);
        if (checkbox) {
            checkbox.checked = false;
            visibleMethods[method] = false;
        }
    });

    if (contactAnalyticsData) {
        renderContactMethodsChart(contactAnalyticsData.contact_methods);
    }
}

function renderContactMethodsChart(contactMethods) {
    const ctx = document.getElementById('contactMethodsChart');
    if (!ctx) return;

    // Destroy existing chart if it exists
    if (contactMethodsChart) {
        contactMethodsChart.destroy();
    }

    const dates = contactMethods.whatsapp.trend.map(t => t.date);

    // Build datasets based on visible methods
    const datasets = [];

    if (visibleMethods.whatsapp) {
        datasets.push({
            label: 'WhatsApp',
            data: contactMethods.whatsapp.trend.map(t => t.count),
            borderColor: '#25d366',
            backgroundColor: 'rgba(37, 211, 102, 0.1)',
            tension: 0.4,
            fill: true,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: '#25d366',
            borderWidth: 2
        });
    }

    if (visibleMethods.call) {
        datasets.push({
            label: 'Phone Call',
            data: contactMethods.call.trend.map(t => t.count),
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            tension: 0.4,
            fill: true,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: '#3b82f6',
            borderWidth: 2
        });
    }

    if (visibleMethods.sms) {
        datasets.push({
            label: 'SMS',
            data: contactMethods.sms.trend.map(t => t.count),
            borderColor: '#a855f7',
            backgroundColor: 'rgba(168, 85, 247, 0.1)',
            tension: 0.4,
            fill: true,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: '#a855f7',
            borderWidth: 2
        });
    }

    if (visibleMethods.email) {
        datasets.push({
            label: 'Email',
            data: contactMethods.email.trend.map(t => t.count),
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.1)',
            tension: 0.4,
            fill: true,
            pointRadius: 4,
            pointHoverRadius: 6,
            pointBackgroundColor: '#ef4444',
            borderWidth: 2
        });
    }

    // Show message if no methods selected
    if (datasets.length === 0) {
        ctx.getContext('2d').clearRect(0, 0, ctx.width, ctx.height);
        return;
    }

    contactMethodsChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#fff',
                        usePointStyle: true,
                        padding: 15,
                        font: {
                            size: 12,
                            weight: '600'
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0, 0, 0, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: '#6366f1',
                    borderWidth: 2,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y + ' contacts';
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#9ca3af',
                        font: {
                            size: 11
                        },
                        padding: 8
                    },
                    title: {
                        display: true,
                        text: 'Number of Contacts',
                        color: '#9ca3af',
                        font: {
                            size: 12,
                            weight: '600'
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#9ca3af',
                        maxRotation: 45,
                        minRotation: 45,
                        font: {
                            size: 10
                        }
                    }
                }
            },
            interaction: {
                mode: 'index',
                intersect: false
            }
        }
    });
}

function displayContactInsights(data) {
    const container = document.getElementById('contactInsights');
    if (!container || !data.ai_insights) return;

    const insights = data.ai_insights;

    if (insights.length === 0) {
        container.innerHTML = `
            <div class="col-span-full glass-effect rounded-xl p-6 text-center">
                <i class="fas fa-chart-line text-gray-600 text-4xl mb-3"></i>
                <p class="text-gray-400">Not enough data yet. Insights will appear as users interact with your ads.</p>
            </div>
        `;
        return;
    }

    const insightColors = {
        'demographics': 'from-blue-500/20 to-purple-500/20 border-blue-500/50',
        'contact_preference': 'from-green-500/20 to-emerald-500/20 border-green-500/50',
        'timing': 'from-yellow-500/20 to-orange-500/20 border-yellow-500/50',
        'content': 'from-pink-500/20 to-red-500/20 border-pink-500/50'
    };

    container.innerHTML = insights.map(insight => `
        <div class="glass-effect bg-gradient-to-br ${insightColors[insight.type] || 'from-indigo-500/20 to-purple-500/20 border-indigo-500/50'} border rounded-xl p-5 hover:scale-[1.02] transition-transform">
            <div class="flex items-start gap-3 mb-3">
                <div class="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">
                    <i class="fas ${insight.icon} text-xl"></i>
                </div>
                <div class="flex-1">
                    <h4 class="font-bold text-lg mb-1">${escapeHtml(insight.title)}</h4>
                    <p class="text-sm text-gray-200 mb-2">${escapeHtml(insight.message)}</p>
                </div>
            </div>
            <div class="bg-black/30 rounded-lg p-3 mt-3">
                <p class="text-xs text-gray-300 flex items-start gap-2">
                    <i class="fas fa-lightbulb text-yellow-400 mt-0.5"></i>
                    <span><strong>Recommendation:</strong> ${escapeHtml(insight.recommendation)}</span>
                </p>
            </div>
        </div>
    `).join('');
}

// ============================================
// UPDATE STATISTICS
// ============================================
function updateStatistics() {
    if (!dashboardData) return;

    const { overview, performance } = dashboardData;

    // Update overview cards
    document.getElementById('totalAds').innerHTML = overview.total_ads;
    document.getElementById('totalViews').innerHTML = performance.total_views.toLocaleString();
    document.getElementById('totalContacts').innerHTML = performance.total_contacts;
    document.getElementById('totalFavorites').innerHTML = performance.current_favorites || 0;
    document.getElementById('totalCategories').innerHTML = Object.keys(dashboardData.categories).length;
}

// ============================================
// AI INSIGHTS
// ============================================
function updateAIInsights() {
    if (!dashboardData || !dashboardData.ai_insights) return;

    const container = document.getElementById('aiInsights');

    if (dashboardData.ai_insights.length === 0) {
        container.innerHTML = `
            <div class="col-span-full glass-effect rounded-xl p-6 text-center">
                <i class="fas fa-check-circle text-green-400 text-4xl mb-3"></i>
                <p class="text-lg font-semibold">All systems optimal!</p>
                <p class="text-sm text-gray-400">Your ads are performing well. Keep up the good work!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = dashboardData.ai_insights.map(insight => {
        const iconMap = {
            'success': 'fa-check-circle text-green-400',
            'warning': 'fa-exclamation-triangle text-yellow-400',
            'info': 'fa-info-circle text-blue-400',
            'error': 'fa-times-circle text-red-400'
        };

        const bgMap = {
            'success': 'from-green-500/20 to-green-600/10',
            'warning': 'from-yellow-500/20 to-yellow-600/10',
            'info': 'from-blue-500/20 to-blue-600/10',
            'error': 'from-red-500/20 to-red-600/10'
        };

        return `
            <div class="glass-effect rounded-xl p-4 border border-white/10 bg-gradient-to-br ${bgMap[insight.type]} slide-in">
                <div class="flex items-start gap-3">
                    <i class="fas ${iconMap[insight.type]} text-2xl mt-1"></i>
                    <div class="flex-1">
                        <h4 class="font-semibold mb-1">${escapeHtml(insight.title)}</h4>
                        <p class="text-sm text-gray-300 mb-2">${escapeHtml(insight.message)}</p>
                        <button class="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition">
                            ${escapeHtml(insight.action)} <i class="fas fa-arrow-right ml-1"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================
// RENDER CHARTS
// ============================================
function renderCharts() {
    if (!dashboardData) return;

    // Destroy existing charts
    Object.values(chartsInstances).forEach(chart => chart.destroy());
    chartsInstances = {};

    // Views Trend Chart
    const viewsCtx = document.getElementById('viewsTrendChart');
    if (viewsCtx) {
        chartsInstances.views = new Chart(viewsCtx, {
            type: 'line',
            data: {
                labels: getLast7Days(),
                datasets: [{
                    label: 'Views',
                    data: dashboardData.trends.views_trend,
                    borderColor: 'rgb(59, 130, 246)',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    x: {
                        ticks: { color: '#9ca3af' },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    // Contacts Trend Chart
    const contactsCtx = document.getElementById('contactsTrendChart');
    if (contactsCtx) {
        chartsInstances.contacts = new Chart(contactsCtx, {
            type: 'bar',
            data: {
                labels: getLast7Days(),
                datasets: [{
                    label: 'Contacts',
                    data: dashboardData.trends.contacts_trend,
                    backgroundColor: 'rgba(34, 197, 94, 0.5)',
                    borderColor: 'rgb(34, 197, 94)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { color: '#9ca3af' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    x: {
                        ticks: { color: '#9ca3af' },
                        grid: { display: false }
                    }
                }
            }
        });
    }

    // Category Performance Chart
    const categoryCtx = document.getElementById('categoryChart');
    if (categoryCtx && dashboardData.categories) {
        const categories = Object.keys(dashboardData.categories);
        const counts = categories.map(cat => dashboardData.categories[cat].count);

        chartsInstances.category = new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: categories.map(c => c.charAt(0).toUpperCase() + c.slice(1)),
                datasets: [{
                    data: counts,
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(168, 85, 247, 0.8)',
                        'rgba(251, 191, 36, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#9ca3af' }
                    }
                }
            }
        });
    }
}

function getLast7Days() {
    const days = [];
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        days.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    }
    return days;
}

// ============================================
// UPDATE REVENUE
// ============================================
function updateRevenue() {
    if (!dashboardData) return;

    document.getElementById('revenueTotal').textContent =
        '$' + dashboardData.revenue_estimate.total_value.toLocaleString();
    document.getElementById('revenueProjected').textContent =
        '$' + dashboardData.revenue_estimate.projected_monthly.toLocaleString();
}

// ============================================
// UPDATE TOP PERFORMERS
// ============================================
function updateTopPerformers() {
    if (!dashboardData || !dashboardData.top_performers) return;

    const container = document.getElementById('topAds');
    const topAds = dashboardData.top_performers.slice(0, 5);

    if (topAds.length === 0) {
        container.innerHTML = '<p class="text-gray-400 text-sm">No ads yet</p>';
        return;
    }

    container.innerHTML = topAds.map((ad, index) => `
        <div class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-700/50 transition cursor-pointer">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br ${
                index === 0 ? 'from-yellow-400 to-orange-500' :
                index === 1 ? 'from-gray-300 to-gray-400' :
                index === 2 ? 'from-orange-400 to-orange-600' :
                'from-blue-400 to-blue-600'
            } flex items-center justify-center font-bold text-sm flex-shrink-0">
                ${index + 1}
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-medium truncate">${escapeHtml(ad.title)}</p>
                <div class="flex gap-3 text-xs text-gray-400 mt-1">
                    <span><i class="fas fa-eye mr-1"></i>${ad.views}</span>
                    <span><i class="fas fa-phone mr-1"></i>${ad.contacts}</span>
                    <span class="capitalize"><i class="fas fa-tag mr-1"></i>${ad.category}</span>
                </div>
            </div>
            <i class="fas fa-arrow-right text-gray-400"></i>
        </div>
    `).join('');
}

// ============================================
// RENDER ADS
// ============================================
function renderAds(ads) {
    const container = document.getElementById('myAdsContainer');
    const loading = document.getElementById('adsLoading');
    const emptyState = document.getElementById('emptyState');

    loading.classList.add('hidden');

    if (ads.length === 0) {
        emptyState.classList.remove('hidden');
        return;
    }

    container.classList.remove('hidden');

    // Show latest 6 ads
    const latestAds = ads.slice(0, 6);

    container.innerHTML = latestAds.map(ad => {
        const isVideo = ad.media && /\.(mp4|mov|webm)$/i.test(ad.media);

        return `
            <div class="ad-card bg-slate-800/50 backdrop-blur rounded-xl overflow-hidden border border-white/10 hover:border-indigo-500/50 transition">
                <!-- Media -->
                <div class="relative h-48 bg-slate-700 overflow-hidden">
                    ${isVideo ?
                        `<video class="w-full h-full object-cover" muted>
                            <source src="${escapeHtml(ad.media)}">
                        </video>` :
                        `<img src="${escapeHtml(ad.media)}" alt="${escapeHtml(ad.title)}" class="w-full h-full object-cover">`
                    }
                    <div class="absolute top-2 right-2">
                        <span class="bg-black/70 backdrop-blur px-2 py-1 rounded text-xs">
                            ${escapeHtml(ad.category)}
                        </span>
                    </div>
                </div>

                <!-- Content -->
                <div class="p-4">
                    <h3 class="font-bold text-lg mb-2 truncate">${escapeHtml(ad.title)}</h3>
                    <p class="text-sm text-gray-400 mb-3 line-clamp-2">${escapeHtml(ad.description || '')}</p>

                    <div class="flex items-center justify-between text-xs text-gray-500 mb-3">
                        <span><i class="fas fa-clock mr-1"></i>${timeAgo(ad.timestamp)}</span>
                        <span><i class="fas fa-eye mr-1"></i>${Math.floor(Math.random() * 100 + 20)} views</span>
                    </div>

                    <!-- Actions -->
                    <div class="flex gap-2">
                        <button onclick="editAd('${ad.ad_id}')" class="flex-1 bg-indigo-600 hover:bg-indigo-700 py-2 rounded text-sm transition">
                            <i class="fas fa-edit mr-1"></i>Edit
                        </button>
                        <button onclick="deleteAd('${ad.ad_id}', '${escapeHtml(ad.title)}')" class="flex-1 bg-red-600 hover:bg-red-700 py-2 rounded text-sm transition">
                            <i class="fas fa-trash mr-1"></i>Delete
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================
// UPDATE ANALYTICS
// ============================================
function updateAnalytics(ads) {
    // Category breakdown
    const categoryCount = {};
    ads.forEach(ad => {
        categoryCount[ad.category] = (categoryCount[ad.category] || 0) + 1;
    });

    const categoryChart = document.getElementById('categoryChart');
    const totalAds = ads.length;

    if (totalAds === 0) {
        categoryChart.innerHTML = '<p class="text-gray-400 text-sm">No data available</p>';
    } else {
        categoryChart.innerHTML = Object.entries(categoryCount).map(([category, count]) => {
            const percentage = Math.round((count / totalAds) * 100);
            return `
                <div>
                    <div class="flex justify-between text-sm mb-1">
                        <span class="capitalize">${escapeHtml(category)}</span>
                        <span class="text-gray-400">${count} (${percentage}%)</span>
                    </div>
                    <div class="w-full bg-gray-700 rounded-full h-2">
                        <div class="bg-gradient-to-r from-indigo-500 to-purple-600 h-2 rounded-full transition-all" style="width: ${percentage}%"></div>
                    </div>
                </div>
            `;
        }).join('');
    }

    // Top performing ads
    const topAds = document.getElementById('topAds');
    const sortedAds = [...ads].sort((a, b) => b.timestamp - a.timestamp).slice(0, 3);

    if (sortedAds.length === 0) {
        topAds.innerHTML = '<p class="text-gray-400 text-sm">No ads yet</p>';
    } else {
        topAds.innerHTML = sortedAds.map((ad, index) => `
            <div class="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-700/50 transition">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-yellow-400 to-orange-500 flex items-center justify-center font-bold text-sm">
                    ${index + 1}
                </div>
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium truncate">${escapeHtml(ad.title)}</p>
                    <p class="text-xs text-gray-400">${Math.floor(Math.random() * 200 + 50)} views</p>
                </div>
            </div>
        `).join('');
    }

    // Recent activity
    const activityList = document.getElementById('activityList');
    activityList.innerHTML = ads.slice(0, 3).map(ad => `
        <div class="flex items-start gap-3 text-sm">
            <div class="w-2 h-2 bg-blue-400 rounded-full mt-2"></div>
            <div class="flex-1">
                <p class="text-gray-300">Posted ad: <strong>${escapeHtml(ad.title)}</strong></p>
                <p class="text-xs text-gray-500">${timeAgo(ad.timestamp)}</p>
            </div>
        </div>
    `).join('');
}

// ============================================
// AD ACTIONS
// ============================================
function editAd(adId) {
    // Redirect to edit page (to be implemented)
    alert('Edit functionality coming soon!\nAd ID: ' + adId);
    // window.location.href = `edit_ad.php?id=${adId}`;
}

function deleteAd(adId, title) {
    if (confirm(`Are you sure you want to delete "${title}"?\n\nThis action cannot be undone.`)) {
        // Call delete API (to be implemented)
        alert('Delete functionality coming soon!\nAd ID: ' + adId);
        // Implementation would go here
    }
}

function showError() {
    const container = document.getElementById('myAdsContainer');
    const loading = document.getElementById('adsLoading');

    loading.classList.add('hidden');
    container.classList.remove('hidden');
    container.innerHTML = `
        <div class="col-span-full bg-red-500/10 border border-red-500/50 rounded-xl p-8 text-center">
            <i class="fas fa-exclamation-triangle text-4xl text-red-400 mb-3"></i>
            <h3 class="text-xl font-bold mb-2">Failed to load ads</h3>
            <p class="text-gray-400 mb-4">There was an error loading your advertisements</p>
            <button onclick="location.reload()" class="bg-indigo-600 hover:bg-indigo-700 px-6 py-2 rounded-lg transition">
                Try Again
            </button>
        </div>
    `;
}

// ============================================
// UI INTERACTIONS
// ============================================

// User menu dropdown
document.getElementById('userMenuBtn').addEventListener('click', () => {
    const dropdown = document.getElementById('userMenuDropdown');
    dropdown.classList.toggle('hidden');
});

// Close dropdown when clicking outside
document.addEventListener('click', (e) => {
    const userMenu = document.getElementById('userMenuBtn');
    const dropdown = document.getElementById('userMenuDropdown');

    if (!userMenu.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.add('hidden');
    }
});

// Mobile menu toggle
document.getElementById('mobileMenuBtn').addEventListener('click', () => {
    const mobileMenu = document.getElementById('mobileMenu');
    mobileMenu.classList.toggle('hidden');
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        }
    });
});

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
});
</script>


</body>
</html>
