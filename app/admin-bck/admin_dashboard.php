<?php
/********************************************
 * SUPER ADMIN DASHBOARD - AdSphere
 * Ultimate platform control center with AI-powered management
 ********************************************/
session_start();

// Block unauthorized access - Check for admin authentication
if(!isset($_SESSION['admin_logged_in']) || $_SESSION['admin_logged_in'] !== true) {
    header("Location: login.php");
    exit();
}

// Check session timeout (1 hour)
$sessionTimeout = 3600; // 1 hour
if (isset($_SESSION['last_activity']) && (time() - $_SESSION['last_activity']) > $sessionTimeout) {
    session_unset();
    session_destroy();
    header("Location: login.php?timeout=1");
    exit();
}

// Update last activity timestamp
$_SESSION['last_activity'] = time();

// Get admin details from session
$adminUsername = $_SESSION['admin_username'] ?? 'Administrator';
$adminRole = $_SESSION['admin_role'] ?? 'super_admin';
$isSuperAdmin = ($adminRole === 'super_admin');

// Optional: Verify admin role for super admin access only
if (!$isSuperAdmin) {
    // Redirect non-super admins to their appropriate dashboard
    header("Location: /app/companies/home/dashboard.php");
    exit();
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Super Admin Control Center - AdSphere</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        /* Futuristic Animations */
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-15px); }
        }

        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.3); }
            50% { box-shadow: 0 0 35px rgba(99, 102, 241, 0.6); }
        }

        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes shimmer {
            0% { background-position: -1000px 0; }
            100% { background-position: 1000px 0; }
        }

        @keyframes scan {
            0%, 100% { transform: translateY(-100%); }
            50% { transform: translateY(100%); }
        }

        @keyframes glitch {
            0%, 100% { transform: translate(0); }
            20% { transform: translate(-2px, 2px); }
            40% { transform: translate(-2px, -2px); }
            60% { transform: translate(2px, 2px); }
            80% { transform: translate(2px, -2px); }
        }

        body {
            background: linear-gradient(135deg, #0a0a0a, #1a1a2e, #16213e, #0f3460, #0a0a0a);
            background-size: 400% 400%;
            animation: gradientShift 20s ease infinite;
        }

        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        }

        .stat-card {
            animation: float 6s ease-in-out infinite;
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
            height: 2px;
            background: linear-gradient(90deg, transparent, #6366f1, transparent);
            animation: scan 3s linear infinite;
        }

        .stat-card:hover {
            transform: translateY(-20px) scale(1.05);
            box-shadow: 0 20px 60px rgba(99, 102, 241, 0.6);
            border-color: rgba(99, 102, 241, 0.8);
        }

        .activity-item {
            animation: slideInRight 0.5s ease-out;
        }

        .live-indicator {
            animation: pulse-glow 2s ease-in-out infinite;
        }

        .shimmer-bg {
            background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.2), transparent);
            background-size: 1000px 100%;
            animation: shimmer 2s infinite;
        }

        .grid-pattern {
            background-image:
                linear-gradient(rgba(99, 102, 241, 0.05) 1px, transparent 1px),
                linear-gradient(90deg, rgba(99, 102, 241, 0.05) 1px, transparent 1px);
            background-size: 50px 50px;
        }

        .tab-btn {
            transition: all 0.3s ease;
            position: relative;
        }

        .tab-btn.active {
            background: linear-gradient(135deg, #6366f1, #8b5cf6);
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.5);
        }

        .tab-btn.active::before {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #6366f1, #8b5cf6, #6366f1);
            background-size: 200% 100%;
            animation: gradientShift 2s ease infinite;
        }

        .control-btn {
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .control-btn::before {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }

        .control-btn:hover::before {
            width: 300px;
            height: 300px;
        }

        .danger-zone {
            border: 2px solid rgba(239, 68, 68, 0.3);
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(220, 38, 38, 0.1));
        }

        .success-zone {
            border: 2px solid rgba(34, 197, 94, 0.3);
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(22, 163, 74, 0.1));
        }

        .neural-network {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            opacity: 0.1;
            z-index: 0;
        }

        .hologram-effect {
            position: relative;
        }

        .hologram-effect::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: repeating-linear-gradient(
                0deg,
                rgba(99, 102, 241, 0.03) 0px,
                transparent 2px,
                transparent 4px,
                rgba(99, 102, 241, 0.03) 6px
            );
            pointer-events: none;
            animation: scan 8s linear infinite;
        }
    </style>
</head>
<body class="text-white overflow-x-hidden relative">

<!-- Neural Network Background -->
<canvas class="neural-network" id="neuralCanvas"></canvas>

<!-- SUPER ADMIN COMMAND CENTER NAVBAR -->
<nav class="bg-black/60 backdrop-blur-2xl border-b-2 border-indigo-500/30 sticky top-0 z-50 hologram-effect">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-20">
            <!-- Left: Brand & System Status -->
            <div class="flex items-center gap-6">
                <div class="flex items-center gap-3 group cursor-pointer">
                    <div class="w-14 h-14 bg-gradient-to-br from-indigo-500 via-purple-600 to-pink-500 rounded-xl flex items-center justify-center relative overflow-hidden group-hover:scale-110 transition-transform">
                        <i class="fas fa-crown text-white text-2xl relative z-10"></i>
                        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent transform -skew-x-12 group-hover:animate-pulse"></div>
                    </div>
                    <div>
                        <h1 class="text-2xl font-black text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
                            SUPER ADMIN
                        </h1>
                        <p class="text-xs text-gray-400 font-mono">CONTROL CENTER v2.0</p>
                    </div>
                </div>

                <!-- System Status Indicators -->
                <div class="hidden lg:flex items-center gap-3 ml-6 pl-6 border-l border-white/10">
                    <div class="flex items-center gap-2">
                        <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                        <span class="text-xs text-gray-400">Systems Online</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <div class="w-2 h-2 bg-blue-400 rounded-full animate-pulse" style="animation-delay: 0.3s;"></div>
                        <span class="text-xs text-gray-400">AI Active</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <div class="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" style="animation-delay: 0.6s;"></div>
                        <span class="text-xs text-gray-400" id="onlineUsers">0 Online</span>
                    </div>
                </div>
            </div>

            <!-- Right: Quick Actions & User -->
            <div class="flex items-center gap-4">
                <!-- Quick Actions -->
                <div class="hidden md:flex items-center gap-2">
                    <button onclick="showNotifications()" class="relative w-10 h-10 bg-white/5 hover:bg-indigo-600/50 rounded-lg flex items-center justify-center transition group">
                        <i class="fas fa-bell text-gray-400 group-hover:text-white"></i>
                        <span class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-xs flex items-center justify-center font-bold">3</span>
                    </button>
                    <button onclick="emergencyStop()" class="w-10 h-10 bg-red-600/20 hover:bg-red-600 rounded-lg flex items-center justify-center transition group">
                        <i class="fas fa-exclamation-triangle text-red-400 group-hover:text-white"></i>
                    </button>
                    <button onclick="toggleAIAssistant()" class="w-10 h-10 bg-purple-600/20 hover:bg-purple-600 rounded-lg flex items-center justify-center transition group">
                        <i class="fas fa-robot text-purple-400 group-hover:text-white"></i>
                    </button>
                </div>

                <!-- User Profile -->
                <div class="flex items-center gap-3 bg-white/5 rounded-xl px-4 py-2 hover:bg-white/10 transition cursor-pointer" onclick="toggleUserMenu()">
                    <div class="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                        <i class="fas fa-user-shield text-white text-sm"></i>
                    </div>

                    <div class="hidden sm:block">
                        <p class="text-sm font-bold text-white">
                            <?= htmlspecialchars($adminUsername, ENT_QUOTES, 'UTF-8') ?>
                        </p>
                        <p class="text-xs text-gray-400">
                            <?= $isSuperAdmin ? 'Super Administrator' : 'Administrator' ?>
                        </p>
                    </div>




                    <i class="fas fa-chevron-down text-gray-400 text-xs"></i>

                </div>
            </div>
        </div>

        <!-- Quick Stats Bar -->
        <div class="flex items-center justify-between py-2 border-t border-white/5">
            <div class="flex items-center gap-6 text-xs">
                <div class="flex items-center gap-2">
                    <i class="fas fa-server text-green-400"></i>
                    <span class="text-gray-400">Server: <span class="text-white font-mono">99.9%</span></span>
                </div>
                <div class="flex items-center gap-2">
                    <i class="fas fa-database text-blue-400"></i>
                    <span class="text-gray-400">DB: <span class="text-white font-mono">Active</span></span>
                </div>
                <div class="flex items-center gap-2">
                    <i class="fas fa-shield-alt text-purple-400"></i>
                    <span class="text-gray-400">Security: <span class="text-white font-mono">Max</span></span>
                </div>
            </div>
            <div class="text-xs text-gray-500 font-mono">
                Last Update: <span id="systemTime">--:--:--</span>
            </div>
        </div>
    </div>
</nav>

