<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AdSphere | Next-Gen Advertising Platform</title>
    <link rel="icon" type="image/png" href="icon.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="/static/css/all.min.css">
    <style>
        /* Futuristic Animations */
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
        }

        @keyframes pulse-glow {
            0%, 100% { box-shadow: 0 0 20px rgba(99, 102, 241, 0.4); }
            50% { box-shadow: 0 0 40px rgba(99, 102, 241, 0.8); }
        }

        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        @keyframes countUp {
            from { opacity: 0; transform: scale(0.5); }
            to { opacity: 1; transform: scale(1); }
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

        .ad-card {
            transition: all 0.3s ease;
        }

        .ad-card:hover {
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 20px 40px rgba(99, 102, 241, 0.3);
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

<!-- Header -->
<?php include "header.php"; ?>

<!-- Hero Section with Live Stats -->
<section class="relative min-h-screen flex items-center justify-center overflow-hidden pt-20 grid-pattern">
    <!-- Animated Background Elements -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
        <div class="absolute top-20 left-10 w-72 h-72 bg-indigo-600/20 rounded-full blur-3xl animate-pulse"></div>
        <div class="absolute bottom-20 right-10 w-96 h-96 bg-purple-600/20 rounded-full blur-3xl animate-pulse" style="animation-delay: 1s;"></div>
        <div class="absolute top-1/2 left-1/2 w-64 h-64 bg-cyan-600/20 rounded-full blur-3xl animate-pulse" style="animation-delay: 2s;"></div>
    </div>

    <div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div class="text-center mb-16">
            <div class="inline-flex items-center gap-2 bg-indigo-600/20 border border-indigo-600/50 rounded-full px-6 py-2 mb-6 live-indicator">
                <div class="w-3 h-3 bg-green-400 rounded-full animate-ping"></div>
                <div class="w-3 h-3 bg-green-400 rounded-full absolute"></div>
                <span class="text-sm font-semibold ml-3">LIVE • Real-time Updates</span>
            </div>

            <h1 class="text-5xl sm:text-6xl lg:text-7xl font-bold mb-6 bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                Next-Gen Advertising
            </h1>
            <p class="text-xl sm:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
                Experience the future of digital marketing with AI-powered insights and real-time analytics
            </p>

            <!-- Live Stats Counter -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12 max-w-4xl mx-auto">
                <div class="glass-card rounded-2xl p-6 stat-card" style="animation-delay: 0s;">
                    <i class="fas fa-ad text-3xl text-indigo-400 mb-3"></i>
                    <div class="text-3xl font-bold mb-1" id="totalAdsCounter">0</div>
                    <div class="text-sm text-gray-400">Active Ads</div>
                </div>
                <div class="glass-card rounded-2xl p-6 stat-card" style="animation-delay: 0.2s;">
                    <i class="fas fa-eye text-3xl text-purple-400 mb-3"></i>
                    <div class="text-3xl font-bold mb-1" id="totalViewsCounter">0</div>
                    <div class="text-sm text-gray-400">Total Views</div>
                </div>
                <div class="glass-card rounded-2xl p-6 stat-card" style="animation-delay: 0.4s;">
                    <i class="fas fa-users text-3xl text-pink-400 mb-3"></i>
                    <div class="text-3xl font-bold mb-1" id="activeUsersCounter">0</div>
                    <div class="text-sm text-gray-400">Active Users</div>
                </div>
                <div class="glass-card rounded-2xl p-6 stat-card" style="animation-delay: 0.6s;">
                    <i class="fas fa-fire text-3xl text-orange-400 mb-3"></i>
                    <div class="text-3xl font-bold mb-1" id="engagementCounter">0</div>
                    <div class="text-sm text-gray-400">Engagement Rate</div>
                </div>
            </div>

            <!-- CTA Buttons -->
            <div class="flex flex-wrap gap-4 justify-center">
                <a href="#ads-feed" class="bg-indigo-600 hover:bg-indigo-700 px-8 py-4 rounded-xl font-bold text-lg transition-all transform hover:scale-105 shadow-lg">
                    <i class="fas fa-rocket mr-2"></i>Explore Ads
                </a>
                <a href="/app/companies/handlers/login.php" class="glass-card hover:bg-white/10 px-8 py-4 rounded-xl font-bold text-lg transition-all transform hover:scale-105">
                    <i class="fas fa-sign-in-alt mr-2"></i>Post Your Ad
                </a>
            </div>
        </div>
    </div>
</section>

<!-- Live Activity Feed -->
<section class="relative py-16 bg-black/20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between mb-8">
            <h2 class="text-3xl font-bold flex items-center gap-3">
                <i class="fas fa-chart-line text-indigo-400"></i>
                Live Activity
            </h2>
            <div class="flex items-center gap-2 text-sm text-gray-400">
                <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span id="lastUpdate">Updated just now</span>
            </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <!-- Live Feed -->
            <div class="lg:col-span-2 glass-card rounded-2xl p-6">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-xl font-bold">Recent Activity</h3>
                    <button onclick="refreshActivity()" class="text-indigo-400 hover:text-indigo-300 transition">
                        <i class="fas fa-sync-alt"></i>
                    </button>
                </div>
                <div id="activityFeed" class="space-y-3 max-h-96 overflow-y-auto">
                    <!-- Loading placeholder -->
                    <div class="shimmer-bg h-16 rounded-lg"></div>
                    <div class="shimmer-bg h-16 rounded-lg"></div>
                    <div class="shimmer-bg h-16 rounded-lg"></div>
                </div>
            </div>

            <!-- Trending Stats -->
            <div class="glass-card rounded-2xl p-6">
                <h3 class="text-xl font-bold mb-4">Trending Now</h3>
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
                            <span class="text-sm text-gray-400">Engagement</span>
                            <i class="fas fa-heart text-pink-400"></i>
                        </div>
                        <div class="text-2xl font-bold" id="totalEngagement">0</div>
                        <div class="text-xs text-gray-400 mt-1">Likes + Favorites</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Ads Feed Section -->
<?php include "ad_page.php"; ?>

<!-- Footer -->
<?php include "footer.php"; ?>

<!-- Live Update Script -->
<script>
// ============================================
// LIVE UPDATES & REAL-TIME ANALYTICS
// ============================================

let updateInterval;
let lastActivityUpdate = Date.now();

// Animated Counter Function
function animateCounter(element, target, duration = 2000, suffix = '') {
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
        const response = await fetch('/api/get_ads.php');
        const data = await response.json();

        if (data && data.ads) {
            const totalAds = data.ads.length;
            const totalViews = data.ads.reduce((sum, ad) => sum + (ad.views || 0), 0);
            const totalFavorites = data.ads.reduce((sum, ad) => sum + (ad.favorites || 0), 0);
            const totalLikes = data.ads.reduce((sum, ad) => sum + (ad.likes || 0), 0);

            // Animate counters
            animateCounter(document.getElementById('totalAdsCounter'), totalAds);
            animateCounter(document.getElementById('totalViewsCounter'), totalViews);
            animateCounter(document.getElementById('activeUsersCounter'), Math.floor(totalViews / 10));
            animateCounter(document.getElementById('engagementCounter'),
                Math.min(99, Math.floor((totalFavorites + totalLikes) / totalAds * 10)), 2000, '%');

            // Update trending stats
            if (data.ads.length > 0) {
                const topAd = data.ads.reduce((max, ad) =>
                    (ad.views || 0) > (max.views || 0) ? ad : max
                );
                document.getElementById('topAdViews').textContent = (topAd.views || 0).toLocaleString();
                document.getElementById('topAdTitle').textContent = topAd.title || 'No title';

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
            }
        }
    } catch (error) {
        console.error('Failed to load live stats:', error);
    }
}

// Load Live Activity Feed
async function loadActivityFeed() {
    try {
        const response = await fetch('/api/get_ads.php');
        const data = await response.json();

        if (data && data.ads) {
            const activities = [];

            // Generate activity items from ads
            data.ads.slice(0, 10).forEach(ad => {
                const timeDiff = Date.now() - (ad.timestamp * 1000);
                const minutesAgo = Math.floor(timeDiff / 60000);

                activities.push({
                    icon: 'fa-ad',
                    color: 'indigo',
                    text: `New ad posted: "${ad.title}"`,
                    time: minutesAgo < 1 ? 'Just now' : `${minutesAgo}m ago`,
                    category: ad.category
                });

                if (ad.views > 0) {
                    activities.push({
                        icon: 'fa-eye',
                        color: 'blue',
                        text: `${ad.views} views on "${ad.title.substring(0, 30)}..."`,
                        time: `${Math.floor(Math.random() * 30) + 1}m ago`,
                        category: ad.category
                    });
                }
            });

            // Shuffle and take top 8
            const shuffled = activities.sort(() => Math.random() - 0.5).slice(0, 8);

            const feedHTML = shuffled.map(activity => `
                <div class="activity-item flex items-center gap-4 p-4 bg-white/5 rounded-xl hover:bg-white/10 transition">
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

            // Update timestamp
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
    btn.querySelector('i').classList.add('fa-spin');

    loadActivityFeed().then(() => {
        setTimeout(() => {
            btn.querySelector('i').classList.remove('fa-spin');
        }, 500);
    });
}

// Update "last updated" time
function updateTimestamp() {
    const seconds = Math.floor((Date.now() - lastActivityUpdate) / 1000);
    const text = seconds < 5 ? 'Updated just now' :
                 seconds < 60 ? `Updated ${seconds}s ago` :
                 `Updated ${Math.floor(seconds / 60)}m ago`;
    document.getElementById('lastUpdate').textContent = text;
}

// Initialize live updates
function initLiveUpdates() {
    // Load initial data
    loadLiveStats();
    loadActivityFeed();

    // Auto-refresh every 30 seconds
    updateInterval = setInterval(() => {
        loadLiveStats();
        loadActivityFeed();
    }, 30000);

    // Update timestamp every second
    setInterval(updateTimestamp, 1000);
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (updateInterval) clearInterval(updateInterval);
});

// Start live updates when page loads
document.addEventListener('DOMContentLoaded', () => {
    initLiveUpdates();

    // Add smooth scroll behavior
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
});
</script>

</body>
</html>

