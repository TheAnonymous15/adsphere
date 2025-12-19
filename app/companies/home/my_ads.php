<?php
/********************************************
 * My Ads - AdSphere
 * Complete ad management interface
 ********************************************/
session_start();

// Block unauthorized access
if(!isset($_SESSION['company'])) {
    header("Location: /app/companies/handlers/login.php");
    exit();
}

$companySlug = $_SESSION['company'];
$companyName = $_SESSION['company_name'] ?? ucfirst($companySlug);

// Load company metadata for categories
$metaFile = __DIR__ . "/../metadata/{$companySlug}.json";
$companyData = [];
if (file_exists($metaFile)) {
    $companyData = json_decode(file_get_contents($metaFile), true);
}
$categories = $companyData['categories'] ?? [];
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Ads - AdSphere</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        .ad-card {
            transition: all 0.3s ease;
        }
        .ad-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(99, 102, 241, 0.3);
        }

        /* Glass effect - was missing */
        .glass-effect {
            background: rgba(30, 41, 59, 0.5);
            backdrop-filter: blur(10px);
        }

        /* Shimmer loading animation - was missing */
        .shimmer-loading {
            background: linear-gradient(90deg, rgba(255,255,255,0.05) 25%, rgba(255,255,255,0.1) 50%, rgba(255,255,255,0.05) 75%);
            background-size: 200% 100%;
            animation: shimmer 1.5s infinite;
        }
        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }

        @keyframes pulse-slow {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .loading {
            animation: pulse-slow 2s infinite;
        }
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* Expanded Chart Modal */
        .chart-expanded {
            position: fixed;
            inset: 0;
            z-index: 100;
            background: rgba(0, 0, 0, 0.9);
            backdrop-filter: blur(10px);
            display: flex;
            flex-direction: column;
            padding: 20px;
        }

        .chart-expanded .chart-container {
            flex: 1;
            min-height: 0;
        }

        /* Granularity Toggle Buttons */
        .granularity-toggle {
            display: flex;
            background: rgba(30, 41, 59, 0.8);
            border-radius: 8px;
            padding: 4px;
            gap: 4px;
        }

        .granularity-btn {
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s ease;
            cursor: pointer;
            border: none;
            background: transparent;
            color: #9ca3af;
        }

        .granularity-btn:hover {
            background: rgba(99, 102, 241, 0.2);
            color: #c7d2fe;
        }

        .granularity-btn.active {
            background: #6366f1;
            color: white;
        }

        /* Instant Tooltip Styles */
        [data-tooltip] {
            position: relative;
        }

        [data-tooltip]::before {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%) translateY(-4px);
            background: rgba(0, 0, 0, 0.95);
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 500;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.15s ease, transform 0.15s ease;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        [data-tooltip]::after {
            content: '';
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%) translateY(2px);
            border: 4px solid transparent;
            border-top-color: rgba(0, 0, 0, 0.95);
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.15s ease, transform 0.15s ease;
            z-index: 1000;
        }

        [data-tooltip]:hover::before,
        [data-tooltip]:hover::after {
            opacity: 1;
            transform: translateX(-50%) translateY(-8px);
        }

        [data-tooltip]:hover::after {
            transform: translateX(-50%) translateY(-2px);
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
                <a href="dashboard.php" class="flex items-center gap-3 hover:opacity-80 transition">
                    <div class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                        <i class="fas fa-ad text-white text-xl"></i>
                    </div>
                    <div>
                        <h1 class="text-xl font-bold text-white">My Ads</h1>
                        <p class="text-xs text-gray-400"><?= htmlspecialchars($companyName) ?></p>
                    </div>
                </a>
            </div>

            <!-- Navigation -->
            <div class="flex items-center gap-4">
                <a href="upload_ad.php" class="hidden sm:flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded-lg font-semibold transition">
                    <i class="fas fa-plus-circle"></i>
                    New Ad
                </a>
                <a href="dashboard.php" class="flex items-center gap-2 text-gray-300 hover:text-white transition">
                    <i class="fas fa-arrow-left"></i>
                    <span class="hidden sm:inline">Dashboard</span>
                </a>
            </div>
        </div>
    </div>
</nav>

<!-- MAIN CONTENT -->
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">


    <!-- HEADER WITH STATS -->
    <div class="mb-8">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
            <div>
                <h1 class="text-3xl sm:text-4xl font-bold mb-2">Your Advertisements</h1>
                <p class="text-gray-400">Manage all your active ads in one place</p>
            </div>
            <div class="flex items-center gap-4">
                <div class="bg-slate-800/50 backdrop-blur rounded-lg px-4 py-2 border border-white/10">
                    <p class="text-xs text-gray-400">Total Ads</p>
                    <p class="text-2xl font-bold" id="totalCount">-</p>
                </div>
            </div>
        </div>

        <!-- FILTERS AND SEARCH -->
        <div class="bg-slate-800/50 backdrop-blur rounded-xl p-4 border border-white/10 mb-6">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

                <!-- Search -->
                <div class="lg:col-span-2">
                    <label class="block text-sm font-medium mb-2">
                        <i class="fas fa-search mr-2"></i>Search Ads
                    </label>
                    <input
                        type="text"
                        id="searchInput"
                        placeholder="Search by title or description..."
                        class="w-full bg-slate-900 border border-gray-600 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                </div>

                <!-- Category Filter -->
                <div>
                    <label class="block text-sm font-medium mb-2">
                        <i class="fas fa-filter mr-2"></i>Category
                    </label>
                    <select
                        id="categoryFilter"
                        class="w-full bg-slate-900 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                        <option value="">All Categories</option>
                        <?php foreach($categories as $cat): ?>
                            <option value="<?= htmlspecialchars($cat) ?>"><?= htmlspecialchars(ucfirst($cat)) ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>

                <!-- Sort -->
                <div>
                    <label class="block text-sm font-medium mb-2">
                        <i class="fas fa-sort mr-2"></i>Sort By
                    </label>
                    <select
                        id="sortFilter"
                        class="w-full bg-slate-900 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                        <option value="newest">Newest First</option>
                        <option value="oldest">Oldest First</option>
                        <option value="most_viewed">Most Viewed</option>
                        <option value="most_favorites">Most Favorites</option>
                        <option value="most_likes">Most Likes</option>
                        <option value="title">Title A-Z</option>
                    </select>
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex flex-wrap gap-2 mt-4">
                <button onclick="clearFilters()" class="text-sm bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition">
                    <i class="fas fa-times mr-1"></i>Clear Filters
                </button>
                <button onclick="selectAll()" class="text-sm bg-indigo-600 hover:bg-indigo-700 px-4 py-2 rounded-lg transition">
                    <i class="fas fa-check-square mr-1"></i>Select All
                </button>
                <button onclick="deselectAll()" class="text-sm bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition">
                    <i class="fas fa-square mr-1"></i>Deselect All
                </button>
                <button onclick="deleteSelected()" class="text-sm bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg transition">
                    <i class="fas fa-trash mr-1"></i>Delete Selected
                </button>
            </div>
        </div>
    </div>
 <div id="adsContainer" class="hidden grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- JS will populate -->
    </div>

    <!-- CONTACT METHODS ANALYTICS -->
    <div class="mb-8" id="contactAnalyticsSection">
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
            <h2 class="text-2xl font-bold flex items-center gap-2">
                <i class="fas fa-phone-volume text-indigo-400"></i>
                Contact Performance
            </h2>
            <div class="flex items-center gap-2">
                <span class="text-xs text-gray-400">Date Range:</span>
                <select id="myAdsDateRange" onchange="updateMyAdsContactAnalytics()" class="text-xs bg-slate-800 border border-gray-600 rounded-lg px-3 py-1.5 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
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
                <span class="text-2xl font-bold text-indigo-400" id="myAdsTotalEngagements">0</span>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div class="bg-slate-900/50 rounded-lg p-3 text-center">
                    <p class="text-xs text-gray-400 mb-1">WhatsApp</p>
                    <p class="text-xl font-bold text-green-400" id="myAdsWhatsappTotal">0</p>
                </div>
                <div class="bg-slate-900/50 rounded-lg p-3 text-center">
                    <p class="text-xs text-gray-400 mb-1">Phone Calls</p>
                    <p class="text-xl font-bold text-blue-400" id="myAdsCallTotal">0</p>
                </div>
                <div class="bg-slate-900/50 rounded-lg p-3 text-center">
                    <p class="text-xs text-gray-400 mb-1">SMS</p>
                    <p class="text-xl font-bold text-purple-400" id="myAdsSmsTotal">0</p>
                </div>
                <div class="bg-slate-900/50 rounded-lg p-3 text-center">
                    <p class="text-xs text-gray-400 mb-1">Email</p>
                    <p class="text-xl font-bold text-red-400" id="myAdsEmailTotal">0</p>
                </div>
            </div>
        </div>

        <!-- Contact Stats Grid with Toggles -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div class="glass-effect rounded-xl p-4 border border-white/10 hover:border-green-500/50 transition cursor-pointer" onclick="toggleMyAdsMethod('whatsapp', event)">
                <div class="flex items-center justify-between mb-2">
                    <i class="fab fa-whatsapp text-green-400 text-2xl"></i>
                    <div class="flex items-center gap-2">
                        <input type="checkbox" id="myAdsShowWhatsapp" checked onclick="event.stopPropagation()" onchange="handleCheckboxChange('whatsapp', this)" class="w-4 h-4 rounded bg-slate-900 border-gray-600 text-green-600 focus:ring-2 focus:ring-green-500">
                        <span class="text-xs text-gray-400">Show</span>
                    </div>
                </div>
                <p class="text-3xl font-bold" id="myAdsWhatsappCount">0</p>
                <p class="text-xs text-gray-400 mt-1">WhatsApp Contacts</p>
            </div>

            <div class="glass-effect rounded-xl p-4 border border-white/10 hover:border-blue-500/50 transition cursor-pointer" onclick="toggleMyAdsMethod('call', event)">
                <div class="flex items-center justify-between mb-2">
                    <i class="fas fa-phone text-blue-400 text-2xl"></i>
                    <div class="flex items-center gap-2">
                        <input type="checkbox" id="myAdsShowCall" checked onclick="event.stopPropagation()" onchange="handleCheckboxChange('call', this)" class="w-4 h-4 rounded bg-slate-900 border-gray-600 text-blue-600 focus:ring-2 focus:ring-blue-500">
                        <span class="text-xs text-gray-400">Show</span>
                    </div>
                </div>
                <p class="text-3xl font-bold" id="myAdsCallCount">0</p>
                <p class="text-xs text-gray-400 mt-1">Phone Calls</p>
            </div>

            <div class="glass-effect rounded-xl p-4 border border-white/10 hover:border-purple-500/50 transition cursor-pointer" onclick="toggleMyAdsMethod('sms', event)">
                <div class="flex items-center justify-between mb-2">
                    <i class="fas fa-sms text-purple-400 text-2xl"></i>
                    <div class="flex items-center gap-2">
                        <input type="checkbox" id="myAdsShowSms" checked onclick="event.stopPropagation()" onchange="handleCheckboxChange('sms', this)" class="w-4 h-4 rounded bg-slate-900 border-gray-600 text-purple-600 focus:ring-2 focus:ring-purple-500">
                        <span class="text-xs text-gray-400">Show</span>
                    </div>
                </div>
                <p class="text-3xl font-bold" id="myAdsSmsCount">0</p>
                <p class="text-xs text-gray-400 mt-1">Text Messages</p>
            </div>

            <div class="glass-effect rounded-xl p-4 border border-white/10 hover:border-red-500/50 transition cursor-pointer" onclick="toggleMyAdsMethod('email', event)">
                <div class="flex items-center justify-between mb-2">
                    <i class="fas fa-envelope text-red-400 text-2xl"></i>
                    <div class="flex items-center gap-2">
                        <input type="checkbox" id="myAdsShowEmail" checked onclick="event.stopPropagation()" onchange="handleCheckboxChange('email', this)" class="w-4 h-4 rounded bg-slate-900 border-gray-600 text-red-600 focus:ring-2 focus:ring-red-500">
                        <span class="text-xs text-gray-400">Show</span>
                    </div>
                </div>
                <p class="text-3xl font-bold" id="myAdsEmailCount">0</p>
                <p class="text-xs text-gray-400 mt-1">Email Contacts</p>
            </div>
        </div>

        <!-- Line Chart -->
        <div id="chartContainer" class="glass-effect rounded-xl p-6 border border-white/10 mb-6">
            <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
                <h3 class="text-lg font-bold flex items-center gap-2">
                    <i class="fas fa-chart-line text-indigo-400"></i>
                    Contact Methods Trend
                </h3>
                <div class="flex flex-wrap items-center gap-3">
                    <!-- Granularity Toggle -->
                    <div class="granularity-toggle">
                        <button onclick="setChartGranularity('daily')" class="granularity-btn active" id="granularityDaily">
                            <i class="fas fa-calendar-day mr-1"></i>Daily
                        </button>
                        <button onclick="setChartGranularity('weekly')" class="granularity-btn" id="granularityWeekly">
                            <i class="fas fa-calendar-week mr-1"></i>Weekly
                        </button>
                        <button onclick="setChartGranularity('monthly')" class="granularity-btn" id="granularityMonthly">
                            <i class="fas fa-calendar-alt mr-1"></i>Monthly
                        </button>
                        <button onclick="setChartGranularity('annually')" class="granularity-btn" id="granularityAnnually">
                            <i class="fas fa-calendar mr-1"></i>Annually
                        </button>
                    </div>

                    <!-- Expand Button -->
                    <button onclick="toggleExpandChart()" class="text-xs bg-slate-700 hover:bg-slate-600 px-3 py-1.5 rounded-lg transition flex items-center gap-1" id="expandChartBtn">
                        <i class="fas fa-expand"></i>
                        <span class="hidden sm:inline">Expand</span>
                    </button>

                    <button onclick="selectAllMyAdsMethods()" class="text-xs bg-indigo-600 hover:bg-indigo-700 px-3 py-1.5 rounded-lg transition">
                        <i class="fas fa-check-square mr-1"></i>Select All
                    </button>
                    <button onclick="deselectAllMyAdsMethods()" class="text-xs bg-gray-700 hover:bg-gray-600 px-3 py-1.5 rounded-lg transition">
                        <i class="fas fa-square mr-1"></i>Deselect All
                    </button>
                </div>
            </div>
            <div class="chart-container" style="position: relative; height: 350px;" id="chartWrapper">
                <canvas id="myAdsContactChart"></canvas>
            </div>

            <!-- Close button (only visible when expanded) -->
            <button onclick="toggleExpandChart()" class="hidden absolute top-4 right-4 bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg transition" id="closeExpandBtn">
                <i class="fas fa-compress mr-2"></i>Close
            </button>
        </div>

        <!-- AI Insights -->
        <div class="mb-6">
            <h3 class="text-xl font-bold mb-4 flex items-center gap-2">
                <i class="fas fa-robot text-purple-400"></i>
                AI Insights & Recommendations
            </h3>
            <div id="myAdsContactInsights" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
                <!-- Will be populated by JS -->
                <div class="glass-effect rounded-xl p-4 shimmer-loading h-32"></div>
                <div class="glass-effect rounded-xl p-4 shimmer-loading h-32"></div>
            </div>
        </div>
    </div>

    <!-- LOADING STATE -->
    <div id="loadingState" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div class="bg-slate-800/50 rounded-xl h-96 animate-pulse"></div>
        <div class="bg-slate-800/50 rounded-xl h-96 animate-pulse"></div>
        <div class="bg-slate-800/50 rounded-xl h-96 animate-pulse"></div>
    </div>

    <!-- ADS CONTAINER -->


    <!-- EMPTY STATE -->
    <div id="emptyState" class="hidden bg-slate-800/30 rounded-xl p-12 text-center">
        <i class="fas fa-rectangle-ad text-6xl text-gray-600 mb-4"></i>
        <h3 class="text-xl font-bold mb-2">No ads found</h3>
        <p class="text-gray-400 mb-6">Start by posting your first advertisement or adjust your filters</p>
        <a href="upload_ad.php" class="inline-block bg-indigo-600 hover:bg-indigo-700 px-6 py-3 rounded-lg font-semibold transition">
            <i class="fas fa-plus-circle mr-2"></i>Post Your First Ad
        </a>
    </div>

    <!-- NO RESULTS STATE -->
    <div id="noResults" class="hidden bg-slate-800/30 rounded-xl p-12 text-center">
        <i class="fas fa-search text-6xl text-gray-600 mb-4"></i>
        <h3 class="text-xl font-bold mb-2">No ads match your search</h3>
        <p class="text-gray-400 mb-6">Try adjusting your filters or search terms</p>
        <button onclick="clearFilters()" class="bg-indigo-600 hover:bg-indigo-700 px-6 py-3 rounded-lg font-semibold transition">
            <i class="fas fa-times mr-2"></i>Clear Filters
        </button>
    </div>
</div>

<!-- DELETE CONFIRMATION MODAL -->
<div id="deleteModal" class="hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-slate-900 rounded-2xl w-full max-w-md p-6 shadow-2xl transform scale-95 opacity-0 transition-all duration-300" id="deleteModalCard">
        <div class="text-center mb-6">
            <div class="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <i class="fas fa-exclamation-triangle text-red-400 text-3xl"></i>
            </div>
            <h3 class="text-2xl font-bold mb-2">Delete Advertisement?</h3>
            <p class="text-gray-400" id="deleteMessage">This action cannot be undone.</p>
        </div>

        <div class="flex gap-3">
            <button onclick="closeDeleteModal()" class="flex-1 bg-gray-700 hover:bg-gray-600 py-3 rounded-lg font-semibold transition">
                Cancel
            </button>
            <button onclick="confirmDelete()" class="flex-1 bg-red-600 hover:bg-red-700 py-3 rounded-lg font-semibold transition">
                Delete
            </button>
        </div>
    </div>
</div>

<!-- SCHEDULE MODAL -->
<div id="scheduleModal" class="hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-slate-900 rounded-2xl w-full max-w-md p-6 shadow-2xl transform scale-95 opacity-0 transition-all duration-300" id="scheduleModalCard">
        <div class="mb-6">
            <div class="w-16 h-16 bg-cyan-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <i class="fas fa-calendar text-cyan-400 text-3xl"></i>
            </div>
            <h3 class="text-2xl font-bold text-center mb-2">Schedule Advertisement</h3>
            <p class="text-gray-400 text-center" id="scheduleAdTitle"></p>
        </div>

        <div class="space-y-4 mb-6">
            <div>
                <label class="block text-sm font-medium mb-2">Start Date (Optional)</label>
                <input type="datetime-local" id="scheduleStartDate" class="w-full bg-slate-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500">
            </div>
            <div>
                <label class="block text-sm font-medium mb-2">End Date (Optional)</label>
                <input type="datetime-local" id="scheduleEndDate" class="w-full bg-slate-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-cyan-500">
            </div>
            <div>
                <label class="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" id="scheduleAutoRenew" class="w-4 h-4 text-cyan-600 bg-slate-800 border-gray-600 rounded focus:ring-cyan-500">
                    <span class="text-sm">Auto-renew when expired</span>
                </label>
            </div>
        </div>

        <div class="flex gap-3">
            <button onclick="closeScheduleModal()" class="flex-1 bg-gray-700 hover:bg-gray-600 py-3 rounded-lg font-semibold transition">
                Cancel
            </button>
            <button onclick="confirmSchedule()" class="flex-1 bg-cyan-600 hover:bg-cyan-700 py-3 rounded-lg font-semibold transition">
                Save Schedule
            </button>
        </div>
    </div>
</div>

<!-- BOOST/PROMOTE MODAL -->
<div id="boostModal" class="hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-slate-900 rounded-2xl w-full max-w-md p-6 shadow-2xl transform scale-95 opacity-0 transition-all duration-300" id="boostModalCard">
        <div class="text-center mb-6">
            <div class="w-16 h-16 bg-orange-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <i class="fas fa-rocket text-orange-400 text-3xl"></i>
            </div>
            <h3 class="text-2xl font-bold mb-2">Boost Advertisement</h3>
            <p class="text-gray-400" id="boostAdTitle"></p>
        </div>

        <div class="space-y-4 mb-6">
            <div class="bg-slate-800 rounded-lg p-4">
                <h4 class="font-bold mb-2">Premium Placement</h4>
                <p class="text-sm text-gray-400 mb-3">Feature your ad at the top for 7 days</p>
                <p class="text-2xl font-bold text-orange-400">$29.99</p>
            </div>
            <div class="bg-slate-800 rounded-lg p-4">
                <h4 class="font-bold mb-2">Social Media Promotion</h4>
                <p class="text-sm text-gray-400 mb-3">Share on our social media channels</p>
                <p class="text-2xl font-bold text-orange-400">$19.99</p>
            </div>
            <p class="text-xs text-gray-500 text-center">Payment integration coming soon</p>
        </div>

        <div class="flex gap-3">
            <button onclick="closeBoostModal()" class="flex-1 bg-gray-700 hover:bg-gray-600 py-3 rounded-lg font-semibold transition">
                Close
            </button>
            <button onclick="confirmBoost()" class="flex-1 bg-orange-600 hover:bg-orange-700 py-3 rounded-lg font-semibold transition">
                Select Plan
            </button>
        </div>
    </div>
</div>

<!-- ANALYTICS MODAL -->
<div id="analyticsModal" class="hidden fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="bg-slate-900 rounded-2xl w-full max-w-2xl p-6 shadow-2xl transform scale-95 opacity-0 transition-all duration-300" id="analyticsModalCard">
        <div class="flex justify-between items-center mb-6">
            <h3 class="text-2xl font-bold">Ad Analytics</h3>
            <button onclick="closeAnalyticsModal()" class="text-gray-400 hover:text-white">
                <i class="fas fa-times text-2xl"></i>
            </button>
        </div>

        <div id="analyticsContent" class="space-y-4">
            <!-- Will be populated by JavaScript -->
        </div>
    </div>
</div>

<script>
/********************************************
 * My Ads JavaScript
 * Handles ad loading, filtering, and management
 ********************************************/

const companySlug = "<?= $companySlug ?>";
let allAds = [];
let filteredAds = [];
let selectedAds = new Set();
let deleteTarget = null;

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
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ============================================
// AI PERFORMANCE PREDICTOR
// ============================================
function predictPerformance(ad) {
    let score = 50; // Base score

    // Title quality (0-20 points)
    const titleLength = (ad.title || '').length;
    if (titleLength >= 20 && titleLength <= 60) score += 20;
    else if (titleLength >= 10 && titleLength <= 80) score += 10;

    // Description quality (0-20 points)
    const descLength = (ad.description || '').length;
    if (descLength >= 100 && descLength <= 500) score += 20;
    else if (descLength >= 50 && descLength <= 1000) score += 10;

    // Historical performance (0-30 points)
    const views = ad.analytics?.total_views || 0;
    const contacts = ad.analytics?.total_contacts || 0;
    const favorites = ad.analytics?.current_favorites || 0;
    const likes = ad.analytics?.total_likes || 0;

    if (views > 100) score += 10;
    else if (views > 50) score += 5;

    if (contacts > 10) score += 10;
    else if (contacts > 5) score += 5;

    if (favorites > 20) score += 5;
    else if (favorites > 10) score += 3;

    if (likes > 10) score += 5;
    else if (likes > 5) score += 2;

    // Engagement rate (0-10 points)
    if (views > 0) {
        const engagementRate = ((contacts + favorites + likes) / views) * 100;
        if (engagementRate > 10) score += 10;
        else if (engagementRate > 5) score += 5;
    }

    // Recency bonus (0-10 points)
    const daysSincePosted = (Date.now() / 1000 - ad.timestamp) / 86400;
    if (daysSincePosted < 7) score += 10;
    else if (daysSincePosted < 30) score += 5;

    // Cap at 100
    return Math.min(100, Math.round(score));
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
// LOAD ADS
// ============================================
async function loadAds() {
    try {
        const [adsRes, analyticsRes] = await Promise.all([
            fetch("/app/api/get_ads.php"),
            fetch("/app/api/get_analytics.php")
        ]);

        const adsData = await adsRes.json();
        const analyticsData = await analyticsRes.json();

        // Filter ads for this company
        allAds = adsData.ads.filter(ad => ad.company === companySlug);

        // Merge analytics data with ads
        if (analyticsData.success && analyticsData.analytics) {
            allAds = allAds.map(ad => ({
                ...ad,
                analytics: analyticsData.analytics[ad.ad_id] || {
                    total_views: 0,
                    total_clicks: 0,
                    total_contacts: 0
                }
            }));
        }

        filteredAds = [...allAds];

        applyFilters();
        loadMyAdsContactAnalytics();

    } catch (error) {
        console.error("Failed to load ads:", error);
        showError();
    }
}

// ============================================
// CONTACT ANALYTICS FOR MY ADS
// ============================================
let myAdsContactChart = null;
let myAdsContactData = null;
let myAdsVisibleMethods = {
    whatsapp: true,
    call: true,
    sms: true,
    email: true
};
let chartGranularity = 'daily';
let isChartExpanded = false;

async function loadMyAdsContactAnalytics() {
    const dateRange = document.getElementById('myAdsDateRange')?.value || '30';

    try {
        const response = await fetch(`/app/api/contact_analytics.php?days=${dateRange}`);
        const data = await response.json();

        console.log('Contact Analytics API Response:', data);

        if (!data.success) {
            console.error('API returned success=false');
            return;
        }

        myAdsContactData = data;

        console.log('=== CONTACT ANALYTICS DEBUG ===');
        console.log('API Debug Info:', data.debug);
        console.log('Files Scanned:', data.debug?.scanned_files);
        console.log('Contact Events Found:', data.debug?.contact_events);
        console.log('Methods Found in Files:', data.debug?.methods_found);
        console.log('Unrecognized Methods:', data.debug?.unrecognized_methods);
        console.log('Counts After Loop:', data.debug?.counts_after_loop);
        console.log('Final Counts from API:', data.debug?.final_counts);
        console.log('---');
        console.log('Contact Methods Data:', data.contact_methods);
        console.log('WhatsApp count:', data.contact_methods.whatsapp.count);
        console.log('Call count:', data.contact_methods.call.count);
        console.log('SMS count:', data.contact_methods.sms.count);
        console.log('Email count:', data.contact_methods.email.count);

        // Calculate total engagements
        const total = data.contact_methods.whatsapp.count +
                     data.contact_methods.call.count +
                     data.contact_methods.sms.count +
                     data.contact_methods.email.count;

        console.log('Total engagements calculated:', total);

        // Update total engagement
        const totalElem = document.getElementById('myAdsTotalEngagements');
        const whatsappTotalElem = document.getElementById('myAdsWhatsappTotal');
        const callTotalElem = document.getElementById('myAdsCallTotal');
        const smsTotalElem = document.getElementById('myAdsSmsTotal');
        const emailTotalElem = document.getElementById('myAdsEmailTotal');

        console.log('Total Engagements Element:', totalElem);
        console.log('WhatsApp Total Element:', whatsappTotalElem);

        if (totalElem) totalElem.textContent = total.toLocaleString();
        if (whatsappTotalElem) whatsappTotalElem.textContent = data.contact_methods.whatsapp.count.toLocaleString();
        if (callTotalElem) callTotalElem.textContent = data.contact_methods.call.count.toLocaleString();
        if (smsTotalElem) smsTotalElem.textContent = data.contact_methods.sms.count.toLocaleString();
        if (emailTotalElem) emailTotalElem.textContent = data.contact_methods.email.count.toLocaleString();

        // Update counts
        const whatsappCountElem = document.getElementById('myAdsWhatsappCount');
        const callCountElem = document.getElementById('myAdsCallCount');
        const smsCountElem = document.getElementById('myAdsSmsCount');
        const emailCountElem = document.getElementById('myAdsEmailCount');

        if (whatsappCountElem) whatsappCountElem.textContent = data.contact_methods.whatsapp.count.toLocaleString();
        if (callCountElem) callCountElem.textContent = data.contact_methods.call.count.toLocaleString();
        if (smsCountElem) smsCountElem.textContent = data.contact_methods.sms.count.toLocaleString();
        if (emailCountElem) emailCountElem.textContent = data.contact_methods.email.count.toLocaleString();

        // Render chart
        renderMyAdsContactChart(data.contact_methods);

        // Display insights
        displayMyAdsInsights(data);

    } catch (error) {
        console.error('Failed to load contact analytics:', error);
    }
}

async function updateMyAdsContactAnalytics() {
    await loadMyAdsContactAnalytics();
}

function getCheckboxId(method) {
    // Map method names to their checkbox IDs
    const idMap = {
        'whatsapp': 'myAdsShowWhatsapp',
        'call': 'myAdsShowCall',
        'sms': 'myAdsShowSms',
        'email': 'myAdsShowEmail'
    };
    return idMap[method];
}

function toggleMyAdsMethod(method, event) {
    // Only toggle if clicking on the card itself, not the checkbox
    if (event && event.target.tagName === 'INPUT') {
        return;
    }

    const checkboxId = getCheckboxId(method);
    const checkbox = document.getElementById(checkboxId);

    console.log('toggleMyAdsMethod called:', method, 'checkbox:', checkboxId, checkbox);

    if (checkbox) {
        checkbox.checked = !checkbox.checked;
        myAdsVisibleMethods[method] = checkbox.checked;

        if (myAdsContactData) {
            renderMyAdsContactChart(myAdsContactData.contact_methods);
        }
    }
}

function handleCheckboxChange(method, checkbox) {
    myAdsVisibleMethods[method] = checkbox.checked;

    if (myAdsContactData) {
        renderMyAdsContactChart(myAdsContactData.contact_methods);
    }
}

function selectAllMyAdsMethods() {
    ['whatsapp', 'call', 'sms', 'email'].forEach(method => {
        const checkboxId = getCheckboxId(method);
        const checkbox = document.getElementById(checkboxId);
        if (checkbox) {
            checkbox.checked = true;
            myAdsVisibleMethods[method] = true;
        }
    });

    if (myAdsContactData) {
        renderMyAdsContactChart(myAdsContactData.contact_methods);
    }
}

function deselectAllMyAdsMethods() {
    ['whatsapp', 'call', 'sms', 'email'].forEach(method => {
        const checkboxId = getCheckboxId(method);
        const checkbox = document.getElementById(checkboxId);
        if (checkbox) {
            checkbox.checked = false;
            myAdsVisibleMethods[method] = false;
        }
    });

    if (myAdsContactData) {
        renderMyAdsContactChart(myAdsContactData.contact_methods);
    }
}

function toggleExpandChart() {
    const container = document.getElementById('chartContainer');
    const expandBtn = document.getElementById('expandChartBtn');
    const closeBtn = document.getElementById('closeExpandBtn');
    const chartWrapper = document.getElementById('chartWrapper');

    isChartExpanded = !isChartExpanded;

    if (isChartExpanded) {
        // Expand
        container.classList.add('chart-expanded');
        chartWrapper.style.height = 'calc(100vh - 200px)';
        expandBtn.classList.add('hidden');
        closeBtn.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
    } else {
        // Collapse
        container.classList.remove('chart-expanded');
        chartWrapper.style.height = '350px';
        expandBtn.classList.remove('hidden');
        closeBtn.classList.add('hidden');
        document.body.style.overflow = '';
    }

    // Re-render chart to fit new size
    setTimeout(() => {
        if (myAdsContactData) {
            renderMyAdsContactChart(myAdsContactData.contact_methods);
        }
    }, 100);
}

// Close expanded chart on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isChartExpanded) {
        toggleExpandChart();
    }
});