<!-- MAIN CONTENT -->
<div class="min-h-screen py-8 grid-pattern relative z-10">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <!-- Header with Live Indicator -->
        <div class="text-center mb-8">
            <div class="inline-flex items-center gap-2 bg-indigo-600/20 border border-indigo-600/50 rounded-full px-6 py-2 mb-4 live-indicator">
                <div class="w-3 h-3 bg-green-400 rounded-full animate-ping"></div>
                <div class="w-3 h-3 bg-green-400 rounded-full absolute"></div>
                <span class="text-sm font-semibold ml-3">LIVE CONTROL CENTER • UPDATED REAL-TIME</span>
            </div>
            <h1 class="text-5xl font-bold mb-2 bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                Platform Command Center
            </h1>
            <p class="text-gray-300 text-lg">Complete administrative control • AI-Powered Management</p>
        </div>

        <!-- Navigation Tabs -->
        <div class="mb-8 overflow-x-auto">
            <div class="flex gap-2 min-w-max">
                <button onclick="switchTab('overview')" class="tab-btn active px-6 py-3 rounded-xl font-semibold flex items-center gap-2 bg-white/5 hover:bg-white/10 transition" id="tab-overview">
                    <i class="fas fa-chart-line"></i>
                    <span>Overview</span>
                </button>
                <button onclick="switchTab('users')" class="tab-btn px-6 py-3 rounded-xl font-semibold flex items-center gap-2 bg-white/5 hover:bg-white/10 transition" id="tab-users">
                    <i class="fas fa-users"></i>
                    <span>Users</span>
                </button>
                <button onclick="switchTab('companies')" class="tab-btn px-6 py-3 rounded-xl font-semibold flex items-center gap-2 bg-white/5 hover:bg-white/10 transition" id="tab-companies">
                    <i class="fas fa-building"></i>
                    <span>Companies</span>
                </button>
                <button onclick="switchTab('ads')" class="tab-btn px-6 py-3 rounded-xl font-semibold flex items-center gap-2 bg-white/5 hover:bg-white/10 transition" id="tab-ads">
                    <i class="fas fa-ad"></i>
                    <span>Ads Management</span>
                </button>
                <button onclick="switchTab('devices')" class="tab-btn px-6 py-3 rounded-xl font-semibold flex items-center gap-2 bg-white/5 hover:bg-white/10 transition" id="tab-devices">
                    <i class="fas fa-mobile-alt"></i>
                    <span>Devices & Security</span>
                </button>
                <button onclick="switchTab('rules')" class="tab-btn px-6 py-3 rounded-xl font-semibold flex items-center gap-2 bg-white/5 hover:bg-white/10 transition" id="tab-rules">
                    <i class="fas fa-gavel"></i>
                    <span>Platform Rules</span>
                </button>
                <button onclick="switchTab('settings')" class="tab-btn px-6 py-3 rounded-xl font-semibold flex items-center gap-2 bg-white/5 hover:bg-white/10 transition" id="tab-settings">
                    <i class="fas fa-cogs"></i>
                    <span>Settings</span>
                </button>
            </div>
        </div>

        <!-- Tab Content Container -->
        <div id="tabContent">
            <!-- OVERVIEW TAB -->
            <div id="content-overview" class="tab-content">

        <!-- Live Stats Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            <div class="glass-card rounded-2xl p-6 stat-card text-center" style="animation-delay: 0s;">
                <i class="fas fa-ad text-5xl text-indigo-400 mb-4"></i>
                <div class="text-5xl font-bold mb-2" id="totalAdsCounter">0</div>
                <div class="text-sm text-gray-300">Active Ads</div>
                <div class="text-xs text-gray-500 mt-2">Platform-wide</div>
            </div>
            <div class="glass-card rounded-2xl p-6 stat-card text-center" style="animation-delay: 0.2s;">
                <i class="fas fa-eye text-5xl text-purple-400 mb-4"></i>
                <div class="text-5xl font-bold mb-2" id="totalViewsCounter">0</div>
                <div class="text-sm text-gray-300">Total Views</div>
                <div class="text-xs text-gray-500 mt-2">All time</div>
            </div>
            <div class="glass-card rounded-2xl p-6 stat-card text-center" style="animation-delay: 0.4s;">
                <i class="fas fa-building text-5xl text-pink-400 mb-4"></i>
                <div class="text-5xl font-bold mb-2" id="activeUsersCounter">0</div>
                <div class="text-sm text-gray-300">Active Companies</div>
                <div class="text-xs text-gray-500 mt-2">With ads</div>
            </div>
            <div class="glass-card rounded-2xl p-6 stat-card text-center" style="animation-delay: 0.6s;">
                <i class="fas fa-fire text-5xl text-orange-400 mb-4"></i>
                <div class="text-5xl font-bold mb-2" id="engagementCounter">0%</div>
                <div class="text-sm text-gray-300">Engagement Rate</div>
                <div class="text-xs text-gray-500 mt-2">Platform average</div>
            </div>
        </div>

        <!-- Additional Stats Row -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6 mb-12">
            <div class="glass-card rounded-2xl p-6 text-center">
                <i class="fas fa-heart text-3xl text-red-400 mb-3"></i>
                <div class="text-3xl font-bold mb-2" id="totalFavoritesCounter">0</div>
                <div class="text-sm text-gray-300">Total Favorites</div>
                <div class="text-xs text-gray-500 mt-1">All ads</div>
            </div>
            <div class="glass-card rounded-2xl p-6 text-center">
                <i class="fas fa-thumbs-up text-3xl text-yellow-400 mb-3"></i>
                <div class="text-3xl font-bold mb-2" id="totalLikesCounter">0</div>
                <div class="text-sm text-gray-300">Total Likes</div>
                <div class="text-xs text-gray-500 mt-1">User engagement</div>
            </div>
            <div class="glass-card rounded-2xl p-6 text-center">
                <i class="fas fa-phone text-3xl text-blue-400 mb-3"></i>
                <div class="text-3xl font-bold mb-2" id="totalContactsCounter">0</div>
                <div class="text-sm text-gray-300">Total Contacts</div>
                <div class="text-xs text-gray-500 mt-1">Dealer interactions</div>
            </div>
            <div class="glass-card rounded-2xl p-6 text-center">
                <i class="fas fa-building text-3xl text-cyan-400 mb-3"></i>
                <div class="text-3xl font-bold mb-2" id="totalCompaniesCounter">0</div>
                <div class="text-sm text-gray-300">Companies</div>
                <div class="text-xs text-gray-500 mt-1">Active advertisers</div>
            </div>
            <div class="glass-card rounded-2xl p-6 text-center">
                <i class="fas fa-tags text-3xl text-green-400 mb-3"></i>
                <div class="text-3xl font-bold mb-2" id="totalCategoriesCounter">0</div>
                <div class="text-sm text-gray-300">Categories</div>
                <div class="text-xs text-gray-500 mt-1">Ad types</div>
            </div>
        </div>

        <!-- AD STATUS STATISTICS SECTION -->
        <div class="glass-card rounded-2xl p-6 mb-12">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold text-white flex items-center gap-3">
                    <i class="fas fa-chart-pie text-blue-400"></i>
                    Advertisement Status Overview
                </h2>
                <button onclick="refreshAdStats()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition text-sm">
                    <i class="fas fa-sync-alt mr-2"></i>Refresh Stats
                </button>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                <!-- Active Ads -->
                <div class="bg-green-600/20 border border-green-600/50 rounded-xl p-6 hover:bg-green-600/30 transition cursor-pointer" onclick="filterAdsByStatus('active')">
                    <div class="flex items-center justify-between mb-3">
                        <i class="fas fa-check-circle text-green-500 text-3xl"></i>
                        <span class="px-2 py-1 bg-green-600 rounded-full text-xs font-bold">LIVE</span>
                    </div>
                    <p class="text-4xl font-bold text-green-500 mb-1" id="activeAdsCount">-</p>
                    <p class="text-sm text-gray-300">Active Ads</p>
                    <p class="text-xs text-gray-500 mt-1">Currently running</p>
                </div>

                <!-- Inactive Ads -->
                <div class="bg-gray-600/20 border border-gray-600/50 rounded-xl p-6 hover:bg-gray-600/30 transition cursor-pointer" onclick="filterAdsByStatus('inactive')">
                    <div class="flex items-center justify-between mb-3">
                        <i class="fas fa-times-circle text-gray-400 text-3xl"></i>
                        <span class="px-2 py-1 bg-gray-600 rounded-full text-xs font-bold">OFF</span>
                    </div>
                    <p class="text-4xl font-bold text-gray-400 mb-1" id="inactiveAdsCount">-</p>
                    <p class="text-sm text-gray-300">Inactive Ads</p>
                    <p class="text-xs text-gray-500 mt-1">Deactivated/Removed</p>
                </div>

                <!-- Scheduled Ads -->
                <div class="bg-purple-600/20 border border-purple-600/50 rounded-xl p-6 hover:bg-purple-600/30 transition cursor-pointer" onclick="filterAdsByStatus('scheduled')">
                    <div class="flex items-center justify-center gap-2 mb-3">
                        <i class="fas fa-clock text-purple-400 text-3xl"></i>
                        <span class="px-2 py-1 bg-purple-600 rounded-full text-xs font-bold">PENDING</span>
                    </div>
                    <p class="text-4xl font-bold text-purple-400 mb-1" id="scheduledAdsCount">-</p>
                    <p class="text-sm text-gray-300">Scheduled Ads</p>
                    <p class="text-xs text-gray-500 mt-1">Future activation</p>
                </div>

                <!-- Expired Ads -->
                <div class="bg-orange-600/20 border border-orange-600/50 rounded-xl p-6 hover:bg-orange-600/30 transition cursor-pointer" onclick="filterAdsByStatus('expired')">
                    <div class="flex items-center justify-center gap-2 mb-3">
                        <i class="fas fa-hourglass-end text-orange-400 text-3xl"></i>
                        <span class="px-2 py-1 bg-orange-600 rounded-full text-xs font-bold">ENDED</span>
                    </div>
                    <p class="text-4xl font-bold text-orange-400 mb-1" id="expiredAdsCount">-</p>
                    <p class="text-sm text-gray-300">Expired Ads</p>
                    <p class="text-xs text-gray-500 mt-1">Past end date</p>
                </div>

                <!-- Total Ads -->
                <div class="bg-indigo-600/20 border border-indigo-600/50 rounded-xl p-6 hover:bg-indigo-600/30 transition">
                    <div class="flex items-center justify-center gap-2 mb-3">
                        <i class="fas fa-database text-indigo-400 text-3xl"></i>
                    </div>
                    <p class="text-4xl font-bold text-indigo-400 mb-1" id="totalAdsCount">-</p>
                    <p class="text-sm text-gray-300">Total Ads</p>
                    <p class="text-xs text-gray-500 mt-1">All time</p>
                </div>
            </div>

            <!-- Status Breakdown Chart -->
            <div class="mt-6 bg-black/30 rounded-xl p-4">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-bold text-white">Status Distribution</h3>
                    <div class="text-sm text-gray-400">
                        <span id="adStatsPercentage">-</span>% Active Rate
                    </div>
                </div>
                <div class="grid grid-cols-1 gap-2">
                    <!-- Active Bar -->
                    <div class="flex items-center gap-3">
                        <span class="text-xs text-gray-400 w-20">Active</span>
                        <div class="flex-1 bg-gray-700 rounded-full h-6 overflow-hidden">
                            <div id="activeBar" class="bg-green-500 h-full transition-all duration-500" style="width: 0%"></div>
                        </div>
                        <span class="text-xs text-gray-400 w-12 text-right" id="activeBarText">0</span>
                    </div>
                    <!-- Inactive Bar -->
                    <div class="flex items-center gap-3">
                        <span class="text-xs text-gray-400 w-20">Inactive</span>
                        <div class="flex-1 bg-gray-700 rounded-full h-6 overflow-hidden">
                            <div id="inactiveBar" class="bg-gray-500 h-full transition-all duration-500" style="width: 0%"></div>
                        </div>
                        <span class="text-xs text-gray-400 w-12 text-right" id="inactiveBarText">0</span>
                    </div>
                    <!-- Scheduled Bar -->
                    <div class="flex items-center gap-3">
                        <span class="text-xs text-gray-400 w-20">Scheduled</span>
                        <div class="flex-1 bg-gray-700 rounded-full h-6 overflow-hidden">
                            <div id="scheduledBar" class="bg-purple-500 h-full transition-all duration-500" style="width: 0%"></div>
                        </div>
                        <span class="text-xs text-gray-400 w-12 text-right" id="scheduledBarText">0</span>
                    </div>
                    <!-- Expired Bar -->
                    <div class="flex items-center gap-3">
                        <span class="text-xs text-gray-400 w-20">Expired</span>
                        <div class="flex-1 bg-gray-700 rounded-full h-6 overflow-hidden">
                            <div id="expiredBar" class="bg-orange-500 h-full transition-all duration-500" style="width: 0%"></div>
                        </div>
                        <span class="text-xs text-gray-400 w-12 text-right" id="expiredBarText">0</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- CONTENT MODERATION ALERTS SECTION -->
        <div class="glass-card rounded-2xl p-6 mb-12">
            <div class="flex items-center justify-between mb-6">
                <h2 class="text-2xl font-bold text-white flex items-center gap-3">
                    <i class="fas fa-shield-alt text-red-500"></i>
                    Content Moderation Alerts
                    <span id="pendingCount" class="px-3 py-1 bg-red-600 rounded-full text-sm">0</span>
                </h2>
                <div class="flex gap-2">
                    <button onclick="refreshViolations()" class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition text-sm">
                        <i class="fas fa-sync-alt mr-2"></i>Refresh
                    </button>
                    <button onclick="runNewScan()" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition text-sm">
                        <i class="fas fa-radar mr-2"></i>Run Scan
                    </button>
                    <a href="/app/admin/moderation_dashboard.php" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg transition text-sm">
                        <i class="fas fa-external-link-alt mr-2"></i>Full Dashboard
                    </a>
                </div>
            </div>

            <!-- Violation Stats -->
            <div class="grid grid-cols-4 gap-4 mb-6">
                <div class="bg-red-600/20 border border-red-600/50 rounded-lg p-4 text-center">
                    <div class="flex items-center justify-center gap-2 mb-2">
                        <i class="fas fa-skull-crossbones text-red-500 text-2xl"></i>
                    </div>
                    <p class="text-3xl font-bold text-red-500" id="criticalViolations">-</p>
                    <p class="text-xs text-gray-400 mt-1">Critical</p>
                </div>
                <div class="bg-orange-600/20 border border-orange-600/50 rounded-lg p-4 text-center">
                    <div class="flex items-center justify-center gap-2 mb-2">
                        <i class="fas fa-exclamation-triangle text-orange-500 text-2xl"></i>
                    </div>
                    <p class="text-3xl font-bold text-orange-500" id="highViolations">-</p>
                    <p class="text-xs text-gray-400 mt-1">High Risk</p>
                </div>
                <div class="bg-yellow-600/20 border border-yellow-600/50 rounded-lg p-4 text-center">
                    <div class="flex items-center justify-center gap-2 mb-2">
                        <i class="fas fa-exclamation-circle text-yellow-500 text-2xl"></i>
                    </div>
                    <p class="text-3xl font-bold text-yellow-500" id="mediumViolations">-</p>
                    <p class="text-xs text-gray-400 mt-1">Medium</p>
                </div>
                <div class="bg-green-600/20 border border-green-600/50 rounded-lg p-4 text-center">
                    <div class="flex items-center justify-center gap-2 mb-2">
                        <i class="fas fa-check-circle text-green-500 text-2xl"></i>
                    </div>
                    <p class="text-3xl font-bold text-green-500" id="resolvedViolations">-</p>
                    <p class="text-xs text-gray-400 mt-1">Resolved</p>
                </div>
            </div>

            <!-- Violations List -->
            <div id="violationsList" class="space-y-3 max-h-96 overflow-y-auto">
                <div class="text-center py-8 text-gray-400">
                    <i class="fas fa-spinner fa-spin text-4xl mb-3"></i>
                    <p>Loading violations...</p>
                </div>
            </div>
        </div>

        <!-- Live Activity Feed & Trending -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-12">
            <!-- Activity Stream -->
            <div class="lg:col-span-2 glass-card rounded-2xl p-6">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-2xl font-bold flex items-center gap-2">
                        <i class="fas fa-chart-line text-indigo-400"></i>
                        Live Activity Feed
                    </h3>
                    <button onclick="refreshActivity()" class="text-indigo-400 hover:text-indigo-300 transition">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </div>
                <div class="flex items-center gap-2 text-sm text-gray-400 mb-4">
                    <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span id="lastUpdate">Updated just now</span>
                </div>
                <div id="activityFeed" class="space-y-3 max-h-96 overflow-y-auto">
                    <div class="shimmer-bg h-16 rounded-lg"></div>
                    <div class="shimmer-bg h-16 rounded-lg"></div>
                    <div class="shimmer-bg h-16 rounded-lg"></div>
                </div>
            </div>

            <!-- Trending Stats -->
            <div class="glass-card rounded-2xl p-6">
                <h3 class="text-2xl font-bold mb-4 flex items-center gap-2">
                    <i class="fas fa-fire text-orange-400"></i>
                    Trending Now
                </h3>
                <div class="space-y-4">
                    <div class="bg-gradient-to-r from-indigo-600/20 to-transparent p-4 rounded-xl border border-indigo-600/30">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm text-gray-400">Most Viewed</span>
                            <i class="fas fa-fire text-orange-400"></i>
                        </div>
                        <div class="text-2xl font-bold" id="topAdViews">0</div>
                        <div class="text-xs text-gray-400 mt-1" id="topAdTitle">Loading...</div>
                    </div>

                    <div class="bg-gradient-to-r from-purple-600/20 to-transparent p-4 rounded-xl border border-purple-600/30">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm text-gray-400">Top Category</span>
                            <i class="fas fa-tag text-purple-400"></i>
                        </div>
                        <div class="text-2xl font-bold" id="topCategory">-</div>
                        <div class="text-xs text-gray-400 mt-1" id="topCategoryCount">0 ads</div>
                    </div>

                    <div class="bg-gradient-to-r from-pink-600/20 to-transparent p-4 rounded-xl border border-pink-600/30">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm text-gray-400">Total Engagement</span>
                            <i class="fas fa-heart text-pink-400"></i>
                        </div>
                        <div class="text-2xl font-bold" id="totalEngagement">0</div>
                        <div class="text-xs text-gray-400 mt-1">Likes + Favorites</div>
                    </div>

                    <div class="bg-gradient-to-r from-green-600/20 to-transparent p-4 rounded-xl border border-green-600/30">
                        <div class="flex items-center justify-between mb-2">
                            <span class="text-sm text-gray-400">Avg Views/Ad</span>
                            <i class="fas fa-chart-bar text-green-400"></i>
                        </div>
                        <div class="text-2xl font-bold" id="avgViews">0</div>
                        <div class="text-xs text-gray-400 mt-1">Per advertisement</div>
                    </div>
                </div>
            </div>
        </div>

                <!-- Charts Section -->
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                    <!-- Views Over Time Chart -->
                    <div class="glass-card rounded-2xl p-6">
                        <h3 class="text-xl font-bold mb-4 flex items-center gap-2">
                            <i class="fas fa-chart-area text-blue-400"></i>
                            Views Distribution
                        </h3>
                        <div class="h-64">
                            <canvas id="viewsChart"></canvas>
                        </div>
                    </div>

                    <!-- Category Distribution Chart -->
                    <div class="glass-card rounded-2xl p-6">
                        <h3 class="text-xl font-bold mb-4 flex items-center gap-2">
                            <i class="fas fa-chart-pie text-purple-400"></i>
                            Category Distribution
                        </h3>
                        <div class="h-64">
                            <canvas id="categoryChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>

            <!-- USERS MANAGEMENT TAB -->
            <div id="content-users" class="tab-content hidden">
                <div class="glass-card rounded-2xl p-6 mb-6">
                    <div class="flex items-center justify-between mb-6">
                        <h2 class="text-2xl font-bold flex items-center gap-2">
                            <i class="fas fa-users-cog text-indigo-400"></i>
                            User Management
                        </h2>
                        <div class="flex items-center gap-2">
                            <input type="text" placeholder="Search users..." class="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500">
                            <button onclick="addNewUser()" class="control-btn px-4 py-2 bg-indigo-600 hover:bg-indigo-700 rounded-lg font-semibold">
                                <i class="fas fa-plus mr-2"></i>Add User
                            </button>
                        </div>
                    </div>

                    <!-- User Stats -->
                    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                        <div class="bg-gradient-to-br from-blue-600/20 to-blue-800/20 p-4 rounded-xl border border-blue-500/30">
                            <i class="fas fa-user-check text-blue-400 text-2xl mb-2"></i>
                            <div class="text-2xl font-bold" id="activeUsersCount">0</div>
                            <div class="text-sm text-gray-400">Active Users</div>
                        </div>
                        <div class="bg-gradient-to-br from-yellow-600/20 to-yellow-800/20 p-4 rounded-xl border border-yellow-500/30">
                            <i class="fas fa-user-clock text-yellow-400 text-2xl mb-2"></i>
                            <div class="text-2xl font-bold" id="pendingUsersCount">0</div>
                            <div class="text-sm text-gray-400">Pending Approval</div>
                        </div>
                        <div class="bg-gradient-to-br from-red-600/20 to-red-800/20 p-4 rounded-xl border border-red-500/30">
                            <i class="fas fa-user-slash text-red-400 text-2xl mb-2"></i>
                            <div class="text-2xl font-bold" id="blockedUsersCount">0</div>
                            <div class="text-sm text-gray-400">Blocked Users</div>
                        </div>
                        <div class="bg-gradient-to-br from-green-600/20 to-green-800/20 p-4 rounded-xl border border-green-500/30">
                            <i class="fas fa-user-friends text-green-400 text-2xl mb-2"></i>
                            <div class="text-2xl font-bold" id="onlineNowCount">0</div>
                            <div class="text-sm text-gray-400">Online Now</div>
                        </div>
                    </div>

                    <!-- Users Table -->
                    <div class="overflow-x-auto">
                        <table class="w-full">
                            <thead>
                                <tr class="border-b border-white/10">
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">User</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Email</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Role</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Status</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Last Active</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Actions</th>
                                </tr>
                            </thead>
                            <tbody id="usersTableBody">
                                <tr class="border-b border-white/5 hover:bg-white/5">
                                    <td colspan="6" class="py-8 text-center text-gray-500">Loading users...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- COMPANIES CONTROL TAB -->
            <div id="content-companies" class="tab-content hidden">
                <div class="glass-card rounded-2xl p-6 mb-6">
                    <div class="flex items-center justify-between mb-6">
                        <h2 class="text-2xl font-bold flex items-center gap-2">
                            <i class="fas fa-building text-purple-400"></i>
                            Companies Management
                        </h2>
                        <div class="flex items-center gap-2">
                            <select class="px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-purple-500">
                                <option value="">All Status</option>
                                <option value="active">Active</option>
                                <option value="suspended">Suspended</option>
                                <option value="pending">Pending</option>
                            </select>
                            <button onclick="approveCompany()" class="control-btn px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-semibold">
                                <i class="fas fa-check-circle mr-2"></i>Approve Selected
                            </button>
                        </div>
                    </div>

                    <!-- Company Stats -->
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                        <div class="bg-gradient-to-br from-purple-600/20 to-purple-800/20 p-4 rounded-xl border border-purple-500/30 hover:border-purple-400/50 transition">
                            <i class="fas fa-building text-purple-400 text-3xl mb-2"></i>
                            <div class="text-3xl font-bold" id="totalCompaniesStats">0</div>
                            <div class="text-sm text-gray-400">Total Companies</div>
                            <div class="text-xs text-gray-500 mt-1">All registered</div>
                        </div>
                        <div class="bg-gradient-to-br from-green-600/20 to-green-800/20 p-4 rounded-xl border border-green-500/30 hover:border-green-400/50 transition">
                            <i class="fas fa-check-circle text-green-400 text-3xl mb-2"></i>
                            <div class="text-3xl font-bold" id="verifiedCompaniesCount">0</div>
                            <div class="text-sm text-gray-400">Verified</div>
                            <div class="text-xs text-gray-500 mt-1">Active & approved</div>
                        </div>
                        <div class="bg-gradient-to-br from-yellow-600/20 to-yellow-800/20 p-4 rounded-xl border border-yellow-500/30 hover:border-yellow-400/50 transition">
                            <i class="fas fa-ban text-yellow-400 text-3xl mb-2"></i>
                            <div class="text-3xl font-bold" id="suspendedCompaniesCount">0</div>
                            <div class="text-sm text-gray-400">Suspended</div>
                            <div class="text-xs text-gray-500 mt-1">Temporarily inactive</div>
                        </div>
                        <div class="bg-gradient-to-br from-red-600/20 to-red-800/20 p-4 rounded-xl border border-red-500/30 hover:border-red-400/50 transition">
                            <i class="fas fa-lock text-red-400 text-3xl mb-2"></i>
                            <div class="text-3xl font-bold" id="blockedCompaniesCount">0</div>
                            <div class="text-sm text-gray-400">Blocked</div>
                            <div class="text-xs text-gray-500 mt-1">Permanently banned</div>
                        </div>
                    </div>

                    <!-- Companies Table -->
                    <div class="overflow-x-auto">
                        <table class="w-full">
                            <thead>
                                <tr class="border-b border-white/10">
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Company</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Ads</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Views</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Status</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Joined</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Actions</th>
                                </tr>
                            </thead>
                            <tbody id="companiesTableBody">
                                <tr class="border-b border-white/5 hover:bg-white/5">
                                    <td colspan="6" class="py-8 text-center text-gray-500">Loading companies...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- ADS MANAGEMENT TAB -->
            <div id="content-ads" class="tab-content hidden">
                <div class="glass-card rounded-2xl p-6 mb-6">
                    <div class="flex items-center justify-between mb-6">
                        <h2 class="text-2xl font-bold flex items-center gap-2">
                            <i class="fas fa-ad text-cyan-400"></i>
                            Ads Management & Control
                        </h2>
                        <div class="flex items-center gap-2">
                            <button onclick="flaggedAds()" class="control-btn px-4 py-2 bg-red-600/20 hover:bg-red-600 rounded-lg font-semibold border border-red-500/30">
                                <i class="fas fa-flag mr-2"></i>Flagged (<span id="flaggedCount">0</span>)
                            </button>
                            <button onclick="bulkApprove()" class="control-btn px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-semibold">
                                <i class="fas fa-check-double mr-2"></i>Bulk Approve
                            </button>
                        </div>
                    </div>

                    <!-- Ads Stats -->
                    <div class="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
                        <div class="bg-gradient-to-br from-cyan-600/20 to-cyan-800/20 p-4 rounded-xl border border-cyan-500/30">
                            <i class="fas fa-ad text-cyan-400 text-2xl mb-2"></i>
                            <div class="text-2xl font-bold" id="totalAdsStats">0</div>
                            <div class="text-sm text-gray-400">Total Ads</div>
                        </div>
                        <div class="bg-gradient-to-br from-green-600/20 to-green-800/20 p-4 rounded-xl border border-green-500/30">
                            <i class="fas fa-check text-green-400 text-2xl mb-2"></i>
                            <div class="text-2xl font-bold" id="activeAdsStats">0</div>
                            <div class="text-sm text-gray-400">Active</div>
                        </div>
                        <div class="bg-gradient-to-br from-yellow-600/20 to-yellow-800/20 p-4 rounded-xl border border-yellow-500/30">
                            <i class="fas fa-clock text-yellow-400 text-2xl mb-2"></i>
                            <div class="text-2xl font-bold" id="pendingAdsStats">0</div>
                            <div class="text-sm text-gray-400">Pending</div>
                        </div>
                        <div class="bg-gradient-to-br from-red-600/20 to-red-800/20 p-4 rounded-xl border border-red-500/30">
                            <i class="fas fa-ban text-red-400 text-2xl mb-2"></i>
                            <div class="text-2xl font-bold" id="rejectedAdsStats">0</div>
                            <div class="text-sm text-gray-400">Rejected</div>
                        </div>
                        <div class="bg-gradient-to-br from-purple-600/20 to-purple-800/20 p-4 rounded-xl border border-purple-500/30">
                            <i class="fas fa-flag text-purple-400 text-2xl mb-2"></i>
                            <div class="text-2xl font-bold" id="reportedAdsStats">0</div>
                            <div class="text-sm text-gray-400">Reported</div>
                        </div>
                    </div>

                    <!-- Ads Table -->
                    <div class="overflow-x-auto">
                        <table class="w-full">
                            <thead>
                                <tr class="border-b border-white/10">
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">
                                        <input type="checkbox" class="rounded">
                                    </th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Ad Title</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Company</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Category</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Views</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Status</th>
                                    <th class="text-left py-3 px-4 text-sm font-semibold text-gray-400">Actions</th>
                                </tr>
                            </thead>
                            <tbody id="adsTableBody">
                                <tr class="border-b border-white/5 hover:bg-white/5">
                                    <td colspan="7" class="py-8 text-center text-gray-500">Loading ads...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- DEVICES & SECURITY TAB -->
            <div id="content-devices" class="tab-content hidden">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                    <!-- Device Tracking -->
                    <div class="glass-card rounded-2xl p-6">
                        <h3 class="text-xl font-bold mb-4 flex items-center gap-2">
                            <i class="fas fa-mobile-alt text-green-400"></i>
                            Device Tracking
                        </h3>
                        <div class="space-y-3">
                            <div class="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                                <div>
                                    <p class="font-semibold">Total Devices Tracked</p>
                                    <p class="text-sm text-gray-400">Unique device fingerprints</p>
                                </div>
                                <div class="text-2xl font-bold text-green-400" id="totalDevices">0</div>
                            </div>
                            <div class="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                                <div>
                                    <p class="font-semibold">Mobile Devices</p>
                                    <p class="text-sm text-gray-400">Smartphones & tablets</p>
                                </div>
                                <div class="text-2xl font-bold text-blue-400" id="mobileDevices">0</div>
                            </div>
                            <div class="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                                <div>
                                    <p class="font-semibold">Desktop Devices</p>
                                    <p class="text-sm text-gray-400">Computers & laptops</p>
                                </div>
                                <div class="text-2xl font-bold text-purple-400" id="desktopDevices">0</div>
                            </div>
                        </div>
                    </div>

                    <!-- Security Controls -->
                    <div class="glass-card rounded-2xl p-6">
                        <h3 class="text-xl font-bold mb-4 flex items-center gap-2">
                            <i class="fas fa-shield-alt text-red-400"></i>
                            Security Controls
                        </h3>
                        <div class="space-y-4">
                            <div class="success-zone rounded-xl p-4">
                                <div class="flex items-center justify-between mb-2">
                                    <span class="font-semibold">Two-Factor Authentication</span>
                                    <label class="relative inline-flex items-center cursor-pointer">
                                        <input type="checkbox" checked class="sr-only peer">
                                        <div class="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-green-600"></div>
                                    </label>
                                </div>
                                <p class="text-xs text-gray-400">Require 2FA for all admin accounts</p>
                            </div>

                            <div class="glass-card rounded-xl p-4 border border-white/10">
                                <div class="flex items-center justify-between mb-2">
                                    <span class="font-semibold">IP Whitelist</span>
                                    <button onclick="manageIPWhitelist()" class="text-indigo-400 hover:text-indigo-300 text-sm">
                                        <i class="fas fa-cog mr-1"></i>Configure
                                    </button>
                                </div>
                                <p class="text-xs text-gray-400">Restrict access to specific IP addresses</p>
                            </div>

                            <div class="danger-zone rounded-xl p-4">
                                <div class="flex items-center justify-between mb-2">
                                    <span class="font-semibold">Suspicious Activity Alert</span>
                                    <label class="relative inline-flex items-center cursor-pointer">
                                        <input type="checkbox" checked class="sr-only peer">
                                        <div class="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
                                    </label>
                                </div>
                                <p class="text-xs text-gray-400">Auto-block suspicious login attempts</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Recent Devices Table -->
                <div class="glass-card rounded-2xl p-6">
                    <h3 class="text-xl font-bold mb-4">Recent Device Activity</h3>
                    <div class="overflow-x-auto">
                        <table class="w-full text-sm">
                            <thead>
                                <tr class="border-b border-white/10">
                                    <th class="text-left py-3 px-4 font-semibold text-gray-400">Device</th>
                                    <th class="text-left py-3 px-4 font-semibold text-gray-400">User</th>
                                    <th class="text-left py-3 px-4 font-semibold text-gray-400">Location</th>
                                    <th class="text-left py-3 px-4 font-semibold text-gray-400">Last Seen</th>
                                    <th class="text-left py-3 px-4 font-semibold text-gray-400">Actions</th>
                                </tr>
                            </thead>
                            <tbody id="devicesTableBody">
                                <tr class="border-b border-white/5">
                                    <td colspan="5" class="py-8 text-center text-gray-500">Loading devices...</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- PLATFORM RULES TAB -->
            <div id="content-rules" class="tab-content hidden">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- Ad Posting Rules -->
                    <div class="glass-card rounded-2xl p-6">
                        <h3 class="text-xl font-bold mb-4 flex items-center gap-2">
                            <i class="fas fa-gavel text-yellow-400"></i>
                            Ad Posting Rules
                        </h3>
                        <div class="space-y-4">
                            <div class="glass-card rounded-xl p-4 border border-white/10">
                                <label class="block mb-2 font-semibold">Minimum Ad Description Length</label>
                                <input type="number" value="50" class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-yellow-500">
                                <p class="text-xs text-gray-500 mt-1">Characters required</p>
                            </div>

                            <div class="glass-card rounded-xl p-4 border border-white/10">
                                <label class="block mb-2 font-semibold">Max Ads Per Company (Daily)</label>
                                <input type="number" value="10" class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-yellow-500">
                                <p class="text-xs text-gray-500 mt-1">Limit daily ad submissions</p>
                            </div>

                            <div class="glass-card rounded-xl p-4 border border-white/10">
                                <label class="flex items-center justify-between mb-2">
                                    <span class="font-semibold">Require Admin Approval</span>
                                    <input type="checkbox" checked class="rounded">
                                </label>
                                <p class="text-xs text-gray-500">All ads must be approved before going live</p>
                            </div>

                            <div class="glass-card rounded-xl p-4 border border-white/10">
                                <label class="flex items-center justify-between mb-2">
                                    <span class="font-semibold">Auto-Detect Prohibited Content</span>
                                    <input type="checkbox" checked class="rounded">
                                </label>
                                <p class="text-xs text-gray-500">Use AI to flag inappropriate content</p>
                            </div>
                        </div>
                    </div>

                    <!-- Content Moderation -->
                    <div class="glass-card rounded-2xl p-6">
                        <h3 class="text-xl font-bold mb-4 flex items-center gap-2">
                            <i class="fas fa-filter text-red-400"></i>
                            Content Moderation
                        </h3>
                        <div class="space-y-4">
                            <div class="glass-card rounded-xl p-4 border border-white/10">
                                <label class="block mb-2 font-semibold">Prohibited Keywords</label>
                                <textarea rows="3" class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-red-500" placeholder="Enter keywords separated by commas..."></textarea>
                                <p class="text-xs text-gray-500 mt-1">Ads containing these words will be auto-flagged</p>
                            </div>

                            <div class="glass-card rounded-xl p-4 border border-white/10">
                                <label class="block mb-2 font-semibold">Allowed Categories</label>
                                <div class="space-y-2">
                                    <label class="flex items-center gap-2">
                                        <input type="checkbox" checked class="rounded">
                                        <span class="text-sm">Electronics</span>
                                    </label>
                                    <label class="flex items-center gap-2">
                                        <input type="checkbox" checked class="rounded">
                                        <span class="text-sm">Real Estate</span>
                                    </label>
                                    <label class="flex items-center gap-2">
                                        <input type="checkbox" checked class="rounded">
                                        <span class="text-sm">Vehicles</span>
                                    </label>
                                    <label class="flex items-center gap-2">
                                        <input type="checkbox" checked class="rounded">
                                        <span class="text-sm">Services</span>
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Save Rules Button -->
                    <div class="lg:col-span-2">
                        <div class="success-zone rounded-xl p-6 text-center">
                            <button onclick="saveRules()" class="control-btn px-8 py-3 bg-green-600 hover:bg-green-700 rounded-xl font-bold text-lg">
                                <i class="fas fa-save mr-2"></i>Save All Rules
                            </button>
                            <p class="text-sm text-gray-400 mt-2">Changes will take effect immediately</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- SYSTEM SETTINGS TAB -->
            <div id="content-settings" class="tab-content hidden">
                <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <!-- General Settings -->
                    <div class="glass-card rounded-2xl p-6">
                        <h3 class="text-xl font-bold mb-4 flex items-center gap-2">
                            <i class="fas fa-cogs text-gray-400"></i>
                            General Settings
                        </h3>
                        <div class="space-y-4">
                            <div class="glass-card rounded-xl p-4 border border-white/10">
                                <label class="block mb-2 font-semibold">Platform Name</label>
                                <input type="text" value="AdSphere" class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-indigo-500">
                            </div>

                            <div class="glass-card rounded-xl p-4 border border-white/10">
                                <label class="block mb-2 font-semibold">Support Email</label>
                                <input type="email" value="support@adsphere.com" class="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:border-indigo-500">
                            </div>

                            <div class="glass-card rounded-xl p-4 border border-white/10">
                                <label class="flex items-center justify-between mb-2">
                                    <span class="font-semibold">Maintenance Mode</span>
                                    <input type="checkbox" class="rounded">
                                </label>
                                <p class="text-xs text-gray-500">Take platform offline for maintenance</p>
                            </div>
                        </div>
                    </div>

                    <!-- Danger Zone -->
                    <div class="glass-card rounded-2xl p-6">
                        <h3 class="text-xl font-bold mb-4 flex items-center gap-2">
                            <i class="fas fa-exclamation-triangle text-red-400"></i>
                            Danger Zone
                        </h3>
                        <div class="space-y-4">
                            <div class="danger-zone rounded-xl p-4">
                                <button onclick="clearCache()" class="control-btn w-full px-4 py-3 bg-red-600/20 hover:bg-red-600 rounded-lg font-semibold border border-red-500/50">
                                    <i class="fas fa-trash mr-2"></i>Clear All Cache
                                </button>
                                <p class="text-xs text-gray-400 mt-2">Remove all cached data</p>
                            </div>

                            <div class="danger-zone rounded-xl p-4">
                                <button onclick="resetAnalytics()" class="control-btn w-full px-4 py-3 bg-red-600/20 hover:bg-red-600 rounded-lg font-semibold border border-red-500/50">
                                    <i class="fas fa-chart-line mr-2"></i>Reset Analytics
                                </button>
                                <p class="text-xs text-gray-400 mt-2">Clear all analytics data</p>
                            </div>

                            <div class="danger-zone rounded-xl p-4">
                                <button onclick="confirmPlatformReset()" class="control-btn w-full px-4 py-3 bg-red-600 hover:bg-red-700 rounded-lg font-bold border border-red-500">
                                    <i class="fas fa-exclamation-circle mr-2"></i>Factory Reset Platform
                                </button>
                                <p class="text-xs text-gray-400 mt-2">⚠️ This action cannot be undone!</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

    </div>
