<?php
// --- DATA ARRAYS ---
$features = [
    [
        'title' => 'AI Ad Generator',
        'desc' => 'Create ads in text, image, or video formats using powerful AI tools.',
        'icon' => '<svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
                  </svg>'
    ],
    [
        'title' => 'Smart Targeting',
        'desc' => 'Target the right customers using behavioral and predictive analytics.',
        'icon' => '<svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 1.567-3 3.5S10.343 15 12 15s3-1.567 3-3.5S13.657 8 12 8z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.4 15a7 7 0 10-14.8 0"></path>
                  </svg>'
    ],
    [
        'title' => 'Multi-Platform Publishing',
        'desc' => 'Publish ads across social media, web, mobile, and partner networks.',
        'icon' => '<svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h4l3 8 4-16 3 8h4"></path>
                  </svg>'
    ]
];

$marketplace = [
    [
        'title' => 'Graphic Templates',
        'desc' => 'Editable ad banners, posters, social media templates.',
        'icon' => '<svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                  </svg>'
    ],
    [
        'title' => 'AI Ad Models',
        'desc' => 'Pre-trained models for ad optimization and recommendation.',
        'icon' => '<svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-6a6 6 0 0112 0v6"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 11H3v6h6v-6z"></path>
                  </svg>'
    ],
    [
        'title' => 'Automation Tools',
        'desc' => 'Scheduling, analytics, lead tracking and integrations.',
        'icon' => '<svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 1.567-3 3.5S10.343 15 12 15s3-1.567 3-3.5S13.657 8 12 8z"></path>
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.4 15a7 7 0 10-14.8 0"></path>
                  </svg>'
    ]
];

$steps = [
    ['step' => '1', 'title' => 'Upload Assets', 'desc' => 'Add product images, description, and goals.', 'icon' => '📤'],
    ['step' => '2', 'title' => 'Auto-generate', 'desc' => 'Generate ads for multiple formats and platforms.', 'icon' => '⚡'],
    ['step' => '3', 'title' => 'Deploy & Optimize', 'desc' => 'Deploy campaigns and let AI optimize performance.', 'icon' => '🚀']
];

$testimonials = [
    ['name'=>'Alice', 'text'=>'This platform revolutionized our ad campaigns!'],
    ['name'=>'Bob', 'text'=>'AI-generated ads saved us weeks of work.'],
    ['name'=>'Carol', 'text'=>'Revenue increased 35% after using AdSphere.']
];

$faqs = [
    ['q'=>'Is there a free trial?', 'a'=>'Yes, a 14-day free trial is available for new users.'],
    ['q'=>'Can I integrate with my CRM?', 'a'=>'Yes, we support multiple CRM and analytics integrations.'],
    ['q'=>'Are the ads optimized automatically?', 'a'=>'Yes, AI models continuously optimize campaigns for best performance.']
];
?>






<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AdSphere | Power</title>
    <link rel="icon" type="image/png" href="icon.png">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <style>
        /* Shared classes */
        .nav-link { @apply text-white/90 hover:text-white font-medium transition-all hover:-translate-y-0.5; }
        .mobile-link { @apply block px-6 py-3 text-gray-800/90 hover:bg-white/30 hover:text-indigo-600 transition; }
        .animate-spin-slow { animation: spin-slow 60s linear infinite; }
        .animate-spin-slow-reverse { animation: spin-slow-reverse 60s linear infinite; }
        @keyframes spin-slow { from {transform: rotate(0deg);} to {transform: rotate(360deg);} }
        @keyframes spin-slow-reverse { from {transform: rotate(360deg);} to {transform: rotate(0deg);} }
    </style>
</head>
<body class="bg-gray-50 text-gray-900 font-sans leading-relaxed scroll-smooth">