function setChartGranularity(granularity) {
    chartGranularity = granularity;

    // Update active button state
    ['daily', 'weekly', 'monthly', 'annually'].forEach(g => {
        const btn = document.getElementById(`granularity${g.charAt(0).toUpperCase() + g.slice(1)}`);
        if (btn) {
            if (g === granularity) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        }
    });

    // Re-render chart with new granularity
    if (myAdsContactData) {
        renderMyAdsContactChart(myAdsContactData.contact_methods);
    }
}

function aggregateDataByGranularity(trendData, granularity) {
    if (!trendData || trendData.length === 0) return { labels: [], data: [] };

    const aggregated = {};

    trendData.forEach(item => {
        const date = new Date(item.date);
        let key;

        switch (granularity) {
            case 'daily':
                key = item.date;
                break;
            case 'weekly':
                // Get the start of the week (Sunday)
                const weekStart = new Date(date);
                weekStart.setDate(date.getDate() - date.getDay());
                key = weekStart.toISOString().split('T')[0];
                break;
            case 'monthly':
                key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
                break;
            case 'annually':
                key = `${date.getFullYear()}`;
                break;
            default:
                key = item.date;
        }

        if (!aggregated[key]) {
            aggregated[key] = 0;
        }
        aggregated[key] += item.count || 0;
    });

    // Sort keys chronologically
    const sortedKeys = Object.keys(aggregated).sort();

    // Format labels based on granularity
    const labels = sortedKeys.map(key => {
        switch (granularity) {
            case 'daily':
                return key;
            case 'weekly':
                return `Week of ${key}`;
            case 'monthly':
                const [year, month] = key.split('-');
                const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                return `${monthNames[parseInt(month) - 1]} ${year}`;
            case 'annually':
                return key;
            default:
                return key;
        }
    });

    const data = sortedKeys.map(key => aggregated[key]);

    return { labels, data, keys: sortedKeys };
}