</div>

<!-- Live Updates JavaScript -->
<script>
// ============================================
// LIVE UPDATES & REAL-TIME ANALYTICS
// ============================================

let updateInterval;
let lastActivityUpdate = Date.now();
let viewsChart = null;
let categoryChart = null;

// Animated Counter Function
function animateCounter(element, target, duration = 2000, suffix = '') {
    if (!element) return;
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            element.textContent = Math.round(target).toLocaleString() + suffix;
            clearInterval(timer);
        } else {
            element.textContent = Math.round(current).toLocaleString() + suffix;
        }
    }, 16);
}

// Load Live Statistics
async function loadLiveStats() {
    console.log('📊 Loading live stats...');
    try {
        // Parallel API calls like my_ads.php does
        const [adsRes, analyticsRes] = await Promise.all([
            fetch('/app/api/get_ads.php'),
            fetch('/app/api/get_analytics.php')
        ]);

        const adsData = await adsRes.json();
        const analyticsData = await analyticsRes.json();

        console.log('📥 Ads API Response:', adsData);
        console.log('📥 Analytics API Response:', analyticsData);
        console.log('📈 Total ads in response:', adsData?.ads?.length);

        if (adsData && adsData.ads) {
            let allAds = adsData.ads || [];

            console.log('📦 Raw ads data sample:', allAds[0]);

            // Merge analytics data with ads (like my_ads.php does)
            if (analyticsData && analyticsData.success && analyticsData.analytics) {
                console.log('🔗 Merging analytics data with ads...');
                allAds = allAds.map(ad => ({
                    ...ad,
                    analytics: analyticsData.analytics[ad.ad_id] || {
                        total_views: ad.views || 0,
                        total_clicks: 0,
                        total_contacts: ad.contacts || 0,
                        current_favorites: ad.favorites || 0,
                        total_likes: ad.likes || 0
                    }
                }));
                console.log('✅ Analytics merged. Sample ad:', allAds[0]);
            } else {
                console.warn('⚠️ Analytics API failed or returned no data, using ad properties directly');
                // If analytics fails, ensure we still have the analytics structure
                allAds = allAds.map(ad => ({
                    ...ad,
                    analytics: {
                        total_views: ad.views || 0,
                        total_clicks: 0,
                        total_contacts: ad.contacts || 0,
                        current_favorites: ad.favorites || 0,
                        total_likes: ad.likes || 0
                    }
                }));
            }

            const totalAds = allAds.length;

            // Use analytics data if available, otherwise fall back to ad properties
            const totalViews = allAds.reduce((sum, ad) =>
                sum + (ad.analytics?.total_views || ad.views || 0), 0);
            const totalFavorites = allAds.reduce((sum, ad) =>
                sum + (ad.analytics?.current_favorites || ad.favorites || 0), 0);
            const totalLikes = allAds.reduce((sum, ad) =>
                sum + (ad.analytics?.total_likes || ad.likes || 0), 0);
            const totalContacts = allAds.reduce((sum, ad) =>
                sum + (ad.analytics?.total_contacts || ad.contacts || 0), 0);

            console.log('📊 Calculated Totals:');
            console.log('  - Views:', totalViews);
            console.log('  - Likes:', totalLikes);
            console.log('  - Favorites:', totalFavorites);
            console.log('  - Contacts:', totalContacts);

            // Get unique companies and categories
            const companies = new Set(allAds.map(ad => ad.company).filter(Boolean));
            const categories = new Set(allAds.map(ad => ad.category).filter(Boolean));

            console.log('  - Companies:', companies.size);
            console.log('  - Categories:', categories.size);

            // Check if elements exist
            const elements = {
                totalAdsCounter: document.getElementById('totalAdsCounter'),
                totalViewsCounter: document.getElementById('totalViewsCounter'),
                activeUsersCounter: document.getElementById('activeUsersCounter'),
                engagementCounter: document.getElementById('engagementCounter'),
                totalFavoritesCounter: document.getElementById('totalFavoritesCounter'),
                totalLikesCounter: document.getElementById('totalLikesCounter'),
                totalContactsCounter: document.getElementById('totalContactsCounter'),
                totalCompaniesCounter: document.getElementById('totalCompaniesCounter'),
                totalCategoriesCounter: document.getElementById('totalCategoriesCounter')
            };

            console.log('🎯 Element Check:');
            Object.keys(elements).forEach(key => {
                console.log(`  - ${key}:`, elements[key] ? '✅ Found' : '❌ Missing');
            });

            // Animate main counters
            console.log('🎨 Animating counters...');
            animateCounter(document.getElementById('totalAdsCounter'), totalAds);
            animateCounter(document.getElementById('totalViewsCounter'), totalViews);

            // Use actual unique companies count instead of estimated users
            animateCounter(document.getElementById('activeUsersCounter'), companies.size);

            const engagementRate = totalAds > 0 ? Math.min(99, Math.floor((totalFavorites + totalLikes) / totalAds * 10)) : 0;
            animateCounter(document.getElementById('engagementCounter'), engagementRate, 2000, '%');

            // Animate additional counters
            animateCounter(document.getElementById('totalFavoritesCounter'), totalFavorites);
            animateCounter(document.getElementById('totalLikesCounter'), totalLikes);
            animateCounter(document.getElementById('totalContactsCounter'), totalContacts);
            animateCounter(document.getElementById('totalCompaniesCounter'), companies.size);
            animateCounter(document.getElementById('totalCategoriesCounter'), categories.size);

            console.log('✅ All counters animated successfully!');

            // Update trending stats
            if (allAds.length > 0) {
                // Find top ad using analytics data
                const topAd = allAds.reduce((max, ad) => {
                    const maxViews = max.analytics?.total_views || max.views || 0;
                    const adViews = ad.analytics?.total_views || ad.views || 0;
                    return adViews > maxViews ? ad : max;
                });

                const topAdViews = topAd.analytics?.total_views || topAd.views || 0;
                document.getElementById('topAdViews').textContent = topAdViews.toLocaleString();
                document.getElementById('topAdTitle').textContent = (topAd.title || 'No title').substring(0, 50) + '...';

                // Category analysis
                const categoryCount = {};
                allAds.forEach(ad => {
                    categoryCount[ad.category] = (categoryCount[ad.category] || 0) + 1;
                });
                const topCategory = Object.entries(categoryCount).sort((a, b) => b[1] - a[1])[0];
                if (topCategory) {
                    document.getElementById('topCategory').textContent = topCategory[0];
                    document.getElementById('topCategoryCount').textContent = `${topCategory[1]} ads`;
                }

                document.getElementById('totalEngagement').textContent =
                    (totalFavorites + totalLikes).toLocaleString();

                // Average views per ad
                const avgViewsPerAd = totalAds > 0 ? Math.round(totalViews / totalAds) : 0;
                document.getElementById('avgViews').textContent = avgViewsPerAd.toLocaleString();

                // Update charts with allAds
                updateCharts(allAds);
            }

            console.log('✅ Live stats loaded successfully!');
        } else {
            console.warn('⚠️ No ads data in response:', data);
        }
    } catch (error) {
        console.error('❌ Failed to load live stats:', error);
        console.error('Error details:', error.message);
        console.error('Stack trace:', error.stack);
    }
}

