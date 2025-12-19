<?php
/********************************************
 * Admin Dashboard - AdSphere
 * Complete platform statistics and analytics
 ********************************************/
session_start();

// Block unauthorized access
if(!isset($_SESSION['company'])) {
    header("Location: /app/companies/handlers/login.php");
    exit();
}

$companySlug = $_SESSION['company'];
$companyName = $_SESSION['company_name'] ?? ucfirst($companySlug);
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - AdSphere</title>
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

        body {
            background: linear-gradient(135deg, #0f172a, #1e1b4b, #312e81, #1e1b4b, #0f172a);
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
        }

        .glass-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .stat-card {
            animation: float 6s ease-in-out infinite;
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-20px) scale(1.05);
            box-shadow: 0 20px 40px rgba(99, 102, 241, 0.4);
        }

        .activity-item {
            animation: slideInRight 0.5s ease-out;
        }

        .live-indicator {
            animation: pulse-glow 2s ease-in-out infinite;
        }

        .shimmer-bg {
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
            background-size: 1000px 100%;
            animation: shimmer 2s infinite;
        }

        .grid-pattern {
            background-image:
                linear-gradient(rgba(99, 102, 241, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(99, 102, 241, 0.03) 1px, transparent 1px);
            background-size: 50px 50px;
        }
    </style>
</head>
<body class="text-white overflow-x-hidden">

<!-- NAVBAR -->
<nav class="bg-slate-900/80 backdrop-blur-lg border-b border-white/10 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
            <div class="flex items-center gap-3">
                <a href="dashboard.php" class="flex items-center gap-3 hover:opacity-80 transition">
                    <div class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                        <i class="fas fa-chart-line text-white text-xl"></i>
                    </div>
                    <div>
                        <h1 class="text-xl font-bold text-white">Admin Dashboard</h1>
                        <p class="text-xs text-gray-400"><?= htmlspecialchars($companyName) ?></p>
                    </div>
                </a>
            </div>

            <div class="flex items-center gap-4">
                <a href="dashboard.php" class="text-gray-300 hover:text-white transition">
                    <i class="fas fa-arrow-left mr-2"></i>Back to Dashboard
                </a>
                <a href="my_ads.php" class="text-gray-300 hover:text-white transition">
                    <i class="fas fa-ad mr-2"></i>My Ads
                </a>
            </div>
        </div>
    </div>
</nav>

<!-- MAIN CONTENT -->
<div class="min-h-screen py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <!-- Header with Live Indicator -->
        <div class="text-center mb-12">
            <div class="inline-flex items-center gap-2 bg-indigo-600/20 border border-indigo-600/50 rounded-full px-6 py-2 mb-4 live-indicator">
                <div class="w-3 h-3 bg-green-400 rounded-full animate-ping"></div>
                <div class="w-3 h-3 bg-green-400 rounded-full absolute"></div>
                <span class="text-sm font-semibold ml-3">LIVE PLATFORM STATISTICS</span>
            </div>
            <h1 class="text-5xl font-bold mb-2 bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                Real-Time Analytics
            </h1>
            <p class="text-gray-300 text-lg">Complete platform overview • Updated every 30 seconds</p>
        </div>

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
                <i class="fas fa-users text-5xl text-pink-400 mb-4"></i>
                <div class="text-5xl font-bold mb-2" id="activeUsersCounter">0</div>
                <div class="text-sm text-gray-300">Active Users</div>
                <div class="text-xs text-gray-500 mt-2">Estimated</div>
            </div>
            <div class="glass-card rounded-2xl p-6 stat-card text-center" style="animation-delay: 0.6s;">
                <i class="fas fa-fire text-5xl text-orange-400 mb-4"></i>
                <div class="text-5xl font-bold mb-2" id="engagementCounter">0%</div>
                <div class="text-sm text-gray-300">Engagement Rate</div>
                <div class="text-xs text-gray-500 mt-2">Platform average</div>
            </div>
        </div>

        <!-- Additional Stats Row -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
            <div class="glass-card rounded-2xl p-6 text-center">
                <i class="fas fa-heart text-3xl text-red-400 mb-3"></i>
                <div class="text-3xl font-bold mb-2" id="totalFavoritesCounter">0</div>
                <div class="text-sm text-gray-300">Total Favorites</div>
            </div>
            <div class="glass-card rounded-2xl p-6 text-center">
                <i class="fas fa-thumbs-up text-3xl text-yellow-400 mb-3"></i>
                <div class="text-3xl font-bold mb-2" id="totalLikesCounter">0</div>
                <div class="text-sm text-gray-300">Total Likes</div>
            </div>
            <div class="glass-card rounded-2xl p-6 text-center">
                <i class="fas fa-building text-3xl text-cyan-400 mb-3"></i>
                <div class="text-3xl font-bold mb-2" id="totalCompaniesCounter">0</div>
                <div class="text-sm text-gray-300">Companies</div>
            </div>
            <div class="glass-card rounded-2xl p-6 text-center">
                <i class="fas fa-tags text-3xl text-green-400 mb-3"></i>
                <div class="text-3xl font-bold mb-2" id="totalCategoriesCounter">0</div>
                <div class="text-sm text-gray-300">Categories</div>
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
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
    try {
        const response = await fetch('/app/api/get_ads.php');
        const data = await response.json();

        if (data && data.ads) {
            const totalAds = data.ads.length;
            const totalViews = data.ads.reduce((sum, ad) => sum + (ad.views || 0), 0);
            const totalFavorites = data.ads.reduce((sum, ad) => sum + (ad.favorites || 0), 0);
            const totalLikes = data.ads.reduce((sum, ad) => sum + (ad.likes || 0), 0);

            // Get unique companies and categories
            const companies = new Set(data.ads.map(ad => ad.company).filter(Boolean));
            const categories = new Set(data.ads.map(ad => ad.category).filter(Boolean));

            // Animate main counters
            animateCounter(document.getElementById('totalAdsCounter'), totalAds);
            animateCounter(document.getElementById('totalViewsCounter'), totalViews);
            animateCounter(document.getElementById('activeUsersCounter'), Math.floor(totalViews / 10));
            const engagementRate = totalAds > 0 ? Math.min(99, Math.floor((totalFavorites + totalLikes) / totalAds * 10)) : 0;
            animateCounter(document.getElementById('engagementCounter'), engagementRate, 2000, '%');

            // Animate additional counters
            animateCounter(document.getElementById('totalFavoritesCounter'), totalFavorites);
            animateCounter(document.getElementById('totalLikesCounter'), totalLikes);
            animateCounter(document.getElementById('totalCompaniesCounter'), companies.size);
            animateCounter(document.getElementById('totalCategoriesCounter'), categories.size);

            // Update trending stats
            if (data.ads.length > 0) {
                const topAd = data.ads.reduce((max, ad) =>
                    (ad.views || 0) > (max.views || 0) ? ad : max
                );
                document.getElementById('topAdViews').textContent = (topAd.views || 0).toLocaleString();
                document.getElementById('topAdTitle').textContent = (topAd.title || 'No title').substring(0, 50) + '...';

                // Category analysis
                const categoryCount = {};
                data.ads.forEach(ad => {
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

                // Update charts
                updateCharts(data.ads);
            }
        }
    } catch (error) {
        console.error('Failed to load live stats:', error);
    }
}

// Update Charts
function updateCharts(ads) {
    // Views Distribution Chart
    const viewsData = ads.slice(0, 10).map(ad => ({
        title: (ad.title || 'Untitled').substring(0, 20) + '...',
        views: ad.views || 0
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

// Initialize
function initDashboard() {
    loadLiveStats();
    loadActivityFeed();

    updateInterval = setInterval(() => {
        loadLiveStats();
        loadActivityFeed();
    }, 30000);

    setInterval(updateTimestamp, 1000);
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