function renderMyAdsContactChart(contactMethods) {
    const ctx = document.getElementById('myAdsContactChart');
    if (!ctx) return;

    // Guard: Chart library available
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js not loaded yet. Skipping chart render.');
        return;
    }

    if (myAdsContactChart) {
        myAdsContactChart.destroy();
    }

    // Aggregate data based on current granularity
    const whatsappAgg = aggregateDataByGranularity(contactMethods.whatsapp?.trend || [], chartGranularity);
    const callAgg = aggregateDataByGranularity(contactMethods.call?.trend || [], chartGranularity);
    const smsAgg = aggregateDataByGranularity(contactMethods.sms?.trend || [], chartGranularity);
    const emailAgg = aggregateDataByGranularity(contactMethods.email?.trend || [], chartGranularity);

    // Get all unique labels/dates
    const allKeys = new Set([
        ...whatsappAgg.keys || [],
        ...callAgg.keys || [],
        ...smsAgg.keys || [],
        ...emailAgg.keys || []
    ]);
    const sortedKeys = Array.from(allKeys).sort();

    // Create maps for easy lookup
    const createDataMap = (agg) => {
        const map = {};
        (agg.keys || []).forEach((key, i) => {
            map[key] = agg.data[i];
        });
        return map;
    };

    const whatsappMap = createDataMap(whatsappAgg);
    const callMap = createDataMap(callAgg);
    const smsMap = createDataMap(smsAgg);
    const emailMap = createDataMap(emailAgg);

    // Format labels based on granularity
    const formatLabel = (key) => {
        switch (chartGranularity) {
            case 'daily':
                return key;
            case 'weekly':
                return `Week of ${key}`;
            case 'monthly':
                const [year, month] = key.split('-');
                const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
                return `${monthNames[parseInt(month) - 1]} ${year}`;
            case 'annually':
                return key;
            default:
                return key;
        }
    };

    const labels = sortedKeys.map(formatLabel);

    const datasets = [];

    if (myAdsVisibleMethods.whatsapp) {
        datasets.push({
            label: 'WhatsApp',
            data: sortedKeys.map(k => whatsappMap[k] ?? 0),
            backgroundColor: 'rgba(37, 211, 102, 0.8)',
            borderColor: '#25d366',
            borderWidth: 1,
            borderRadius: 4,
            hoverBackgroundColor: '#25d366',
            order: 3
        });
    }

    if (myAdsVisibleMethods.call) {
        datasets.push({
            label: 'Phone Call',
            data: sortedKeys.map(k => callMap[k] ?? 0),
            backgroundColor: 'rgba(59, 130, 246, 0.8)',
            borderColor: '#3b82f6',
            borderWidth: 1,
            borderRadius: 4,
            hoverBackgroundColor: '#3b82f6',
            order: 2
        });
    }

    if (myAdsVisibleMethods.sms) {
        datasets.push({
            label: 'SMS',
            data: sortedKeys.map(k => smsMap[k] ?? 0),
            backgroundColor: 'rgba(168, 85, 247, 0.8)',
            borderColor: '#a855f7',
            borderWidth: 1,
            borderRadius: 4,
            hoverBackgroundColor: '#a855f7',
            order: 4
        });
    }

    if (myAdsVisibleMethods.email) {
        datasets.push({
            label: 'Email',
            data: sortedKeys.map(k => emailMap[k] ?? 0),
            backgroundColor: 'rgba(239, 68, 68, 0.8)',
            borderColor: '#ef4444',
            borderWidth: 1,
            borderRadius: 4,
            hoverBackgroundColor: '#ef4444',
            order: 1
        });
    }

    if (datasets.length === 0 || labels.length === 0) {
        const c2d = ctx.getContext('2d');
        c2d.clearRect(0, 0, ctx.width, ctx.height);
        return;
    }

    // Detect if all series are zero to avoid "invisible at baseline" confusion
    const allZero = datasets.every(ds => (ds.data || []).every(v => v === 0));

    // Get granularity label for title
    const granularityLabels = {
        'daily': 'Daily',
        'weekly': 'Weekly',
        'monthly': 'Monthly',
        'annually': 'Annual'
    };

    myAdsContactChart = new Chart(ctx, {
        type: 'bar',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { top: 8, right: 8, bottom: 8, left: 8 } },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: '#fff',
                        usePointStyle: true,
                        padding: isChartExpanded ? 20 : 15,
                        font: { size: isChartExpanded ? 14 : 12, weight: '600' }
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
                    titleFont: { size: isChartExpanded ? 14 : 12 },
                    bodyFont: { size: isChartExpanded ? 13 : 11 },
                    callbacks: {
                        title: function(context) {
                            return `${granularityLabels[chartGranularity]} View: ${context[0].label}`;
                        },
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) label += ': ';
                            label += context.parsed.y + ' contacts';
                            return label;
                        }
                    }
                },
                // Optional message when all zero
                title: allZero ? { display: true, text: 'No contact activity in selected period', color: '#9ca3af', font: { size: 12 } } : {
                    display: isChartExpanded,
                    text: `${granularityLabels[chartGranularity]} Contact Methods Trend`,
                    color: '#fff',
                    font: { size: 18, weight: 'bold' },
                    padding: { bottom: 20 }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grace: '5%',
                    grid: { color: 'rgba(255, 255, 255, 0.1)', drawBorder: false },
                    ticks: {
                        color: '#9ca3af',
                        font: { size: isChartExpanded ? 13 : 11 },
                        padding: 8
                    },
                    title: {
                        display: true,
                        text: 'Number of Contacts',
                        color: '#9ca3af',
                        font: { size: isChartExpanded ? 14 : 12, weight: '600' }
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: {
                        color: '#9ca3af',
                        maxRotation: 45,
                        minRotation: chartGranularity === 'daily' ? 45 : 0,
                        font: { size: isChartExpanded ? 12 : 10 }
                    }
                }
            },
            interaction: { mode: 'index', intersect: false }
        }
    });
}