// Update Charts
function updateCharts(ads) {
    // Views Distribution Chart - use analytics data
    const viewsData = ads.slice(0, 10).map(ad => ({
        title: (ad.title || 'Untitled').substring(0, 20) + '...',
        views: ad.analytics?.total_views || ad.views || 0
    }));

    if (viewsChart) viewsChart.destroy();

    const viewsCtx = document.getElementById('viewsChart');
    if (viewsCtx) {
        viewsChart = new Chart(viewsCtx, {
            type: 'bar',
            data: {
                labels: viewsData.map(d => d.title),
                datasets: [{
                    label: 'Views',
                    data: viewsData.map(d => d.views),
                    backgroundColor: 'rgba(99, 102, 241, 0.6)',
                    borderColor: 'rgba(99, 102, 241, 1)',
                    borderWidth: 1,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#fff'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#9ca3af' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#9ca3af', maxRotation: 45, minRotation: 45 }
                    }
                }
            }
        });
    }

    // Category Distribution Chart
    const categoryCount = {};
    ads.forEach(ad => {
        categoryCount[ad.category] = (categoryCount[ad.category] || 0) + 1;
    });

    if (categoryChart) categoryChart.destroy();

    const categoryCtx = document.getElementById('categoryChart');
    if (categoryCtx) {
        categoryChart = new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(categoryCount),
                datasets: [{
                    data: Object.values(categoryCount),
                    backgroundColor: [
                        'rgba(99, 102, 241, 0.8)',
                        'rgba(168, 85, 247, 0.8)',
                        'rgba(236, 72, 153, 0.8)',
                        'rgba(251, 146, 60, 0.8)',
                        'rgba(34, 197, 94, 0.8)',
                        'rgba(59, 130, 246, 0.8)'
                    ],
                    borderColor: 'rgba(255, 255, 255, 0.1)',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#fff', padding: 15 }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#fff'
                    }
                }
            }
        });
    }
}

