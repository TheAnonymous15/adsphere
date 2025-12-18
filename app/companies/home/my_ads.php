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
    <style>
        .ad-card {
            transition: all 0.3s ease;
        }
        .ad-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(99, 102, 241, 0.3);
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

    <!-- LOADING STATE -->
    <div id="loadingState" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div class="bg-slate-800/50 rounded-xl h-96 animate-pulse"></div>
        <div class="bg-slate-800/50 rounded-xl h-96 animate-pulse"></div>
        <div class="bg-slate-800/50 rounded-xl h-96 animate-pulse"></div>
    </div>

    <!-- ADS CONTAINER -->
    <div id="adsContainer" class="hidden grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <!-- JS will populate -->
    </div>

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

    } catch (error) {
        console.error("Failed to load ads:", error);
        showError();
    }
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

                    <!-- Stats -->
                    <div class="grid grid-cols-3 gap-2 mb-4 text-xs">
                        <div class="bg-slate-900/50 rounded-lg p-2 text-center">
                            <i class="fas fa-eye text-blue-400 mb-1"></i>
                            <p class="text-gray-400">Views</p>
                            <p class="font-bold">${ad.analytics?.total_views || 0}</p>
                        </div>
                        <div class="bg-slate-900/50 rounded-lg p-2 text-center">
                            <i class="fas fa-phone text-green-400 mb-1"></i>
                            <p class="text-gray-400">Contacts</p>
                            <p class="font-bold">${ad.analytics?.total_contacts || 0}</p>
                        </div>
                        <div class="bg-slate-900/50 rounded-lg p-2 text-center">
                            <i class="fas fa-heart text-red-400 mb-1"></i>
                            <p class="text-gray-400">Favorites</p>
                            <p class="font-bold">${ad.analytics?.current_favorites || 0}</p>
                        </div>
                    </div>

                    <div class="flex items-center justify-between text-xs text-gray-500 mb-4 pb-4 border-b border-white/10">
                        <span><i class="fas fa-clock mr-1"></i>${timeAgo(ad.timestamp)}</span>
                        <span class="text-gray-400">ID: ${ad.ad_id.substring(0, 15)}...</span>
                    </div>

                    <!-- Actions -->
                    <div class="grid grid-cols-2 gap-2">
                        <button onclick="editAd('${ad.ad_id}')" class="bg-indigo-600 hover:bg-indigo-700 py-2.5 rounded-lg text-sm font-semibold transition">
                            <i class="fas fa-edit mr-1"></i>Edit
                        </button>
                        <button onclick="deleteAd('${ad.ad_id}', '${escapeHtml(ad.title).replace(/'/g, "\\'")}' )" class="bg-red-600 hover:bg-red-700 py-2.5 rounded-lg text-sm font-semibold transition">
                            <i class="fas fa-trash mr-1"></i>Delete
                        </button>
                        <button onclick="toggleStatus('${ad.ad_id}', '${ad.status || 'active'}')" class="bg-yellow-600 hover:bg-yellow-700 py-2.5 rounded-lg text-sm font-semibold transition">
                            <i class="fas fa-${(ad.status || 'active') === 'active' ? 'pause' : 'play'} mr-1"></i>${(ad.status || 'active') === 'active' ? 'Pause' : 'Activate'}
                        </button>
                        <button onclick="duplicateAd('${ad.ad_id}', '${escapeHtml(ad.title).replace(/'/g, "\\'")}' )" class="bg-purple-600 hover:bg-purple-700 py-2.5 rounded-lg text-sm font-semibold transition">
                            <i class="fas fa-copy mr-1"></i>Duplicate
                        </button>
                        <button onclick="scheduleAd('${ad.ad_id}', '${escapeHtml(ad.title).replace(/'/g, "\\'")}' )" class="bg-cyan-600 hover:bg-cyan-700 py-2.5 rounded-lg text-sm font-semibold transition">
                            <i class="fas fa-calendar mr-1"></i>Schedule
                        </button>
                        <button onclick="boostAd('${ad.ad_id}', '${escapeHtml(ad.title).replace(/'/g, "\\'")}' )" class="bg-orange-600 hover:bg-orange-700 py-2.5 rounded-lg text-sm font-semibold transition">
                            <i class="fas fa-rocket mr-1"></i>Boost
                        </button>
                        <button onclick="viewAnalytics('${ad.ad_id}')" class="bg-teal-600 hover:bg-teal-700 py-2.5 rounded-lg text-sm font-semibold transition">
                            <i class="fas fa-chart-line mr-1"></i>Analytics
                        </button>
                        <button onclick="viewAd('${ad.ad_id}')" class="bg-gray-700 hover:bg-gray-600 py-2.5 rounded-lg text-sm font-semibold transition">
                            <i class="fas fa-eye mr-1"></i>View
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
        const response = await fetch(\`/app/api/get_analytics.php?ad_id=\${adId}\`);
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

            const content = \`
                <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                    <div class="bg-slate-800 rounded-lg p-4 text-center">
                        <i class="fas fa-eye text-blue-400 text-3xl mb-2"></i>
                        <p class="text-2xl font-bold">\${analytics.total_views || 0}</p>
                        <p class="text-sm text-gray-400">Total Views</p>
                    </div>
                    <div class="bg-slate-800 rounded-lg p-4 text-center">
                        <i class="fas fa-phone text-green-400 text-3xl mb-2"></i>
                        <p class="text-2xl font-bold">\${analytics.total_contacts || 0}</p>
                        <p class="text-sm text-gray-400">Total Contacts</p>
                    </div>
                    <div class="bg-slate-800 rounded-lg p-4 text-center">
                        <i class="fas fa-heart text-red-400 text-3xl mb-2"></i>
                        <p class="text-2xl font-bold">\${analytics.current_favorites || 0}</p>
                        <p class="text-sm text-gray-400">Favorites</p>
                    </div>
                    <div class="bg-slate-800 rounded-lg p-4 text-center">
                        <i class="fas fa-thumbs-up text-yellow-400 text-3xl mb-2"></i>
                        <p class="text-2xl font-bold">\${analytics.total_likes || 0}</p>
                        <p class="text-sm text-gray-400">Total Likes</p>
                    </div>
                </div>

                <div class="bg-slate-800 rounded-lg p-4 mb-4">
                    <h4 class="font-bold mb-3">Contact Methods Breakdown</h4>
                    <div class="space-y-2">
                        \${Object.entries(contactMethods).map(([method, count]) => \`
                            <div class="flex justify-between items-center">
                                <span class="capitalize"><i class="fas fa-\${method === 'whatsapp' ? 'whatsapp' : method === 'email' ? 'envelope' : method === 'sms' ? 'sms' : 'phone'} mr-2"></i>\${method}</span>
                                <span class="font-bold">\${count}</span>
                            </div>
                        \`).join('') || '<p class="text-gray-400 text-sm">No contacts yet</p>'}
                    </div>
                </div>

                <div class="bg-slate-800 rounded-lg p-4">
                    <h4 class="font-bold mb-3">Recent Activity</h4>
                    <div class="space-y-2 max-h-60 overflow-y-auto">
                        \${events.slice(-10).reverse().map(event => \`
                            <div class="flex items-center gap-3 text-sm py-2 border-b border-white/10">
                                <i class="fas fa-\${event.type === 'view' ? 'eye' : event.type === 'click' ? 'mouse-pointer' : 'phone'} text-gray-400"></i>
                                <span class="flex-1">\${event.type === 'contact' ? \`Contact via \${event.metadata?.method || 'unknown'}\` : event.type.charAt(0).toUpperCase() + event.type.slice(1)}</span>
                                <span class="text-xs text-gray-500">\${new Date(event.timestamp * 1000).toLocaleString()}</span>
                            </div>
                        \`).join('') || '<p class="text-gray-400 text-sm">No activity yet</p>'}
                    </div>
                </div>

                <div class="mt-4 text-center">
                    <button onclick="exportAnalytics('\${adId}')" class="bg-indigo-600 hover:bg-indigo-700 px-6 py-2 rounded-lg font-semibold transition">
                        <i class="fas fa-download mr-2"></i>Export Data
                    </button>
                </div>
            \`;

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