function displayMyAdsInsights(data) {
    const container = document.getElementById('myAdsContactInsights');
    if (!container || !data.ai_insights) return;

    const insights = data.ai_insights;

    if (insights.length === 0) {
        container.innerHTML = '<div class="col-span-full glass-effect rounded-xl p-6 text-center border border-white/10"><i class="fas fa-chart-line text-gray-600 text-4xl mb-3"></i><p class="text-gray-400">Start getting contacts to see AI-powered insights!</p></div>';
        return;
    }

    const insightColors = {
        'demographics': 'from-blue-500/20 to-purple-500/20 border-blue-500/50',
        'contact_preference': 'from-green-500/20 to-emerald-500/20 border-green-500/50',
        'timing': 'from-yellow-500/20 to-orange-500/20 border-yellow-500/50',
        'content': 'from-pink-500/20 to-red-500/20 border-pink-500/50'
    };

    container.innerHTML = insights.map(insight =>
        '<div class="glass-effect bg-gradient-to-br ' + (insightColors[insight.type] || 'from-indigo-500/20 to-purple-500/20 border-indigo-500/50') + ' border rounded-xl p-5 hover:scale-[1.02] transition-all">' +
            '<div class="flex items-start gap-3 mb-3">' +
                '<div class="w-12 h-12 rounded-full bg-white/10 flex items-center justify-center flex-shrink-0">' +
                    '<i class="fas ' + insight.icon + ' text-2xl"></i>' +
                '</div>' +
                '<div class="flex-1">' +
                    '<h4 class="font-bold text-lg mb-1">' + escapeHtml(insight.title) + '</h4>' +
                    '<p class="text-sm text-gray-200">' + escapeHtml(insight.message) + '</p>' +
                '</div>' +
            '</div>' +
            '<div class="bg-black/30 rounded-lg p-3 border-l-4 border-yellow-400">' +
                '<p class="text-xs text-gray-300 flex items-start gap-2">' +
                    '<i class="fas fa-lightbulb text-yellow-400 mt-1"></i>' +
                    '<span><strong>AI Recommendation:</strong> ' + escapeHtml(insight.recommendation) + '</span>' +
                '</p>' +
            '</div>' +
        '</div>'
    ).join('');
}