// Load Live Activity Feed
async function loadActivityFeed() {
    try {
        const response = await fetch('/app/api/get_ads.php');
        const data = await response.json();

        if (data && data.ads) {
            const activities = [];

            data.ads.slice(0, 10).forEach(ad => {
                const timeDiff = Date.now() - (ad.timestamp * 1000);
                const minutesAgo = Math.floor(timeDiff / 60000);

                activities.push({
                    icon: 'fa-ad',
                    color: 'indigo',
                    text: `New ad: "${(ad.title || 'Untitled').substring(0, 40)}..."`,
                    time: minutesAgo < 1 ? 'Just now' : minutesAgo < 60 ? `${minutesAgo}m ago` : `${Math.floor(minutesAgo / 60)}h ago`,
                    category: ad.category || 'Uncategorized'
                });

                if ((ad.views || 0) > 0) {
                    activities.push({
                        icon: 'fa-eye',
                        color: 'blue',
                        text: `${ad.views} views • "${(ad.title || 'Untitled').substring(0, 30)}..."`,
                        time: `${Math.floor(Math.random() * 30) + 1}m ago`,
                        category: ad.category || 'Uncategorized'
                    });
                }
            });

            const shuffled = activities.sort(() => Math.random() - 0.5).slice(0, 10);

            const feedHTML = shuffled.map(activity => `
                <div class="activity-item flex items-center gap-4 p-4 bg-white/5 rounded-xl hover:bg-white/10 transition cursor-pointer">
                    <div class="w-12 h-12 bg-${activity.color}-600/20 rounded-full flex items-center justify-center flex-shrink-0">
                        <i class="fas ${activity.icon} text-${activity.color}-400"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <p class="text-sm text-white truncate">${activity.text}</p>
                        <div class="flex items-center gap-2 mt-1">
                            <span class="text-xs text-gray-400">${activity.time}</span>
                            <span class="text-xs text-gray-500">•</span>
                            <span class="text-xs text-indigo-400">${activity.category}</span>
                        </div>
                    </div>
                    <i class="fas fa-chevron-right text-gray-600"></i>
                </div>
            `).join('');

            document.getElementById('activityFeed').innerHTML = feedHTML;
            document.getElementById('lastUpdate').textContent = 'Updated just now';
            lastActivityUpdate = Date.now();
        }
    } catch (error) {
        console.error('Failed to load activity feed:', error);
    }
}

