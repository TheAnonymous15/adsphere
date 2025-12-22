<?php
/**
 * PUBLIC SERVICE - Homepage
 * Port 8001
 */
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AdSphere - Find What You're Looking For</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .hero-pattern {
            background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
        }
        .glass {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
    </style>
</head>
<body class="hero-pattern">

<!-- Navigation -->
<nav class="glass fixed top-0 left-0 right-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
            <a href="/" class="flex items-center gap-3">
                <div class="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
                    <span class="text-2xl">📢</span>
                </div>
                <span class="text-2xl font-bold text-white">AdSphere</span>
            </a>

            <div class="hidden md:flex items-center gap-6">
                <a href="/ads" class="text-white/80 hover:text-white transition">Browse Ads</a>
                <a href="/categories" class="text-white/80 hover:text-white transition">Categories</a>
                <a href="http://localhost:8003/login" class="bg-white text-purple-600 px-6 py-2 rounded-full font-semibold hover:bg-opacity-90 transition">
                    Post Your Ad
                </a>
            </div>
        </div>
    </div>
</nav>

<!-- Hero Section -->
<div class="pt-32 pb-20 px-4">
    <div class="max-w-4xl mx-auto text-center">
        <h1 class="text-5xl md:text-6xl font-bold text-white mb-6">
            Find What You're Looking For
        </h1>
        <p class="text-xl text-white/80 mb-10">
            Browse thousands of ads from trusted sellers. Buy, sell, or discover amazing deals.
        </p>

        <!-- Search Box -->
        <div class="glass rounded-2xl p-2 max-w-2xl mx-auto mb-12">
            <form action="/search" method="GET" class="flex gap-2">
                <input type="text" name="q" placeholder="What are you looking for?"
                    class="flex-1 bg-white/10 text-white placeholder-white/50 px-6 py-4 rounded-xl focus:outline-none focus:ring-2 focus:ring-white/30">
                <button type="submit" class="bg-white text-purple-600 px-8 py-4 rounded-xl font-semibold hover:bg-opacity-90 transition">
                    <i class="fas fa-search mr-2"></i>Search
                </button>
            </form>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-3 gap-8 max-w-lg mx-auto">
            <div class="text-center">
                <div class="text-4xl font-bold text-white" id="adCount">0</div>
                <div class="text-white/60 text-sm">Active Ads</div>
            </div>
            <div class="text-center">
                <div class="text-4xl font-bold text-white" id="categoryCount">0</div>
                <div class="text-white/60 text-sm">Categories</div>
            </div>
            <div class="text-center">
                <div class="text-4xl font-bold text-white" id="companyCount">0</div>
                <div class="text-white/60 text-sm">Sellers</div>
            </div>
        </div>
    </div>
</div>

<!-- Categories Section -->
<div class="bg-white py-16">
    <div class="max-w-7xl mx-auto px-4">
        <h2 class="text-3xl font-bold text-gray-800 text-center mb-12">Popular Categories</h2>

        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4" id="categories">
            <!-- Categories will be loaded here -->
        </div>
    </div>
</div>

<!-- Latest Ads Section -->
<div class="bg-gray-50 py-16">
    <div class="max-w-7xl mx-auto px-4">
        <div class="flex justify-between items-center mb-8">
            <h2 class="text-3xl font-bold text-gray-800">Latest Ads</h2>
            <a href="/ads" class="text-purple-600 hover:text-purple-700 font-semibold">
                View All <i class="fas fa-arrow-right ml-2"></i>
            </a>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6" id="latestAds">
            <!-- Ads will be loaded here -->
        </div>
    </div>
</div>

<!-- Footer -->
<footer class="bg-gray-900 text-white py-12">
    <div class="max-w-7xl mx-auto px-4">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div>
                <div class="flex items-center gap-2 mb-4">
                    <span class="text-2xl">📢</span>
                    <span class="text-xl font-bold">AdSphere</span>
                </div>
                <p class="text-gray-400 text-sm">
                    Your trusted marketplace for buying and selling.
                </p>
            </div>
            <div>
                <h4 class="font-semibold mb-4">Quick Links</h4>
                <ul class="space-y-2 text-gray-400 text-sm">
                    <li><a href="/ads" class="hover:text-white">Browse Ads</a></li>
                    <li><a href="/categories" class="hover:text-white">Categories</a></li>
                    <li><a href="http://localhost:8003/register" class="hover:text-white">Become a Seller</a></li>
                </ul>
            </div>
            <div>
                <h4 class="font-semibold mb-4">For Business</h4>
                <ul class="space-y-2 text-gray-400 text-sm">
                    <li><a href="http://localhost:8003/login" class="hover:text-white">Company Login</a></li>
                    <li><a href="http://localhost:8003/register" class="hover:text-white">Register Company</a></li>
                </ul>
            </div>
            <div>
                <h4 class="font-semibold mb-4">Administration</h4>
                <ul class="space-y-2 text-gray-400 text-sm">
                    <li><a href="http://localhost:8002/login" class="hover:text-white">Admin Login</a></li>
                </ul>
            </div>
        </div>
        <div class="border-t border-gray-800 mt-8 pt-8 text-center text-gray-500 text-sm">
            © <?= date('Y') ?> AdSphere. All rights reserved.
        </div>
    </div>
</footer>

<script>
// Load stats and content
async function loadData() {
    try {
        const response = await fetch('/api/get_ads');
        const data = await response.json();

        if (data.ads) {
            // Update stats
            document.getElementById('adCount').textContent = data.ads.length;

            // Get unique categories and companies
            const categories = [...new Set(data.ads.map(a => a.category).filter(Boolean))];
            const companies = [...new Set(data.ads.map(a => a.company).filter(Boolean))];

            document.getElementById('categoryCount').textContent = categories.length;
            document.getElementById('companyCount').textContent = companies.length;

            // Load categories
            const categoryIcons = {
                'electronics': 'fa-laptop',
                'vehicles': 'fa-car',
                'property': 'fa-home',
                'fashion': 'fa-tshirt',
                'furniture': 'fa-couch',
                'services': 'fa-briefcase',
                'jobs': 'fa-user-tie',
                'food': 'fa-utensils'
            };

            document.getElementById('categories').innerHTML = categories.slice(0, 6).map(cat => `
                <a href="/category/${cat}" class="bg-white border border-gray-200 rounded-xl p-6 text-center hover:shadow-lg hover:border-purple-300 transition group">
                    <i class="fas ${categoryIcons[cat] || 'fa-tag'} text-3xl text-purple-500 mb-3 group-hover:scale-110 transition"></i>
                    <div class="font-semibold text-gray-800 capitalize">${cat}</div>
                </a>
            `).join('');

            // Load latest ads
            document.getElementById('latestAds').innerHTML = data.ads.slice(0, 8).map(ad => `
                <a href="/ad/${ad.id}" class="bg-white rounded-xl overflow-hidden shadow hover:shadow-xl transition group">
                    <div class="h-48 bg-gray-200 flex items-center justify-center">
                        ${ad.images && ad.images[0]
                            ? `<img src="${ad.images[0]}" class="w-full h-full object-cover">`
                            : `<i class="fas fa-image text-4xl text-gray-400"></i>`
                        }
                    </div>
                    <div class="p-4">
                        <h3 class="font-semibold text-gray-800 mb-1 truncate group-hover:text-purple-600">${ad.title || 'Untitled'}</h3>
                        <p class="text-sm text-gray-500 capitalize">${ad.category || 'Uncategorized'}</p>
                        ${ad.price ? `<p class="text-purple-600 font-bold mt-2">KES ${Number(ad.price).toLocaleString()}</p>` : ''}
                    </div>
                </a>
            `).join('');
        }
    } catch (error) {
        console.error('Failed to load data:', error);
    }
}

document.addEventListener('DOMContentLoaded', loadData);
</script>

</body>
</html>