// ============================================
// RENDER ADS
// ============================================
function renderAds(ads) {
    const container = document.getElementById('adsContainer');
    const loading = document.getElementById('loadingState');
    const emptyState = document.getElementById('emptyState');
    const noResults = document.getElementById('noResults');

    loading.classList.add('hidden');
    container.classList.add('hidden');
    emptyState.classList.add('hidden');
    noResults.classList.add('hidden');

    // Update total count
    document.getElementById('totalCount').textContent = allAds.length;

    if (allAds.length === 0) {
        emptyState.classList.remove('hidden');
        return;
    }

    if (ads.length === 0) {
        noResults.classList.remove('hidden');
        return;
    }

    container.classList.remove('hidden');

    container.innerHTML = ads.map(ad => {
        const isVideo = ad.media && /\.(mp4|mov|webm)$/i.test(ad.media);
        const isSelected = selectedAds.has(ad.ad_id);

        return `
            <div class="ad-card bg-slate-800/50 backdrop-blur rounded-xl overflow-hidden border ${isSelected ? 'border-indigo-500 ring-2 ring-indigo-500' : 'border-white/10'} hover:border-indigo-500/50 transition fade-in">

                <!-- Selection Checkbox -->
                <div class="absolute top-4 left-4 z-10">
                    <input
                        type="checkbox"
                        class="w-5 h-5 rounded bg-slate-900 border-gray-600 text-indigo-600 focus:ring-2 focus:ring-indigo-500 cursor-pointer"
                        onchange="toggleSelect('${ad.ad_id}')"
                        ${isSelected ? 'checked' : ''}>
                </div>

                <!-- Media -->
                <div class="relative h-56 bg-slate-700 overflow-hidden">
                    ${isVideo ?
                        `<video class="w-full h-full object-cover" muted loop onmouseover="this.play()" onmouseout="this.pause()">
                            <source src="${escapeHtml(ad.media)}">
                        </video>` :
                        `<img src="${escapeHtml(ad.media)}" alt="${escapeHtml(ad.title)}" class="w-full h-full object-cover">`
                    }

                    <!-- Category Badge -->
                    <div class="absolute top-4 right-4">
                        <span class="bg-black/70 backdrop-blur px-3 py-1 rounded-full text-xs font-medium">
                            <i class="fas fa-tag mr-1"></i>${escapeHtml(ad.category)}
                        </span>
                    </div>

                    <!-- Status Badge -->
                    <div class="absolute bottom-4 right-4">
                        ${(ad.status || 'active') === 'active' ?
                            `<span class="bg-green-500 px-3 py-1 rounded-full text-xs font-bold">
                                <i class="fas fa-circle text-xs mr-1"></i>Active
                            </span>` :
                            `<span class="bg-yellow-500 px-3 py-1 rounded-full text-xs font-bold">
                                <i class="fas fa-pause text-xs mr-1"></i>Paused
                            </span>`
                        }
                    </div>
                </div>

                <!-- Content -->
                <div class="p-5">
                    <h3 class="font-bold text-xl mb-2 line-clamp-1">${escapeHtml(ad.title)}</h3>
                    <p class="text-sm text-gray-400 mb-4 line-clamp-2">${escapeHtml(ad.description || 'No description')}</p>

                    <!-- Performance Predictor -->
                    ${(() => {
                        const score = predictPerformance(ad);
                        const scoreColor = score >= 80 ? 'green' : score >= 50 ? 'yellow' : 'red';
                        const scoreIcon = score >= 80 ? 'fa-fire' : score >= 50 ? 'fa-chart-line' : 'fa-exclamation-triangle';
                        return `
                            <div class="mb-3 p-2 rounded-lg bg-${scoreColor}-600/20 border border-${scoreColor}-600/50 flex items-center gap-2">
                                <i class="fas ${scoreIcon} text-${scoreColor}-400"></i>
                                <div class="flex-1">
                                    <div class="flex items-center justify-between">
                                        <span class="text-xs font-semibold">AI Performance Score</span>
                                        <span class="text-sm font-bold text-${scoreColor}-400">${score}%</span>
                                    </div>
                                    <div class="w-full bg-slate-900/50 rounded-full h-1.5 mt-1">
                                        <div class="bg-${scoreColor}-500 h-1.5 rounded-full" style="width: ${score}%"></div>
                                    </div>
                                </div>
                            </div>
                        `;
                    })()}

                    <!-- Stats -->
                    <div class="grid grid-cols-4 gap-1 mb-4 text-xs">
                        <div class="bg-slate-900/50 rounded p-1.5 text-center">
                            <i class="fas fa-eye text-blue-400 text-sm"></i>
                            <p class="text-[10px] text-gray-400 mt-0.5">Views</p>
                            <p class="font-bold text-xs">${ad.analytics?.total_views || 0}</p>
                        </div>
                        <div class="bg-slate-900/50 rounded p-1.5 text-center">
                            <i class="fas fa-phone text-green-400 text-sm"></i>
                            <p class="text-[10px] text-gray-400 mt-0.5">Contacts</p>
                            <p class="font-bold text-xs">${ad.analytics?.total_contacts || 0}</p>
                        </div>
                        <div class="bg-slate-900/50 rounded p-1.5 text-center">
                            <i class="fas fa-heart text-red-400 text-sm"></i>
                            <p class="text-[10px] text-gray-400 mt-0.5">Favorites</p>
                            <p class="font-bold text-xs">${ad.analytics?.current_favorites || 0}</p>
                        </div>
                        <div class="bg-slate-900/50 rounded p-1.5 text-center">
                            <i class="fas fa-thumbs-up text-yellow-400 text-sm"></i>
                            <p class="text-[10px] text-gray-400 mt-0.5">Likes</p>
                            <p class="font-bold text-xs">${ad.analytics?.total_likes || 0}</p>
                        </div>
                    </div>

                    <div class="flex items-center justify-between text-xs text-gray-500 mb-4 pb-4 border-b border-white/10">
                        <span><i class="fas fa-clock mr-1"></i>${timeAgo(ad.timestamp)}</span>
                        <span class="text-gray-400">ID: ${ad.ad_id.substring(0, 15)}...</span>
                    </div>

                    <!-- Actions -->
                    <div class="grid grid-cols-4 gap-1.5">
                        <button onclick="editAd('${ad.ad_id}')" data-tooltip="Edit Ad" class="bg-indigo-600 hover:bg-indigo-700 py-1.5 px-2 rounded text-xs font-medium transition cursor-pointer">
                            <i class="fas fa-edit text-[10px]"></i>
                        </button>
                        <button onclick="deleteAd('${ad.ad_id}', '${escapeHtml(ad.title).replace(/'/g, "\\'")}' )" data-tooltip="Delete Ad" class="bg-red-600 hover:bg-red-700 py-1.5 px-2 rounded text-xs font-medium transition cursor-pointer">
                            <i class="fas fa-trash text-[10px]"></i>
                        </button>
                        <button onclick="toggleStatus('${ad.ad_id}', '${ad.status || 'active'}')" data-tooltip="${(ad.status || 'active') === 'active' ? 'Pause Ad' : 'Activate Ad'}" class="bg-yellow-600 hover:bg-yellow-700 py-1.5 px-2 rounded text-xs font-medium transition cursor-pointer">
                            <i class="fas fa-${(ad.status || 'active') === 'active' ? 'pause' : 'play'} text-[10px]"></i>
                        </button>
                        <button onclick="duplicateAd('${ad.ad_id}', '${escapeHtml(ad.title).replace(/'/g, "\\'")}' )" data-tooltip="Duplicate Ad" class="bg-purple-600 hover:bg-purple-700 py-1.5 px-2 rounded text-xs font-medium transition cursor-pointer">
                            <i class="fas fa-copy text-[10px]"></i>
                        </button>
                        <button onclick="scheduleAd('${ad.ad_id}', '${escapeHtml(ad.title).replace(/'/g, "\\'")}' )" data-tooltip="Schedule Ad" class="bg-cyan-600 hover:bg-cyan-700 py-1.5 px-2 rounded text-xs font-medium transition cursor-pointer">
                            <i class="fas fa-calendar text-[10px]"></i>
                        </button>
                        <button onclick="boostAd('${ad.ad_id}', '${escapeHtml(ad.title).replace(/'/g, "\\'")}' )" data-tooltip="Boost Ad" class="bg-orange-600 hover:bg-orange-700 py-1.5 px-2 rounded text-xs font-medium transition cursor-pointer">
                            <i class="fas fa-rocket text-[10px]"></i>
                        </button>
                        <button onclick="viewAnalytics('${ad.ad_id}')" data-tooltip="View Analytics" class="bg-teal-600 hover:bg-teal-700 py-1.5 px-2 rounded text-xs font-medium transition cursor-pointer">
                            <i class="fas fa-chart-line text-[10px]"></i>
                        </button>
                        <button onclick="viewAd('${ad.ad_id}')" data-tooltip="View Ad Page" class="bg-gray-700 hover:bg-gray-600 py-1.5 px-2 rounded text-xs font-medium transition cursor-pointer">
                            <i class="fas fa-eye text-[10px]"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================
// FILTERING AND SORTING
// ============================================
function applyFilters() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const category = document.getElementById('categoryFilter').value;
    const sortBy = document.getElementById('sortFilter').value;

    // Filter
    filteredAds = allAds.filter(ad => {
        const matchesSearch = !searchTerm ||
            ad.title.toLowerCase().includes(searchTerm) ||
            (ad.description && ad.description.toLowerCase().includes(searchTerm));

        const matchesCategory = !category || ad.category === category;

        return matchesSearch && matchesCategory;
    });

    // Sort
    filteredAds.sort((a, b) => {
        switch(sortBy) {
            case 'newest':
                return b.timestamp - a.timestamp;
            case 'oldest':
                return a.timestamp - b.timestamp;
            case 'most_viewed':
                return (b.analytics?.total_views || 0) - (a.analytics?.total_views || 0);
            case 'most_favorites':
                return (b.analytics?.current_favorites || 0) - (a.analytics?.current_favorites || 0);
            case 'most_likes':
                return (b.analytics?.total_likes || 0) - (a.analytics?.total_likes || 0);
            case 'title':
                return a.title.localeCompare(b.title);
            default:
                return 0;
        }
    });

    renderAds(filteredAds);
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('categoryFilter').value = '';
    document.getElementById('sortFilter').value = 'newest';
    applyFilters();
}

// ============================================
// SELECTION MANAGEMENT
// ============================================
function toggleSelect(adId) {
    if (selectedAds.has(adId)) {
        selectedAds.delete(adId);
    } else {
        selectedAds.add(adId);
    }
    renderAds(filteredAds);
}

function selectAll() {
    filteredAds.forEach(ad => selectedAds.add(ad.ad_id));
    renderAds(filteredAds);
}

function deselectAll() {
    selectedAds.clear();
    renderAds(filteredAds);
}

// ============================================
// AD ACTIONS
// ============================================
function editAd(adId) {
    window.location.href = `edit_ad.php?id=${adId}`;
}

function viewAd(adId) {
    window.open('/', '_blank');
}

function deleteAd(adId, title) {
    deleteTarget = { id: adId, title: title, multiple: false };
    document.getElementById('deleteMessage').textContent = `Are you sure you want to delete "${title}"? This action cannot be undone.`;
    openDeleteModal();
}

function deleteSelected() {
    if (selectedAds.size === 0) {
        alert('Please select at least one ad to delete');
        return;
    }

    deleteTarget = { ids: Array.from(selectedAds), multiple: true };
    document.getElementById('deleteMessage').textContent = `Are you sure you want to delete ${selectedAds.size} ad(s)? This action cannot be undone.`;
    openDeleteModal();
}

async function confirmDelete() {
    if (!deleteTarget) return;

    const deleteBtn = event.target;
    deleteBtn.disabled = true;
    deleteBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Deleting...';

    try {
        const adIds = deleteTarget.multiple ? deleteTarget.ids : [deleteTarget.id];

        const response = await fetch('/app/api/delete_ad.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ad_ids: adIds })
        });

        const result = await response.json();

        if (result.success) {
            // Remove deleted ads from local arrays
            if (deleteTarget.multiple) {
                allAds = allAds.filter(ad => !deleteTarget.ids.includes(ad.ad_id));
                selectedAds.clear();
            } else {
                allAds = allAds.filter(ad => ad.ad_id !== deleteTarget.id);
            }

            closeDeleteModal();
            applyFilters();

            // Show success message
            showNotification('success', result.message);
        } else {
            alert('Error: ' + result.message);
            deleteBtn.disabled = false;
            deleteBtn.innerHTML = 'Delete';
        }
    } catch (error) {
        console.error('Delete error:', error);
        alert('Failed to delete ad(s). Please try again.');
        deleteBtn.disabled = false;
        deleteBtn.innerHTML = 'Delete';
    }
}

async function toggleStatus(adId, currentStatus) {
    const newStatus = currentStatus === 'active' ? 'paused' : 'active';

    try {
        const response = await fetch('/app/api/update_ad_status.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ad_id: adId,
                status: newStatus
            })
        });

        const result = await response.json();

        if (result.success) {
            // Update local ad status
            const ad = allAds.find(a => a.ad_id === adId);
            if (ad) {
                ad.status = newStatus;
                applyFilters();
            }

            showNotification('success', `Ad ${newStatus === 'active' ? 'activated' : 'paused'} successfully`);
        } else {
            alert('Error: ' + result.message);
        }
    } catch (error) {
        console.error('Status toggle error:', error);
        alert('Failed to update ad status. Please try again.');
    }
}

async function duplicateAd(adId, title) {
    if (!confirm(`Create a copy of "${title}"?`)) return;

    try {
        const response = await fetch('/app/api/duplicate_ad.php', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ ad_id: adId })
        });

        const result = await response.json();

        if (result.success) {
            showNotification('success', 'Ad duplicated successfully! Reloading...');

            // Reload ads after 1 second
            setTimeout(() => {
                loadAds();
            }, 1000);
        } else {
            alert('Error: ' + result.message);
        }
    } catch (error) {
        console.error('Duplicate error:', error);
        alert('Failed to duplicate ad. Please try again.');
    }
}

function showNotification(type, message) {
    const container = document.createElement('div');
    container.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transform translate-x-0 transition-all duration-300 ${
        type === 'success' ? 'bg-green-500' : 'bg-red-500'
    }`;
    container.innerHTML = `
        <div class="flex items-center gap-3">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} text-white text-xl"></i>
            <span class="text-white font-medium">${message}</span>
        </div>
    `;

    document.body.appendChild(container);

    setTimeout(() => {
        container.style.transform = 'translateX(400px)';
        setTimeout(() => container.remove(), 300);
    }, 3000);
}

// ============================================
// MODAL CONTROLS
// ============================================
function openDeleteModal() {
    const modal = document.getElementById('deleteModal');
    const card = document.getElementById('deleteModalCard');

    modal.classList.remove('hidden');
    setTimeout(() => {
        card.classList.remove('scale-95', 'opacity-0');
        card.classList.add('scale-100', 'opacity-100');
    }, 10);
}

function closeDeleteModal() {
    const modal = document.getElementById('deleteModal');
    const card = document.getElementById('deleteModalCard');

    card.classList.add('scale-95', 'opacity-0');
    card.classList.remove('scale-100', 'opacity-100');

    setTimeout(() => {
        modal.classList.add('hidden');
        deleteTarget = null;
    }, 300);
}

// Close modal on backdrop click
document.getElementById('deleteModal').addEventListener('click', (e) => {
    if (e.target.id === 'deleteModal') {
        closeDeleteModal();
    }
});

function showError() {
    const container = document.getElementById('adsContainer');
    const loading = document.getElementById('loadingState');

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
// SCHEDULE MODAL
// ============================================
let scheduleAdId = null;

function scheduleAd(adId, title) {
    scheduleAdId = adId;
    document.getElementById('scheduleAdTitle').textContent = title;

    // Clear form
    document.getElementById('scheduleStartDate').value = '';
    document.getElementById('scheduleEndDate').value = '';
    document.getElementById('scheduleAutoRenew').checked = false;

    openScheduleModal();
}

function openScheduleModal() {
    const modal = document.getElementById('scheduleModal');
    const card = document.getElementById('scheduleModalCard');

    modal.classList.remove('hidden');
    setTimeout(() => {
        card.classList.remove('scale-95', 'opacity-0');
        card.classList.add('scale-100', 'opacity-100');
    }, 10);
}

function closeScheduleModal() {
    const modal = document.getElementById('scheduleModal');
    const card = document.getElementById('scheduleModalCard');

    card.classList.add('scale-95', 'opacity-0');
    card.classList.remove('scale-100', 'opacity-100');

    setTimeout(() => {
        modal.classList.add('hidden');
        scheduleAdId = null;
    }, 300);
}

async function confirmSchedule() {
    if (!scheduleAdId) return;

    const startDate = document.getElementById('scheduleStartDate').value;
    const endDate = document.getElementById('scheduleEndDate').value;
    const autoRenew = document.getElementById('scheduleAutoRenew').checked;

    try {
        const response = await fetch('/app/api/schedule_ad.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ad_id: scheduleAdId,
                start_date: startDate,
                end_date: endDate,
                auto_renew: autoRenew
            })
        });

        const result = await response.json();

        if (result.success) {
            closeScheduleModal();
            showNotification('success', 'Schedule updated successfully!');
            loadAds(); // Reload to show updated status
        } else {
            alert('Error: ' + result.message);
        }
    } catch (error) {
        console.error('Schedule error:', error);
        alert('Failed to update schedule. Please try again.');
    }
}