// Refresh activity manually
function refreshActivity() {
    const btn = event.target.closest('button');
    if (!btn) return;
    const icon = btn.querySelector('i');
    if (icon) icon.classList.add('fa-spin');

    loadActivityFeed().then(() => {
        setTimeout(() => {
            if (icon) icon.classList.remove('fa-spin');
        }, 500);
    });
}

// Update timestamp
function updateTimestamp() {
    const elem = document.getElementById('lastUpdate');
    if (!elem) return;

    const seconds = Math.floor((Date.now() - lastActivityUpdate) / 1000);
    const text = seconds < 5 ? 'Updated just now' :
                 seconds < 60 ? `Updated ${seconds}s ago` :
                 `Updated ${Math.floor(seconds / 60)}m ago`;
    elem.textContent = text;
}

// Update system time
function updateSystemTime() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('en-US', { hour12: false });
    const elem = document.getElementById('systemTime');
    if (elem) elem.textContent = timeStr;
}

// ============================================
// TAB SWITCHING
// ============================================
function switchTab(tabName) {
    // Hide all tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });

    // Remove active class from all tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab content
    const content = document.getElementById('content-' + tabName);
    if (content) content.classList.remove('hidden');

    // Add active class to selected tab
    const tab = document.getElementById('tab-' + tabName);
    if (tab) tab.classList.add('active');

    // Load tab-specific data
    loadTabData(tabName);
}

function loadTabData(tabName) {
    switch(tabName) {
        case 'users':
            loadUsersData();
            break;
        case 'companies':
            loadCompaniesData();
            break;
        case 'ads':
            loadAdsData();
            break;
        case 'devices':
            loadDevicesData();
            break;
    }
}

// ============================================
// USER MANAGEMENT FUNCTIONS
// ============================================
async function loadUsersData() {
    const usersTableBody = document.getElementById('usersTableBody');
    if (!usersTableBody) return;

    // Show loading state
    usersTableBody.innerHTML = '<tr><td colspan="6" class="py-8 text-center text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i>Loading users...</td></tr>';

    try {
        // Fetch real users data from API
        // TODO: Create /app/api/admin/get_users.php endpoint
        const response = await fetch('/app/api/admin/get_users.php');
        const data = await response.json();

        if (!data.success || !data.users || data.users.length === 0) {
            usersTableBody.innerHTML = '<tr><td colspan="6" class="py-8 text-center text-gray-400">No users found</td></tr>';
            return;
        }

        const users = data.users;

        usersTableBody.innerHTML = users.map(user => `
        <tr class="border-b border-white/5 hover:bg-white/5">
            <td class="py-3 px-4">
                <div class="flex items-center gap-3">
                    <div class="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
                        <span class="text-xs font-bold">${user.name.charAt(0)}</span>
                    </div>
                    <span class="font-semibold">${user.name}</span>
                </div>
            </td>
            <td class="py-3 px-4 text-gray-400">${user.email}</td>
            <td class="py-3 px-4">
                <span class="px-2 py-1 bg-indigo-600/20 text-indigo-400 rounded text-xs font-semibold">${user.role}</span>
            </td>
            <td class="py-3 px-4">
                <span class="px-2 py-1 ${user.status === 'active' ? 'bg-green-600/20 text-green-400' : 'bg-red-600/20 text-red-400'} rounded text-xs font-semibold">
                    ${user.status}
                </span>
            </td>
            <td class="py-3 px-4 text-gray-400 text-sm">${user.lastActive}</td>
            <td class="py-3 px-4">
                <div class="flex items-center gap-2">
                    <button onclick="editUser('${user.email}')" class="text-indigo-400 hover:text-indigo-300">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button onclick="deleteUser('${user.email}')" class="text-red-400 hover:text-red-300">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');

        // Update stats from real data
        document.getElementById('activeUsersCount').textContent = users.filter(u => u.status === 'active').length;
        document.getElementById('pendingUsersCount').textContent = users.filter(u => u.status === 'pending').length;
        document.getElementById('blockedUsersCount').textContent = users.filter(u => u.status === 'blocked').length;
        document.getElementById('onlineNowCount').textContent = users.filter(u => u.lastActive && u.lastActive.includes('min')).length;

    } catch (error) {
        console.error('Failed to load users:', error);
        usersTableBody.innerHTML = '<tr><td colspan="6" class="py-8 text-center text-red-400"><i class="fas fa-exclamation-triangle mr-2"></i>Failed to load users. Using sample data.</td></tr>';

        // Fallback to sample data if API fails
        const sampleUsers = [
            { name: 'Sample User', email: 'sample@example.com', role: 'User', status: 'active', lastActive: 'Just now' }
        ];

        usersTableBody.innerHTML += sampleUsers.map(user => `
            <tr class="border-b border-white/5 hover:bg-white/5">
                <td class="py-3 px-4">
                    <div class="flex items-center gap-3">
                        <div class="w-8 h-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-full flex items-center justify-center">
                            <span class="text-xs font-bold">${user.name.charAt(0)}</span>
                        </div>
                        <span class="font-semibold">${user.name}</span>
                    </div>
                </td>
                <td class="py-3 px-4 text-gray-400">${user.email}</td>
                <td class="py-3 px-4">
                    <span class="px-2 py-1 bg-indigo-600/20 text-indigo-400 rounded text-xs font-semibold">${user.role}</span>
                </td>
                <td class="py-3 px-4">
                    <span class="px-2 py-1 bg-green-600/20 text-green-400 rounded text-xs font-semibold">${user.status}</span>
                </td>
                <td class="py-3 px-4 text-gray-400 text-sm">${user.lastActive}</td>
                <td class="py-3 px-4">
                    <div class="flex items-center gap-2">
                        <button onclick="editUser('${user.email}')" class="text-indigo-400 hover:text-indigo-300">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteUser('${user.email}')" class="text-red-400 hover:text-red-300">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('');
    }
}

function addNewUser() {
    alert('Add New User modal would open here');
}

function editUser(email) {
    alert('Edit user: ' + email);
}

function deleteUser(email) {
    if (confirm('Are you sure you want to delete this user?')) {
        alert('User deleted: ' + email);
        loadUsersData();
    }
}

// ============================================
// COMPANY MANAGEMENT FUNCTIONS
// ============================================
async function loadCompaniesData() {
    const companiesTableBody = document.getElementById('companiesTableBody');
    if (!companiesTableBody) return;

    companiesTableBody.innerHTML = '<tr><td colspan="6" class="py-8 text-center text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i>Loading companies...</td></tr>';

    try {
        // Fetch companies from API
        const response = await fetch('/app/api/get_companies.php');
        const data = await response.json();

        if (!data || !data.success || !data.companies) {
            companiesTableBody.innerHTML = '<tr><td colspan="6" class="py-8 text-center text-gray-400">No companies found</td></tr>';
            return;
        }

        const companies = data.companies;
        const stats = data.stats;

        if (companies.length === 0) {
            companiesTableBody.innerHTML = '<tr><td colspan="6" class="py-8 text-center text-gray-400">No companies found</td></tr>';
            return;
        }

        // Update stats cards
        document.getElementById('totalCompaniesStats').textContent = stats.total;
        document.getElementById('verifiedCompaniesCount').textContent = stats.verified;
        document.getElementById('suspendedCompaniesCount').textContent = stats.suspended;
        document.getElementById('blockedCompaniesCount').textContent = stats.blocked;

        // Render companies table
        companiesTableBody.innerHTML = companies.map(company => {
            const statusColors = {
                'verified': 'bg-green-600/20 text-green-400 border-green-500/30',
                'active': 'bg-blue-600/20 text-blue-400 border-blue-500/30',
                'suspended': 'bg-yellow-600/20 text-yellow-400 border-yellow-500/30',
                'blocked': 'bg-red-600/20 text-red-400 border-red-500/30',
                'banned': 'bg-red-600/20 text-red-400 border-red-500/30'
            };

            const statusIcons = {
                'verified': 'fa-check-circle',
                'active': 'fa-circle',
                'suspended': 'fa-pause-circle',
                'blocked': 'fa-lock',
                'banned': 'fa-ban'
            };

            const status = company.status || 'active';
            const statusClass = statusColors[status] || 'bg-gray-600/20 text-gray-400';
            const statusIcon = statusIcons[status] || 'fa-circle';

            return `
        <tr class="border-b border-white/5 hover:bg-white/5 transition">
            <td class="py-3 px-4">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center">
                        <i class="fas fa-building text-white"></i>
                    </div>
                    <div>
                        <div class="font-semibold">${escapeHtml(company.company_name)}</div>
                        <div class="text-xs text-gray-500">${escapeHtml(company.email)}</div>
                    </div>
                </div>
            </td>
            <td class="py-3 px-4 text-gray-400">${company.total_ads}</td>
            <td class="py-3 px-4 text-gray-400">${company.total_views.toLocaleString()}</td>
            <td class="py-3 px-4">
                <span class="px-2 py-1 ${statusClass} rounded text-xs font-semibold border flex items-center gap-1 w-fit">
                    <i class="fas ${statusIcon}"></i>
                    ${status.charAt(0).toUpperCase() + status.slice(1)}
                </span>
            </td>
            <td class="py-3 px-4 text-gray-400 text-sm">${formatDate(company.created_at)}</td>
            <td class="py-3 px-4">
                <div class="flex items-center gap-2">
                    <button onclick="viewCompany('${escapeHtml(company.company_slug)}')" class="text-indigo-400 hover:text-indigo-300 transition" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${status !== 'suspended' ? `
                    <button onclick="suspendCompany('${escapeHtml(company.company_slug)}')" class="text-yellow-400 hover:text-yellow-300 transition" title="Suspend">
                        <i class="fas fa-pause"></i>
                    </button>
                    ` : `
                    <button onclick="activateCompany('${escapeHtml(company.company_slug)}')" class="text-green-400 hover:text-green-300 transition" title="Activate">
                        <i class="fas fa-play"></i>
                    </button>
                    `}
                    ${status !== 'blocked' && status !== 'banned' ? `
                    <button onclick="blockCompany('${escapeHtml(company.company_slug)}')" class="text-red-400 hover:text-red-300 transition" title="Block">
                        <i class="fas fa-ban"></i>
                    </button>
                    ` : `
                    <button onclick="unblockCompany('${escapeHtml(company.company_slug)}')" class="text-blue-400 hover:text-blue-300 transition" title="Unblock">
                        <i class="fas fa-unlock"></i>
                    </button>
                    `}
                </div>
            </td>
        </tr>
    `;
        }).join('');

    } catch (error) {
        console.error('Failed to load companies:', error);
        companiesTableBody.innerHTML = '<tr><td colspan="6" class="py-8 text-center text-red-400"><i class="fas fa-exclamation-triangle mr-2"></i>Failed to load companies</td></tr>';
    }
}

function formatDate(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function approveCompany() {
    alert('Approve selected companies');
}

function viewCompany(companySlug) {
    alert('View company: ' + companySlug);
    // TODO: Redirect to company details page or show modal
}

function suspendCompany(companySlug) {
    if (confirm('Are you sure you want to suspend this company? All their ads will be hidden.')) {
        // TODO: Implement API call to suspend company
        alert('Company suspended: ' + companySlug);
        loadCompaniesData();
    }
}

function activateCompany(companySlug) {
    if (confirm('Activate this company? Their ads will become visible again.')) {
        // TODO: Implement API call to activate company
        alert('Company activated: ' + companySlug);
        loadCompaniesData();
    }
}

function blockCompany(companySlug) {
    if (confirm('BLOCK this company permanently? This action will ban them from the platform and remove all their ads. This cannot be easily undone.')) {
        // TODO: Implement API call to block company
        alert('Company blocked: ' + companySlug);
        loadCompaniesData();
    }
}

function unblockCompany(companySlug) {
    if (confirm('Unblock this company? They will be able to access the platform again.')) {
        // TODO: Implement API call to unblock company
        alert('Company unblocked: ' + companySlug);
        loadCompaniesData();
    }
}
        loadCompaniesData();
    }
}

