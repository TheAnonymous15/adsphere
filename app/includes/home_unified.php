<?php
/********************************************
 * ADSPHERE HOME PAGE
 * Combined single-file structure for optimal performance
 ********************************************/
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AdSphere | The Future of Digital Advertising</title>
    <link rel="icon" type="image/png" href="/app/assets/images/adsphere.ico">
    <script src="/app/assets/css/tailwind.js"></script>
    <link rel="stylesheet" href="/app/assets/css/all.min.css">
    <style>
        /* Shared Classes */
        .nav-link {
            @apply text-white/90 hover:text-white font-medium transition-all hover:-translate-y-0.5;
        }
        .mobile-link {
            @apply block px-6 py-3 text-gray-800/90 hover:bg-white/30 hover:text-indigo-600 transition;
        }

        /* Hero Gradient Animation */
        .animated-gradient {
            background: linear-gradient(135deg, #6366f1, #8b5cf6, #d946ef);
            background-size: 400% 400%;
            animation: gradientShift 10s ease infinite;
        }

        /* Body Background Gradient */
        body {
            background: linear-gradient(135deg, #0b927e, #0b343b, #119585);
            background-size: 400% 400%;
            animation: gradientShift 20s ease infinite;
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
    </style>
</head>
<body class="text-gray-900 font-sans leading-relaxed scroll-smooth">

<!-- ============================================ -->
<!-- HEADER / NAVIGATION -->
<!-- ============================================ -->
<header class="fixed top-0 left-0 w-full z-50 backdrop-blur-xl bg-white/10 border-b border-white/20 shadow-lg">
    <nav class="max-w-7xl mx-auto px-6 flex items-center justify-between h-20">

        <!-- Branding -->
        <div class="flex items-center space-x-4 group cursor-pointer">
            <div class="p-1 rounded-xl bg-white/20 backdrop-blur-lg shadow-md transition-transform group-hover:scale-105">
                <img src="/app/assets/images/icc.png" alt="AdSphere Logo" class="h-12 w-auto object-contain">
            </div>
        </div>

        <!-- Desktop Menu -->
        <div class="hidden md:flex items-center space-x-8">
            <a href="#features" class="nav-link">Features</a>
            <a href="#marketplace" class="nav-link">Marketplace</a>
            <a href="#pricing" class="nav-link">Pricing</a>
            <a href="#testimonials" class="nav-link">Testimonials</a>
            <a href="#faq" class="nav-link">FAQ</a>
            <a href="#signup" class="px-5 py-2.5 bg-white text-indigo-600 rounded-xl font-semibold shadow hover:shadow-lg transition-all hover:-translate-y-0.5">Signup</a>
            <a href="/app/companies/handlers/login.php" class="px-5 py-2.5 border border-white/70 text-white rounded-xl font-semibold hover:bg-white hover:text-indigo-700 transition-all hover:-translate-y-0.5">Login</a>
        </div>

        <!-- Mobile Menu Button -->
        <button id="mobile-menu-button" class="md:hidden focus:outline-none text-white">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8h16M4 16h16"/>
            </svg>
        </button>
    </nav>

    <!-- Mobile Menu -->
    <div id="mobile-menu" class="hidden md:hidden bg-white/20 backdrop-blur-lg border-t border-white/10 shadow-xl">
        <a href="#features" class="mobile-link">Features</a>
        <a href="#marketplace" class="mobile-link">Marketplace</a>
        <a href="#pricing" class="mobile-link">Pricing</a>
        <a href="#testimonials" class="mobile-link">Testimonials</a>
        <a href="#faq" class="mobile-link">FAQ</a>
        <a href="#signup" class="mobile-link font-semibold text-indigo-600">Signup</a>
        <a href="/app/companies/handlers/login.php" class="mobile-link font-semibold text-indigo-600">Login</a>
    </div>
</header>

<!-- ============================================ -->
<!-- HERO SECTION -->
<!-- ============================================ -->
<section class="relative animated-gradient text-white overflow-hidden pt-24 w-full h-auto">
    <div class="max-w-7xl mx-auto px-6 py-24 grid grid-cols-1 md:grid-cols-2 gap-12">

        <!-- LEFT COLUMN -->
        <div class="flex flex-col justify-between h-full gap-8">
            <!-- Branding / Headline -->
            <div class="space-y-6 text-center md:text-left">
                <h1 class="text-5xl md:text-6xl font-extrabold leading-tight drop-shadow-lg">
                    The Future of Digital Advertising
                </h1>
                <p class="text-xl md:text-2xl text-indigo-100 drop-shadow-sm">
                    Create, manage, and deploy ads with AI-powered automation. Upload once, generate multiple formats, and scale performance automatically.
                </p>
                <div class="flex flex-col sm:flex-row gap-4 justify-center md:justify-start mt-6">
                    <a href="#ads-feed" class="px-6 py-3 bg-white text-indigo-600 font-semibold rounded-xl shadow-lg transform transition hover:-translate-y-1 hover:shadow-2xl">
                        Browse Ads
                    </a>
                    <a href="/app/companies/handlers/login.php" class="px-6 py-3 border border-white text-white rounded-xl font-semibold hover:bg-white hover:text-indigo-600 transition transform hover:-translate-y-1">
                        Post Your Ad
                    </a>
                </div>
            </div>

            <!-- Boost Subsection -->
            <div class="w-full bg-white/10 backdrop-blur-md rounded-2xl p-6 shadow-lg flex flex-col gap-4">
                <h3 class="text-xl md:text-2xl font-bold text-white">Boost Your Ads Instantly</h3>
                <p class="text-indigo-100 text-sm md:text-base">
                    With AdSphere, you can automate campaigns, track performance, and scale your ad spend efficiently—all in one platform.
                </p>
                <a href="#ads-feed" class="mt-2 px-4 py-2 bg-indigo-500 text-white font-semibold rounded-xl shadow hover:shadow-lg transition transform hover:-translate-y-0.5 w-max">
                    Explore Now
                </a>
            </div>
        </div>

        <!-- RIGHT COLUMN -->
        <div class="flex flex-col justify-between h-full gap-8">
            <!-- Video Section -->
            <div class="w-full rounded-3xl shadow-2xl overflow-hidden">
                <div class="relative h-72 md:h-96 w-full rounded-2xl overflow-hidden">
                    <video autoplay muted loop playsinline class="w-full h-full object-cover">
                        <source src="/app/assets/videos/ad.webm" type="video/webm">
                        Your browser does not support the video tag.
                    </video>
                </div>
            </div>

            <!-- Stats / Timeline -->
            <div class="relative max-w-full">
                <!-- Timeline Line -->
                <div class="absolute top-1/2 transform -translate-y-1/2 left-0 right-0 h-1 bg-white/20"></div>

                <div class="flex justify-between items-center relative z-10 text-white">
                    <!-- Stat 1 -->
                    <div class="flex flex-col items-center text-center w-1/3">
                        <div class="p-4 rounded-full bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center text-2xl shadow-lg transform transition-transform hover:scale-110">
                            <i class="fas fa-bullhorn"></i>
                        </div>
                        <div class="mt-4 text-3xl md:text-4xl font-extrabold">+12k</div>
                        <div class="text-indigo-100 text-sm md:text-base mt-1">Ads Created</div>
                    </div>

                    <!-- Stat 2 -->
                    <div class="flex flex-col items-center text-center w-1/3">
                        <div class="p-4 rounded-full bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center text-2xl shadow-lg transform transition-transform hover:scale-110">
                            <i class="fas fa-chart-line"></i>
                        </div>
                        <div class="mt-4 text-3xl md:text-4xl font-extrabold">65%</div>
                        <div class="text-indigo-100 text-sm md:text-base mt-1">Avg Performance Boost</div>
                    </div>

                    <!-- Stat 3 -->
                    <div class="flex flex-col items-center text-center w-1/3">
                        <div class="p-4 rounded-full bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center text-2xl shadow-lg transform transition-transform hover:scale-110">
                            <i class="fas fa-dollar-sign"></i>
                        </div>
                        <div class="mt-4 text-3xl md:text-4xl font-extrabold">$2.4M</div>
                        <div class="text-indigo-100 text-sm md:text-base mt-1">Ad Spend Optimized</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- ============================================ -->
<!-- ADS FEED SECTION -->
<!-- ============================================ -->
<?php include 'ad_page.php'; ?>

<!-- ============================================ -->
<!-- FOOTER -->
<!-- ============================================ -->
<footer class="w-full bg-black/20 backdrop-blur-md shadow-inner text-white mt-20 py-10">
    <div class="max-w-sm mx-auto flex flex-col items-center text-center gap-6 px-4">
        <h2 class="text-lg font-semibold bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 via-pink-400 to-purple-400">
            The future of digital advertising
        </h2>
        <div class="border-t border-white/20 w-full pt-4 text-xs text-white/70">
            &copy; <span id="footer-year"></span> AdSphere. All rights reserved.
        </div>
    </div>
</footer>

<!-- ============================================ -->
<!-- SCRIPTS -->
<!-- ============================================ -->
<script>
// Mobile menu toggle
const mobileBtn = document.getElementById('mobile-menu-button');
const mobileMenu = document.getElementById('mobile-menu');
if (mobileBtn && mobileMenu) {
    mobileBtn.addEventListener('click', () => mobileMenu.classList.toggle('hidden'));
}

// Smooth scrolling for navigation links
document.querySelectorAll('a.nav-link, a.mobile-link, a[href^="#"]').forEach(link => {
    link.addEventListener('click', e => {
        const href = link.getAttribute('href');
        if (href.startsWith('#')) {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
                    mobileMenu.classList.add('hidden');
                }
            }
        }
    });
});

// Set footer year
const footerYear = document.getElementById('footer-year');
if (footerYear) {
    footerYear.textContent = new Date().getFullYear();
}

// Log page load
console.log('🏠 Home page loaded successfully');
console.log('📍 Current URL:', window.location.href);
console.log('⏰ Loaded at:', new Date().toLocaleString());
</script>

</body>
</html>