document.getElementById('scheduleModal').addEventListener('click', (e) => {
    if (e.target.id === 'scheduleModal') closeScheduleModal();
});

// ============================================
// BOOST MODAL
// ============================================
let boostAdId = null;

function boostAd(adId, title) {
    boostAdId = adId;
    document.getElementById('boostAdTitle').textContent = title;
    openBoostModal();
}

function openBoostModal() {
    const modal = document.getElementById('boostModal');
    const card = document.getElementById('boostModalCard');

    modal.classList.remove('hidden');
    setTimeout(() => {
        card.classList.remove('scale-95', 'opacity-0');
        card.classList.add('scale-100', 'opacity-100');
    }, 10);
}

function closeBoostModal() {
    const modal = document.getElementById('boostModal');
    const card = document.getElementById('boostModalCard');

    card.classList.add('scale-95', 'opacity-0');
    card.classList.remove('scale-100', 'opacity-100');

    setTimeout(() => {
        modal.classList.add('hidden');
        boostAdId = null;
    }, 300);
}

function confirmBoost() {
    // Placeholder for payment integration
    alert('Payment integration coming soon!\\nAd ID: ' + boostAdId + '\\n\\nThis will allow you to:\\n- Feature your ad at the top\\n- Promote on social media\\n- Reach more customers');
    closeBoostModal();
}