// ============================================
// ADS MANAGEMENT FUNCTIONS
// ============================================
async function loadAdsData() {
    const adsTableBody = document.getElementById('adsTableBody');
    if (!adsTableBody) return;

    adsTableBody.innerHTML = '<tr><td colspan="7" class="py-8 text-center text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i>Loading ads...</td></tr>';

    try {
        const response = await fetch('/app/api/get_ads.php');
        const data = await response.json();

        if (!data || !data.ads || data.ads.length === 0) {
            adsTableBody.innerHTML = '<tr><td colspan="7" class="py-8 text-center text-gray-400">No ads found</td></tr>';
            return;
        }

        const ads = data.ads.map(ad => ({
            ad_id: ad.ad_id,
            title: ad.title || 'Untitled',
            company: ad.company || 'Unknown',
            category: ad.category || 'Uncategorized',
            views: ad.views || 0,
            status: ad.status || 'active',
            flagged: ad.flagged || false
        }));

        adsTableBody.innerHTML = ads.map((ad, i) => `
        <tr class="border-b border-white/5 hover:bg-white/5">
            <td class="py-3 px-4">
                <input type="checkbox" class="rounded">
            </td>
            <td class="py-3 px-4 font-semibold">${ad.title}</td>
            <td class="py-3 px-4 text-gray-400">${ad.company}</td>
            <td class="py-3 px-4 text-gray-400">${ad.category}</td>
            <td class="py-3 px-4 text-gray-400">${ad.views.toLocaleString()}</td>
            <td class="py-3 px-4">
                <span class="px-2 py-1 ${
                    ad.status === 'active' ? 'bg-green-600/20 text-green-400' :
                    ad.status === 'flagged' ? 'bg-red-600/20 text-red-400' :
                    'bg-yellow-600/20 text-yellow-400'
                } rounded text-xs font-semibold">${ad.status}</span>
            </td>
            <td class="py-3 px-4">
                <div class="flex items-center gap-2">
                    <button onclick="approveAd(${i})" class="text-green-400 hover:text-green-300">
                        <i class="fas fa-check"></i>
                    </button>
                    <button onclick="rejectAd(${i})" class="text-red-400 hover:text-red-300">
                        <i class="fas fa-times"></i>
                    </button>
                    <button onclick="editAd(${i})" class="text-indigo-400 hover:text-indigo-300">
                        <i class="fas fa-edit"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');

        document.getElementById('totalAdsStats').textContent = ads.length;
        document.getElementById('activeAdsStats').textContent = ads.filter(a => a.status === 'active').length;
        document.getElementById('pendingAdsStats').textContent = ads.filter(a => a.status === 'pending').length;
        document.getElementById('rejectedAdsStats').textContent = ads.filter(a => a.status === 'rejected').length;
        document.getElementById('reportedAdsStats').textContent = ads.filter(a => a.flagged).length;
        document.getElementById('flaggedCount').textContent = ads.filter(a => a.flagged).length;

    } catch (error) {
        console.error('Failed to load ads:', error);
        adsTableBody.innerHTML = '<tr><td colspan="7" class="py-8 text-center text-red-400"><i class="fas fa-exclamation-triangle mr-2"></i>Failed to load ads</td></tr>';
    }
}

function flaggedAds() {
    alert('Show flagged ads');
}

function bulkApprove() {
    alert('Bulk approve selected ads');
}

function approveAd(id) {
    alert('Approve ad: ' + id);
    loadAdsData();
}

function rejectAd(id) {
    if (confirm('Reject this ad?')) {
        alert('Ad rejected: ' + id);
        loadAdsData();
    }
}

function editAd(id) {
    alert('Edit ad: ' + id);
}

// ============================================
// DEVICES & SECURITY FUNCTIONS
// ============================================
async function loadDevicesData() {
    const devicesTableBody = document.getElementById('devicesTableBody');
    if (!devicesTableBody) return;

    devicesTableBody.innerHTML = '<tr><td colspan="5" class="py-8 text-center text-gray-500"><i class="fas fa-spinner fa-spin mr-2"></i>Loading devices...</td></tr>';

    try {
        // Fetch device data from user profiling API
        const response = await fetch('/app/api/user_profiling.php');
        const data = await response.json();

        if (!data.success || !data.devices || data.devices.length === 0) {
            devicesTableBody.innerHTML = '<tr><td colspan="5" class="py-8 text-center text-gray-400">No devices tracked yet. Device fingerprinting will appear as users visit the platform.</td></tr>';

            // Set counts to 0
            document.getElementById('totalDevices').textContent = '0';
            document.getElementById('mobileDevices').textContent = '0';
            document.getElementById('desktopDevices').textContent = '0';
            return;
        }

        const devices = data.devices.map(d => ({
            fingerprint: d.fingerprint,
            device: d.device_type || 'Unknown Device',
            user: d.user_id || 'Anonymous',
            location: d.location || 'Unknown',
            lastSeen: d.last_seen ? timeAgo(d.last_seen) : 'Never',
            isMobile: d.is_mobile || false
        }));

        devicesTableBody.innerHTML = devices.map(device => `
            <tr class="border-b border-white/5 hover:bg-white/5">
                <td class="py-3 px-4">
                    <div class="flex items-center gap-2">
                        <i class="fas fa-${device.isMobile ? 'mobile-alt' : 'desktop'} text-indigo-400"></i>
                        <span class="text-sm">${device.device}</span>
                    </div>
                </td>
                <td class="py-3 px-4 text-gray-400 text-sm">${device.user}</td>
                <td class="py-3 px-4 text-gray-400 text-sm">${device.location}</td>
                <td class="py-3 px-4 text-gray-400 text-sm">${device.lastSeen}</td>
                <td class="py-3 px-4">
                    <button onclick="blockDevice('${device.fingerprint}')" class="text-red-400 hover:text-red-300 text-sm">
                        <i class="fas fa-ban mr-1"></i>Block
                    </button>
                </td>
            </tr>
        `).join('');

        // Update device statistics
        document.getElementById('totalDevices').textContent = devices.length;
        document.getElementById('mobileDevices').textContent = devices.filter(d => d.isMobile).length;
        document.getElementById('desktopDevices').textContent = devices.filter(d => !d.isMobile).length;

    } catch (error) {
        console.error('Failed to load devices:', error);
        devicesTableBody.innerHTML = '<tr><td colspan="5" class="py-8 text-center text-red-400"><i class="fas fa-exclamation-triangle mr-2"></i>Failed to load device data. Check if user_profiling.php API is accessible.</td></tr>';

        // Set counts to 0 on error
        document.getElementById('totalDevices').textContent = '0';
        document.getElementById('mobileDevices').textContent = '0';
        document.getElementById('desktopDevices').textContent = '0';
    }
}

// Helper function to format timestamps
function timeAgo(timestamp) {
    const seconds = Math.floor((Date.now() / 1000) - timestamp);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return Math.floor(seconds / 60) + ' mins ago';
    if (seconds < 86400) return Math.floor(seconds / 3600) + ' hours ago';
    if (seconds < 604800) return Math.floor(seconds / 86400) + ' days ago';
    return new Date(timestamp * 1000).toLocaleDateString();
}

function manageIPWhitelist() {
    alert('IP Whitelist management modal would open here');
}

function blockDevice(device) {
    if (confirm('Block device: ' + device + '?')) {
        alert('Device blocked');
        loadDevicesData();
    }
}

// ============================================
// PLATFORM RULES FUNCTIONS
// ============================================
function saveRules() {
    alert('Platform rules saved successfully!');
}

// ============================================
// SYSTEM SETTINGS FUNCTIONS
// ============================================
function clearCache() {
    if (confirm('Clear all cached data? This may temporarily slow down the platform.')) {
        alert('Cache cleared successfully!');
    }
}

function resetAnalytics() {
    if (confirm('Reset all analytics data? This action cannot be undone!')) {
        alert('Analytics reset!');
    }
}

function confirmPlatformReset() {
    const confirmation = prompt('Type "RESET PLATFORM" to confirm factory reset:');
    if (confirmation === 'RESET PLATFORM') {
        alert('Platform reset initiated!');
    }
}

// ============================================
// QUICK ACTION FUNCTIONS
// ============================================
function showNotifications() {
    alert('Notifications panel would open here');
}

function emergencyStop() {
    if (confirm('Activate emergency stop? This will halt all platform operations!')) {
        alert('🚨 EMERGENCY STOP ACTIVATED');
    }
}

function toggleAIAssistant() {
    alert('AI Assistant panel would open here');
}

function toggleUserMenu() {
    // Create dropdown menu if it doesn't exist
    let menu = document.getElementById('userDropdownMenu');

    if (!menu) {
        menu = document.createElement('div');
        menu.id = 'userDropdownMenu';
        menu.className = 'absolute top-full right-0 mt-2 w-64 glass-card rounded-xl shadow-xl border border-white/20 overflow-hidden z-50';
        menu.style.display = 'none';

        menu.innerHTML = `
            <div class="p-4 border-b border-white/10">
                <p class="text-sm font-bold text-white"><?= htmlspecialchars($adminUsername) ?></p>
                <p class="text-xs text-gray-400"><?= htmlspecialchars($_SESSION['admin_role'] ?? 'Administrator') ?></p>
            </div>
            <div class="p-2">
                <a href="#" onclick="viewProfile(event)" class="flex items-center gap-3 px-4 py-3 hover:bg-white/10 rounded-lg transition">
                    <i class="fas fa-user text-indigo-400"></i>
                    <span class="text-sm text-white">My Profile</span>
                </a>
                <a href="#" onclick="changePassword(event)" class="flex items-center gap-3 px-4 py-3 hover:bg-white/10 rounded-lg transition">
                    <i class="fas fa-key text-yellow-400"></i>
                    <span class="text-sm text-white">Change Password</span>
                </a>
                <a href="#" onclick="viewActivityLog(event)" class="flex items-center gap-3 px-4 py-3 hover:bg-white/10 rounded-lg transition">
                    <i class="fas fa-history text-blue-400"></i>
                    <span class="text-sm text-white">Activity Log</span>
                </a>
                <div class="border-t border-white/10 my-2"></div>
                <a href="logout.php" class="flex items-center gap-3 px-4 py-3 hover:bg-red-600/20 rounded-lg transition text-red-400">
                    <i class="fas fa-sign-out-alt"></i>
                    <span class="text-sm font-semibold">Logout</span>
                </a>
            </div>
        `;

        event.target.closest('div').style.position = 'relative';
        event.target.closest('div').appendChild(menu);
    }

    // Toggle menu visibility
    if (menu.style.display === 'none') {
        menu.style.display = 'block';
    } else {
        menu.style.display = 'none';
    }

    // Close menu when clicking outside
    setTimeout(() => {
        document.addEventListener('click', function closeMenu(e) {
            if (!menu.contains(e.target) && !e.target.closest('[onclick="toggleUserMenu()"]')) {
                menu.style.display = 'none';
                document.removeEventListener('click', closeMenu);
            }
        });
    }, 0);
}

function viewProfile(e) {
    e.preventDefault();
    alert('View Profile - Coming soon');
}

function changePassword(e) {
    e.preventDefault();
    alert('Change Password - Coming soon');
}

function viewActivityLog(e) {
    e.preventDefault();
    alert('Activity Log - Coming soon');
}

// ============================================
// AD STATUS STATISTICS FUNCTIONS
// ============================================
async function loadAdStatusStats() {
    try {
        const res = await fetch('/app/api/ad_status_stats.php');
        const data = await res.json();

        if (data.success) {
            const stats = data.stats;

            // Update counters
            document.getElementById('activeAdsCount').textContent = stats.active || 0;
            document.getElementById('inactiveAdsCount').textContent = stats.inactive || 0;
            document.getElementById('scheduledAdsCount').textContent = stats.scheduled || 0;
            document.getElementById('expiredAdsCount').textContent = stats.expired || 0;
            document.getElementById('totalAdsCount').textContent = stats.total || 0;

            // Calculate percentages
            const total = stats.total || 1; // Avoid division by zero
            const activePercent = Math.round((stats.active / total) * 100);
            const inactivePercent = Math.round((stats.inactive / total) * 100);
            const scheduledPercent = Math.round((stats.scheduled / total) * 100);
            const expiredPercent = Math.round((stats.expired / total) * 100);

            // Update percentage display
            document.getElementById('adStatsPercentage').textContent = activePercent;

            // Update progress bars
            setTimeout(() => {
                document.getElementById('activeBar').style.width = activePercent + '%';
                document.getElementById('inactiveBar').style.width = inactivePercent + '%';
                document.getElementById('scheduledBar').style.width = scheduledPercent + '%';
                document.getElementById('expiredBar').style.width = expiredPercent + '%';

                document.getElementById('activeBarText').textContent = stats.active;
                document.getElementById('inactiveBarText').textContent = stats.inactive;
                document.getElementById('scheduledBarText').textContent = stats.scheduled;
                document.getElementById('expiredBarText').textContent = stats.expired;
            }, 100);

            // Animate counters
            animateCounter(document.getElementById('activeAdsCount'), stats.active);
            animateCounter(document.getElementById('inactiveAdsCount'), stats.inactive);
            animateCounter(document.getElementById('scheduledAdsCount'), stats.scheduled);
            animateCounter(document.getElementById('expiredAdsCount'), stats.expired);
            animateCounter(document.getElementById('totalAdsCount'), stats.total);
        }
    } catch (error) {
        console.error('Failed to load ad status stats:', error);
    }
}


function refreshAdStats() {
    // Show loading state
    ['activeAdsCount', 'inactiveAdsCount', 'scheduledAdsCount', 'expiredAdsCount', 'totalAdsCount'].forEach(id => {
        const element = document.getElementById(id);
        if (element) element.textContent = '-';
    });

    // Reload stats
    loadAdStatusStats();
}

function filterAdsByStatus(status) {
    // This will open a filtered view - implement based on your needs
    console.log('Filter ads by status:', status);
    // You can redirect to a page with filtered ads or show a modal
    // Example: window.location.href = `/app/admin/ads.php?status=${status}`;
}

// ============================================
// CONTENT MODERATION FUNCTIONS
// ============================================
async function loadViolations() {
    try {
        const [violationsRes, statsRes] = await Promise.all([
            fetch('/app/api/moderation_violations.php?action=list&status=pending'),
            fetch('/app/api/moderation_violations.php?action=stats')
        ]);

        const violationsData = await violationsRes.json();
        const statsData = await statsRes.json();

        if (statsData.success) {
            document.getElementById('pendingCount').textContent = statsData.stats.pending || 0;
            document.getElementById('criticalViolations').textContent = statsData.stats.critical || 0;
            document.getElementById('highViolations').textContent = statsData.stats.high || 0;
            document.getElementById('mediumViolations').textContent = statsData.stats.medium || 0;
            document.getElementById('resolvedViolations').textContent = statsData.stats.resolved || 0;
        }

        if (violationsData.success) {
            displayViolations(violationsData.violations);
        }
    } catch (error) {
        console.error('Failed to load violations:', error);
        document.getElementById('violationsList').innerHTML = `
            <div class="text-center py-8 text-red-400">
                <i class="fas fa-exclamation-triangle text-4xl mb-3"></i>
                <p>Failed to load violations</p>
            </div>
        `;
    }
}

function displayViolations(violations) {
    const container = document.getElementById('violationsList');

    if (!violations || violations.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-green-400">
                <i class="fas fa-check-circle text-4xl mb-3"></i>
                <p>No pending violations. All ads are compliant!</p>
            </div>
        `;
        return;
    }

    container.innerHTML = violations.map(v => {
        const severityColors = {
            4: 'red',
            3: 'orange',
            2: 'yellow',
            1: 'yellow'
        };
        const severityText = {
            4: 'CRITICAL',
            3: 'HIGH',
            2: 'MEDIUM',
            1: 'LOW'
        };
        const color = severityColors[v.severity] || 'gray';
        const severity = severityText[v.severity] || 'UNKNOWN';

        const violations = v.violations_data || {};
        const issues = violations.content_issues || [];
        const flags = violations.pattern_flags || [];

        return `
            <div class="bg-${color}-600/10 border-l-4 border-${color}-600 rounded-lg p-4 hover:bg-white/5 transition">
                <div class="flex items-start justify-between mb-3">
                    <div class="flex-1">
                        <div class="flex items-center gap-3 mb-2">
                            <span class="px-3 py-1 bg-${color}-600 rounded-full text-xs font-bold">${severity}</span>
                            <span class="text-sm text-gray-400">Score: ${v.ai_score}/100</span>
                            <span class="text-sm text-gray-400">ID: ${escapeHtml(v.ad_id).substring(0, 15)}...</span>
                        </div>
                        <h3 class="text-lg font-bold text-white mb-1">${escapeHtml(v.ad_title || 'Untitled')}</h3>
                        <p class="text-sm text-gray-400 mb-2">${escapeHtml((v.ad_description || '').substring(0, 100))}...</p>
                        <div class="flex gap-4 text-xs text-gray-500">
                            <span><i class="fas fa-building mr-1"></i>${escapeHtml(v.company_name || 'Unknown')}</span>
                            <span><i class="fas fa-tag mr-1"></i>${escapeHtml(v.category_name || 'Unknown')}</span>
                            <span><i class="fas fa-clock mr-1"></i>${formatTimestamp(v.created_at)}</span>
                        </div>
                    </div>
                </div>

                <!-- Violations -->
                ${issues.length > 0 ? `
                    <div class="bg-black/30 rounded-lg p-3 mb-3">
                        <div class="text-xs text-${color}-400 font-bold mb-2">POLICY VIOLATIONS:</div>
                        <div class="space-y-1">
                            ${issues.map(issue => `
                                <div class="flex items-start gap-2 text-xs">
                                    <i class="fas fa-times-circle text-${color}-500 mt-0.5"></i>
                                    <span class="text-gray-300">${escapeHtml(issue)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                ${flags.length > 0 ? `
                    <div class="bg-black/30 rounded-lg p-3 mb-3">
                        <div class="text-xs text-orange-400 font-bold mb-2">PATTERN FLAGS:</div>
                        <div class="space-y-1">
                            ${flags.map(flag => `
                                <div class="flex items-start gap-2 text-xs">
                                    <i class="fas fa-flag text-orange-500 mt-0.5"></i>
                                    <span class="text-gray-300">${escapeHtml(flag)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                <!-- Actions -->
                <div class="flex gap-2 flex-wrap">
                    <button onclick="takeViolationAction(${v.id}, 'delete', '${escapeHtml(v.ad_id)}')"
                            class="px-3 py-1.5 bg-red-600 hover:bg-red-700 rounded-lg transition text-xs font-semibold">
                        <i class="fas fa-trash mr-1"></i>Delete Ad
                    </button>
                    <button onclick="takeViolationAction(${v.id}, 'ban', '${escapeHtml(v.ad_id)}')"
                            class="px-3 py-1.5 bg-gray-700 hover:bg-gray-800 rounded-lg transition text-xs font-semibold">
                        <i class="fas fa-ban mr-1"></i>Ban Company
                    </button>
                    <button onclick="takeViolationAction(${v.id}, 'pause', '${escapeHtml(v.ad_id)}')"
                            class="px-3 py-1.5 bg-yellow-600 hover:bg-yellow-700 rounded-lg transition text-xs font-semibold">
                        <i class="fas fa-pause mr-1"></i>Pause
                    </button>
                    <button onclick="takeViolationAction(${v.id}, 'approve', '${escapeHtml(v.ad_id)}')"
                            class="px-3 py-1.5 bg-green-600 hover:bg-green-700 rounded-lg transition text-xs font-semibold">
                        <i class="fas fa-check mr-1"></i>Approve
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

async function takeViolationAction(violationId, actionType, adId) {
    const actionNames = {
        delete: 'Delete this ad',
        ban: 'Ban this company',
        pause: 'Pause this ad',
        approve: 'Approve (no action)'
    };

    if (!confirm(`Are you sure you want to: ${actionNames[actionType]}?`)) {
        return;
    }

    try {
        const formData = new FormData();
        formData.append('action', 'take_action');
        formData.append('violation_id', violationId);
        formData.append('action_type', actionType);
        formData.append('admin_user', '<?= $adminUsername ?>');
        formData.append('reason', 'Admin dashboard action');

        const res = await fetch('/app/api/moderation_violations.php', {
            method: 'POST',
            body: formData
        });

        const data = await res.json();

        if (data.success) {
            let message = `Action completed: ${actionType}`;
            if (data.notification) {
                if (data.notification === 'sent') {
                    message += ' ✉️ Owner notified';
                } else if (data.notification === 'failed') {
                    message += ' ⚠️ Notification failed';
                }
            }
            showNotification(message, 'success');
            refreshViolations();
        } else {
            showNotification(`Failed: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Action failed:', error);
        showNotification('Action failed: Network error', 'error');
    }
}

function refreshViolations() {
    document.getElementById('violationsList').innerHTML = `
        <div class="text-center py-8 text-gray-400">
            <i class="fas fa-spinner fa-spin text-4xl mb-3"></i>
            <p>Refreshing violations...</p>
        </div>
    `;
    loadViolations();
}

async function runNewScan() {
    const btn = event.target;
    const originalHTML = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Scanning...';

    try {
        const res = await fetch('/app/api/scanner.php?action=scan');
        const data = await res.json();

        if (data.success) {
            showNotification(`Scan complete! Found ${data.data.flagged_ads.length} violations`, 'success');
            setTimeout(refreshViolations, 1000);
        } else {
            showNotification('Scan failed', 'error');
        }
    } catch (error) {
        console.error('Scan failed:', error);
        showNotification('Scan failed: Network error', 'error');
    }

    btn.disabled = false;
    btn.innerHTML = originalHTML;
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);

    if (diff < 60) return 'Just now';
    if (diff < 3600) return Math.floor(diff / 60) + ' mins ago';
    if (diff < 86400) return Math.floor(diff / 3600) + ' hours ago';
    return Math.floor(diff / 86400) + ' days ago';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type) {
    const color = type === 'success' ? 'green' : type === 'error' ? 'red' : 'blue';
    const icon = type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : 'info-circle';

    const div = document.createElement('div');
    div.className = `fixed top-20 right-4 px-6 py-4 bg-${color}-600 text-white rounded-lg shadow-2xl z-50 flex items-center gap-3 animate-slide-in`;
    div.innerHTML = `
        <i class="fas fa-${icon}"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(div);

    setTimeout(() => {
        div.style.opacity = '0';
        div.style.transform = 'translateX(100%)';
        div.style.transition = 'all 0.3s ease';
        setTimeout(() => div.remove(), 300);
    }, 3000);
}

// ============================================
// NEURAL NETWORK BACKGROUND
// ============================================
function initNeuralNetwork() {
    const canvas = document.getElementById('neuralCanvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const particles = [];
    const particleCount = 50;

    for (let i = 0; i < particleCount; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            vx: (Math.random() - 0.5) * 0.5,
            vy: (Math.random() - 0.5) * 0.5
        });
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = 'rgba(99, 102, 241, 0.1)';
        ctx.fillStyle = 'rgba(99, 102, 241, 0.3)';

        particles.forEach(p => {
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
            if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

            ctx.beginPath();
            ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
            ctx.fill();
        });

        particles.forEach((p1, i) => {
            particles.slice(i + 1).forEach(p2 => {
                const dx = p1.x - p2.x;
                const dy = p1.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 150) {
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }
            });
        });

        requestAnimationFrame(animate);
    }

    animate();
}

// Initialize
function initDashboard() {
    loadLiveStats();
    loadActivityFeed();
    loadAdStatusStats(); // Load ad status statistics
    loadViolations(); // Load moderation violations
    initNeuralNetwork();

    updateInterval = setInterval(() => {
        loadLiveStats();
        loadActivityFeed();
        loadAdStatusStats(); // Refresh ad stats
        loadViolations(); // Refresh violations
    }, 30000);

    setInterval(updateTimestamp, 1000);
    setInterval(updateSystemTime, 1000);
    updateSystemTime();
}

window.addEventListener('beforeunload', () => {
    if (updateInterval) clearInterval(updateInterval);
});

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}
</script>

</body>
</html>