<!-- NAVIGATION -->
<section class="fixed top-0 left-0 w-full z-50 backdrop-blur-xl bg-white/10 border-b border-white/20 shadow-lg">
    <nav class="max-w-7xl mx-auto px-6 flex items-center justify-between h-20">
        <!-- Branding -->
        


        <div class="flex items-center space-x-4 group cursor-pointer">
            <div class="p-1  bg-white/20shadow-md transition-transform group-hover:scale-105">
                <img src="/app/assets/images/icon.png"  class="h-20 w-50">
            </div>
            <h1 class="text-3xl font-extrabold text-white tracking-wide drop-shadow-md"></h1>
        </div>




        <!-- Desktop Menu -->
        <div class="hidden md:flex items-center space-x-8">
            <a href="#features" class="nav-link">Features</a>
            <a href="#marketplace" class="nav-link">Marketplace</a>
            <a href="#pricing" class="nav-link">Pricing</a>
            <a href="#testimonials" class="nav-link">Testimonials</a>
            <a href="#faq" class="nav-link">FAQ</a>
            <a href="signup" class="px-5 py-2.5 bg-white text-indigo-600 rounded-xl font-semibold shadow hover:shadow-lg transition-all hover:-translate-y-0.5">Signup</a>
            <a href="login" class="px-5 py-2.5 border border-white/70 text-white rounded-xl font-semibold hover:bg-white hover:text-indigo-700 transition-all hover:-translate-y-0.5">Login</a>
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
        <a href="login" class="mobile-link font-semibold text-indigo-600">Login</a>
    </div>
</section>

<script>
    // Mobile menu toggle
    const btn = document.getElementById('mobile-menu-button');
    const menu = document.getElementById('mobile-menu');
    btn.addEventListener('click', () => { menu.classList.toggle('hidden'); });
</script>










<section class="relative bg-gradient-to-r from-indigo-500 to-pink-500 text-white overflow-hidden pt-24 w-full h-auto">
  <div class="max-w-7xl mx-auto px-6 py-24 grid grid-cols-1 md:grid-cols-2 gap-12">

    <!-- LEFT COLUMN -->
    <div class="flex flex-col justify-between h-full gap-8">
      <!-- Branding / Headline -->
      <div class="space-y-6 text-center md:text-left">
        <h1 class="text-5xl md:text-6xl font-extrabold leading-tight drop-shadow-lg">The Future of Digital Advertising</h1>
        <p class="text-xl md:text-2xl text-indigo-100 drop-shadow-sm">
          Create, manage, and deploy ads with AI-powered automation. Upload once, generate multiple formats, and scale performance automatically.
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center md:justify-start mt-6">
          <a href="#signup" class="px-6 py-3 bg-white text-indigo-600 font-semibold rounded-xl shadow-lg transform transition hover:-translate-y-1 hover:shadow-2xl">Get Started</a>
          <a href="#features" class="px-6 py-3 border border-white text-white rounded-xl font-semibold hover:bg-white hover:text-indigo-600 transition transform hover:-translate-y-1">Learn More</a>
        </div>
      </div>

      <!-- Boost Subsection -->
      <div class="w-full bg-white/10 backdrop-blur-md rounded-2xl p-6 shadow-lg flex flex-col gap-4">
        <h3 class="text-xl md:text-2xl font-bold text-white">Boost Your Ads Instantly</h3>
        <p class="text-indigo-100 text-sm md:text-base">
          With AdSphere, you can automate campaigns, track performance, and scale your ad spend efficiently—all in one platform.
        </p>
        <a href="#signup" class="mt-2 px-4 py-2 bg-indigo-500 text-white font-semibold rounded-xl shadow hover:shadow-lg transition transform hover:-translate-y-0.5 w-max">Get Started</a>
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
    <div class="flex flex-col items-center text-center w-1/3 animate-fade-up delay-100">
      <div class="p-4 rounded-full bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center text-2xl shadow-lg transform transition-transform hover:scale-110">
        <i class="fas fa-bullhorn"></i>
      </div>
      <div class="mt-4 text-3xl md:text-4xl font-extrabold">+12k</div>
      <div class="text-indigo-100 text-sm md:text-base mt-1">Ads Created</div>
    </div>

    <!-- Stat 2 -->
    <div class="flex flex-col items-center text-center w-1/3 animate-fade-up delay-300">
      <div class="p-4 rounded-full bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center text-2xl shadow-lg transform transition-transform hover:scale-110">
        <i class="fas fa-chart-line"></i>
      </div>
      <div class="mt-4 text-3xl md:text-4xl font-extrabold">65%</div>
      <div class="text-indigo-100 text-sm md:text-base mt-1">Avg Performance Boost</div>
    </div>

    <!-- Stat 3 -->
    <div class="flex flex-col items-center text-center w-1/3 animate-fade-up delay-500">
      <div class="p-4 rounded-full bg-gradient-to-tr from-indigo-500 to-pink-500 flex items-center justify-center text-2xl shadow-lg transform transition-transform hover:scale-110">
        <i class="fas fa-dollar-sign"></i>
      </div>
      <div class="mt-4 text-3xl md:text-4xl font-extrabold">$2.4M</div>
      <div class="text-indigo-100 text-sm md:text-base mt-1">Ad Spend Optimized</div>
    </div>

  </div>