document.getElementById('boostModal').addEventListener('click', (e) => {
    if (e.target.id === 'boostModal') closeBoostModal();
});

// ============================================
// ANALYTICS MODAL
// ============================================
async function viewAnalytics(adId) {
    try {
        const response = await fetch(`/app/api/get_analytics.php?ad_id=${adId}`);
        const result = await response.json();

        if (result.success && result.analytics) {
            const analytics = result.analytics;
            const events = analytics.events || [];

            // Group events by type
            const viewEvents = events.filter(e => e.type === 'view');
            const contactEvents = events.filter(e => e.type === 'contact');

            // Contact methods breakdown
            const contactMethods = {};
            contactEvents.forEach(e => {
                const method = e.metadata?.method || 'unknown';
                contactMethods[method] = (contactMethods[method] || 0) + 1;
            });

            const content = `
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div class="bg-slate-800 rounded-lg p-4 text-center">
                        <i class="fas fa-eye text-blue-400 text-3xl mb-2"></i>
                        <p class="text-2xl font-bold">${analytics.total_views || 0}</p>
                        <p class="text-sm text-gray-400">Total Views</p>
                    </div>
                    <div class="bg-slate-800 rounded-lg p-4 text-center">
                        <i class="fas fa-phone text-green-400 text-3xl mb-2"></i>
                        <p class="text-2xl font-bold">${analytics.total_contacts || 0}</p>
                        <p class="text-sm text-gray-400">Total Contacts</p>
                    </div>
                    <div class="bg-slate-800 rounded-lg p-4 text-center">
                        <i class="fas fa-heart text-red-400 text-3xl mb-2"></i>
                        <p class="text-2xl font-bold">${analytics.current_favorites || 0}</p>
                        <p class="text-sm text-gray-400">Favorites</p>
                    </div>
                    <div class="bg-slate-800 rounded-lg p-4 text-center">
                        <i class="fas fa-thumbs-up text-yellow-400 text-3xl mb-2"></i>
                        <p class="text-2xl font-bold">${analytics.total_likes || 0}</p>
                        <p class="text-sm text-gray-400">Total Likes</p>
                    </div>
                </div>

                <div class="bg-slate-800 rounded-lg p-4 mb-4">
                    <h4 class="font-bold mb-3">Contact Methods Breakdown</h4>
                    <div class="space-y-2">
                        ${Object.entries(contactMethods).map(([method, count]) =>
                            '<div class="flex justify-between items-center">' +
                                '<span class="capitalize"><i class="fas fa-' + (method === 'whatsapp' ? 'whatsapp' : method === 'email' ? 'envelope' : method === 'sms' ? 'sms' : 'phone') + ' mr-2"></i>' + method + '</span>' +
                                '<span class="font-bold">' + count + '</span>' +
                            '</div>'
                        ).join('') || '<p class="text-gray-400 text-sm">No contacts yet</p>'}
                    </div>
                </div>

                <div class="bg-slate-800 rounded-lg p-4">
                    <h4 class="font-bold mb-3">Recent Activity</h4>
                    <div class="space-y-2 max-h-60 overflow-y-auto">
                        ${events.slice(-10).reverse().map(event =>
                            '<div class="flex items-center gap-3 text-sm py-2 border-b border-white/10">' +
                                '<i class="fas fa-' + (event.type === 'view' ? 'eye' : event.type === 'click' ? 'mouse-pointer' : 'phone') + ' text-gray-400"></i>' +
                                '<span class="flex-1">' + (event.type === 'contact' ? 'Contact via ' + (event.metadata?.method || 'unknown') : event.type.charAt(0).toUpperCase() + event.type.slice(1)) + '</span>' +
                                '<span class="text-xs text-gray-500">' + new Date(event.timestamp * 1000).toLocaleString() + '</span>' +
                            '</div>'
                        ).join('') || '<p class="text-gray-400 text-sm">No activity yet</p>'}
                    </div>
                </div>

                <div class="mt-4 text-center">
                    <button onclick="exportAnalytics('${adId}')" class="bg-indigo-600 hover:bg-indigo-700 px-6 py-2 rounded-lg font-semibold transition">
                        <i class="fas fa-download mr-2"></i>Export Data
                    </button>
                </div>
            `;

            document.getElementById('analyticsContent').innerHTML = content;
            openAnalyticsModal();
        } else {
            alert('Failed to load analytics');
        }
    } catch (error) {
        console.error('Analytics error:', error);
        alert('Failed to load analytics. Please try again.');
    }
}

function openAnalyticsModal() {
    const modal = document.getElementById('analyticsModal');
    const card = document.getElementById('analyticsModalCard');

    modal.classList.remove('hidden');
    setTimeout(() => {
        card.classList.remove('scale-95', 'opacity-0');
        card.classList.add('scale-100', 'opacity-100');
    }, 10);
}

function closeAnalyticsModal() {
    const modal = document.getElementById('analyticsModal');
    const card = document.getElementById('analyticsModalCard');

    card.classList.add('scale-95', 'opacity-0');
    card.classList.remove('scale-100', 'opacity-100');

    setTimeout(() => {
        modal.classList.add('hidden');
    }, 300);
}

function exportAnalytics(adId) {
    // Placeholder for CSV export
    alert('Export functionality coming soon!\\nAd ID: ' + adId + '\\n\\nWill export:\\n- View history\\n- Contact details\\n- Performance metrics\\n- Time-based data');
}

document.getElementById('analyticsModal').addEventListener('click', (e) => {
    if (e.target.id === 'analyticsModal') closeAnalyticsModal();
});

// ============================================
// EVENT LISTENERS
// ============================================
document.getElementById('searchInput').addEventListener('input', () => {
    clearTimeout(window.searchTimeout);
    window.searchTimeout = setTimeout(applyFilters, 300);
});

document.getElementById('categoryFilter').addEventListener('change', applyFilters);
document.getElementById('sortFilter').addEventListener('change', applyFilters);

// ============================================
// INITIALIZATION
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    loadAds();
});
</script>

</body>
</html>