</div>

<!-- Add this inside your <style> or Tailwind custom styles -->
<style>
@keyframes fadeUp {
  0% { opacity: 0; transform: translateY(20px); }
  100% { opacity: 1; transform: translateY(0); }
}
.animate-fade-up {
  animation: fadeUp 1s ease forwards;
}
.delay-100 { animation-delay: 0.1s; }
.delay-300 { animation-delay: 0.3s; }
.delay-500 { animation-delay: 0.5s; }
</style>





    </div>

  </div>
</section>
















<!-- FEATURES -->
<section id="features" class="py-24 bg-gray-50 w-full">
    <div class="max-w-7xl mx-auto px-6 text-center">
        <h3 class="text-4xl font-bold mb-4">Powerful Features</h3>
        <p class="text-gray-600 mb-12 max-w-3xl mx-auto">Everything you need to generate, optimize, and deploy ads at scale — in one platform.</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-10">
            <?php foreach($features as $f): ?>
            <div class="bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transform hover:-translate-y-3 transition duration-300">
                <div class="w-16 h-16 mb-6 flex items-center justify-center rounded-full bg-gradient-to-r from-indigo-500 to-pink-500 mx-auto"><?= $f['icon'] ?></div>
                <h4 class="text-xl font-semibold mb-2"><?= $f['title'] ?></h4>
                <p class="text-gray-600"><?= $f['desc'] ?></p>
            </div>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<!-- How It Works Section -->
<section id="how" class="py-24 bg-gray-50 w-full">
    <div class="max-w-7xl mx-auto px-6 text-center">
        <h3 class="text-4xl font-bold mb-4">How It Works</h3>
        <p class="text-gray-600 mb-12 max-w-3xl mx-auto">Follow three simple steps to launch and optimize your ad campaigns effortlessly.</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-10">
            <?php foreach($steps as $s): ?>
            <div class="bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transform hover:-translate-y-3 transition duration-300">
                <div class="w-16 h-16 mb-6 flex items-center justify-center rounded-full bg-gradient-to-r from-indigo-500 to-pink-500 text-white text-2xl"><?= $s['icon'] ?></div>
                <div class="text-3xl font-bold mb-2"><?= $s['step'] ?></div>
                <h4 class="text-xl font-semibold mb-2"><?= $s['title'] ?></h4>
                <p class="text-gray-600"><?= $s['desc'] ?></p>
            </div>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<!-- TESTIMONIALS -->
<section id="testimonials" class="py-24 bg-white w-full">
    <div class="max-w-7xl mx-auto px-6 text-center">
        <h3 class="text-4xl font-bold mb-4">Testimonials</h3>
        <p class="text-gray-600 mb-12 max-w-3xl mx-auto">What our customers say about AdSphere.</p>
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-10">
            <?php foreach($testimonials as $t): 
                $initial = strtoupper($t['name'][0]); ?>
            <div class="bg-gray-50 rounded-2xl p-8 shadow-lg hover:shadow-2xl transform hover:-translate-y-3 transition duration-300">
                <div class="w-16 h-16 rounded-full bg-indigo-500 text-white flex items-center justify-center mx-auto text-xl font-bold mb-4"><?= $initial ?></div>
                <p class="text-gray-700 mb-4">"<?= $t['text'] ?>"</p>
                <strong class="text-gray-900"><?= $t['name'] ?></strong>
            </div>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<!-- FAQ SECTION -->
<section id="faq" class="py-24 bg-gray-50 w-full" >
    <div class="max-w-4xl mx-auto px-6 text-center">
        <h3 class="text-4xl font-bold mb-6">Frequently Asked Questions</h3>
        <div class="space-y-4 text-left">
            <?php foreach($faqs as $f): ?>
            <div class="border rounded-xl shadow-sm bg-white">
                <button class="w-full px-6 py-4 text-left flex justify-between items-center faq-toggle focus:outline-none">
                    <span class="font-semibold"><?= $f['q'] ?></span>
                    <span class="text-xl transform transition-transform duration-300">+</span>
                </button>
                <div class="px-6 pb-4 hidden faq-content text-gray-700"><?= $f['a'] ?></div>
            </div>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<script>
    // FAQ toggle
    document.querySelectorAll('.faq-toggle').forEach(btn => {
        btn.addEventListener('click', () => {
            const content = btn.nextElementSibling;
            const icon = btn.querySelector('span:last-child');
            content.classList.toggle('hidden');
            icon.classList.toggle('rotate-45');
        });
    });
</script>

</body>
</html>
