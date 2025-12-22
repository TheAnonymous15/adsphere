<?php
?>
<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
    <script defer src="script.js"></script>
<link rel="stylesheet" href="/app/assets/css/all.min.css">
    <link rel="icon" type="image/png" href="icon.png">
    <title>  AdSphere | Power  </title>
</head>
<body class="bg-gray-50 text-gray-900 font-sans leading-relaxed scroll-smooth">


<section class="fixed top-0 left-0 w-full z-50 backdrop-blur-xl bg-white/10 border-b border-white/20 shadow-lg">
    <nav class="max-w-7xl mx-auto px-6 flex items-center justify-between h-20">

        <!-- Branding -->
        <div class="flex items-center space-x-4 group cursor-pointer">
            <div class="p-1 rounded-xl bg-white/20 backdrop-blur-lg shadow-md transition-transform group-hover:scale-105">
                <img src="icc.png" alt="AdSphere Logo" class="h-12 w-auto object-contain">
            </div>
            <h1 class="text-3xl font-extrabold text-white tracking-wide drop-shadow-md">
                AdSphere
            </h1>
        </div>

        <!-- Desktop Menu -->
        <div class="hidden md:flex items-center space-x-8">
            <a href="#features" class="nav-link">Features</a>
            <a href="#marketplace" class="nav-link">Marketplace</a>
            <a href="#pricing" class="nav-link">Pricing</a>
            <a href="#testimonials" class="nav-link">Testimonials</a>
            <a href="#faq" class="nav-link">FAQ</a>

            <a href="#signup"
               class="px-5 py-2.5 bg-white text-indigo-600 rounded-xl font-semibold shadow hover:shadow-lg transition-all hover:-translate-y-0.5">
                Signup
            </a>

            <a href="#login"
               class="px-5 py-2.5 border border-white/70 text-white rounded-xl font-semibold hover:bg-white hover:text-indigo-700 transition-all hover:-translate-y-0.5">
                Login
            </a>
        </div>

        <!-- Mobile Menu Button -->
        <button id="mobile-menu-button" class="md:hidden focus:outline-none text-white">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" 
                      d="M4 8h16M4 16h16"/>
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
        <a href="#login" class="mobile-link font-semibold text-indigo-600">Login</a>
    </div>
</section>

<!-- Shared Styles -->
<style>
    .nav-link {
        @apply text-white/90 hover:text-white font-medium transition-all hover:-translate-y-0.5;
    }
    .mobile-link {
        @apply block px-6 py-3 text-gray-800/90 hover:bg-white/30 hover:text-indigo-600 transition;
    }
</style>

<script>
    const btn = document.getElementById('mobile-menu-button');
    const menu = document.getElementById('mobile-menu');
    btn.addEventListener('click', () => {
        menu.classList.toggle('hidden');
    });
</script>





<section class="relative bg-gradient-to-r from-indigo-500 to-pink-500 text-white overflow-hidden">
    <div class="max-w-7xl mx-auto px-6 py-24 flex flex-col-reverse md:flex-row items-center gap-12">

        <!-- Text Content -->
        <div class="flex-1 text-center md:text-left space-y-6">
            <h1 class="text-5xl md:text-6xl font-extrabold mb-4 leading-tight drop-shadow-lg">
                The Future of Digital Advertising
            </h1>

            <p class="text-xl md:text-2xl text-indigo-100 drop-shadow-sm">
                Create, manage, and deploy ads with AI-powered automation. Upload once, generate multiple formats, and scale performance automatically.
            </p>
            
            <!-- CTA Buttons -->
            <div class="flex flex-col sm:flex-row gap-4 justify-center md:justify-start mt-6">
                <a href="#signup" class="px-6 py-3 bg-white text-indigo-600 font-semibold rounded-xl shadow-lg transform transition hover:-translate-y-1 hover:shadow-2xl">
                    Get Started
                </a>
                <a href="#features" class="px-6 py-3 border border-white text-white rounded-xl font-semibold hover:bg-white hover:text-indigo-600 transition transform hover:-translate-y-1">
                    Learn More
                </a>
            </div>

            <!-- Stats -->
            <div class="mt-10 flex flex-col sm:flex-row justify-center md:justify-start gap-8 text-sm md:text-base text-indigo-100">
                <div class="flex items-center gap-2">
                    <span class="font-bold text-white text-lg md:text-xl">+12k</span>
                    <span>Ads Created</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="font-bold text-white text-lg md:text-xl">65%</span>
                    <span>Avg Performance Boost</span>
                </div>
                <div class="flex items-center gap-2">
                    <span class="font-bold text-white text-lg md:text-xl">$2.4M</span>
                    <span>Ad Spend Optimized</span>
                </div>
            </div>
        </div>

<div class="flex-1 flex justify-center md:justify-end">
  <div class="w-full max-w-lg rounded-3xl shadow-2xl overflow-hidden">
    <!-- Main Video -->
    <div class="relative h-72 md:h-96 w-full rounded-2xl overflow-hidden">
      <video autoplay muted loop playsinline class="w-full h-full object-cover">
        <source src="ad.webm" type="video/webm">
        Your browser does not support the video tag.
      </video>
    </div>
  </div>
</div>
</section>











<section id="cta" class="relative py-24 bg-gradient-to-r from-indigo-500 to-pink-500 text-white text-center overflow-hidden">
    <!-- Decorative Floating Shapes -->
    <div class="absolute -top-16 -left-16 w-72 h-72 bg-white/10 rounded-full animate-spin-slow pointer-events-none"></div>
    <div class="absolute -bottom-16 -right-16 w-72 h-72 bg-white/10 rounded-full animate-spin-slow-reverse pointer-events-none"></div>
    <div class="absolute inset-0 bg-black/20 pointer-events-none"></div>

    <div class="relative max-w-3xl mx-auto px-6">
        <h3 class="text-4xl sm:text-5xl font-extrabold mb-4 leading-tight drop-shadow-lg">Ready to Supercharge Your Ads?</h3>
        <p class="text-lg sm:text-xl mb-8 text-indigo-100 drop-shadow-sm">Start your free trial today and experience AI-powered ad automation that scales effortlessly.</p>

        <button class="px-10 py-4 bg-white text-indigo-600 font-bold rounded-full shadow-2xl hover:scale-105 transform transition duration-300 ease-in-out hover:shadow-indigo-400/50">
            Get Started
        </button>
    </div>
</section>

<style>
    /* Smooth spinning animations for decorative shapes */
    @keyframes spin-slow {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    @keyframes spin-slow-reverse {
        from { transform: rotate(360deg); }
        to { transform: rotate(0deg); }
    }
    .animate-spin-slow { animation: spin-slow 60s linear infinite; }
    .animate-spin-slow-reverse { animation: spin-slow-reverse 60s linear infinite; }
</style>





<!-- Features Section -->
<section id="features" class="py-24 bg-gray-50">
    <div class="max-w-7xl mx-auto px-6 text-center">
        <h3 class="text-4xl font-bold mb-4">Powerful Features</h3>
        <p class="text-gray-600 mb-12 max-w-3xl mx-auto">Everything you need to generate, optimize, and deploy ads at scale — in one platform.</p>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-10">
            <?php
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

            foreach ($features as $f) {
                echo "<div class='bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transform hover:-translate-y-3 transition duration-300'>
                        <div class='w-16 h-16 mb-6 flex items-center justify-center rounded-full bg-gradient-to-r from-indigo-500 to-pink-500 mx-auto'>
                            {$f['icon']}
                        </div>
                        <h4 class='text-xl font-semibold mb-2'>{$f['title']}</h4>
                        <p class='text-gray-600'>{$f['desc']}</p>
                      </div>";
            }
            ?>
        </div>
    </div>
</section>











<!-- Marketplace Section -->
<section id="marketplace" class="py-24 bg-gray-50">
    <div class="max-w-7xl mx-auto px-6 text-center">
        <h3 class="text-4xl font-bold mb-4">Digital Products & Services Marketplace</h3>
        <p class="text-gray-600 mb-12 max-w-3xl mx-auto">Discover ready-to-use tools, AI models, and templates to boost your ad campaigns.</p>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-10">
            <?php
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

            foreach ($marketplace as $m) {
                echo "<div class='bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transform hover:-translate-y-3 transition duration-300'>
                        <div class='w-16 h-16 mb-6 flex items-center justify-center rounded-full bg-gradient-to-r from-indigo-500 to-pink-500 mx-auto'>
                            {$m['icon']}
                        </div>
                        <h4 class='text-xl font-semibold mb-2'>{$m['title']}</h4>
                        <p class='text-gray-600 mb-4'>{$m['desc']}</p>
                        <a href='#' class='inline-block mt-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition'>Explore</a>
                      </div>";
            }
            ?>
        </div>
    </div>
</section>







<!-- AI-Powered Automation Section -->
<section id="ai" class="py-24 bg-white">
    <div class="max-w-7xl mx-auto px-6 text-center">
        <h3 class="text-4xl font-bold mb-4">AI-Powered Automation</h3>
        <p class="text-gray-600 mb-12 max-w-3xl mx-auto">
            Use machine-learning tools for ad prediction, performance scoring, and customer segmentation. Automate creation, targeting, and optimization with real-time insights.
        </p>
        <div class="flex justify-center">
            <div class="w-full max-w-lg h-72 bg-gradient-to-br from-gray-100 to-white rounded-3xl shadow-2xl flex items-center justify-center">
                <span class="text-gray-400">AI Analytics / Dashboard Mockup</span>
            </div>
        </div>
    </div>
</section>

<!-- How It Works Section -->
<section id="how" class="py-24 bg-gray-50">
    <div class="max-w-7xl mx-auto px-6 text-center">
        <h3 class="text-4xl font-bold mb-4">How It Works</h3>
        <p class="text-gray-600 mb-12 max-w-3xl mx-auto">Follow three simple steps to launch and optimize your ad campaigns effortlessly.</p>

        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-10">
            <?php
            $steps = [
                ['step' => '1', 'title' => 'Upload Assets', 'desc' => 'Add product images, description, and goals.', 'icon' => '📤'],
                ['step' => '2', 'title' => 'Auto-generate', 'desc' => 'Generate ads for multiple formats and platforms.', 'icon' => '⚡'],
                ['step' => '3', 'title' => 'Deploy & Optimize', 'desc' => 'Deploy campaigns and let AI optimize performance.', 'icon' => '🚀']
            ];

            foreach ($steps as $s) {
                echo "<div class='bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transform hover:-translate-y-3 transition duration-300'>
                        <div class='w-16 h-16 mb-6 flex items-center justify-center rounded-full bg-gradient-to-r from-indigo-500 to-pink-500 text-white text-2xl'>{$s['icon']}</div>
                        <div class='text-3xl font-bold mb-2'>{$s['step']}</div>
                        <h4 class='text-xl font-semibold mb-2'>{$s['title']}</h4>
                        <p class='text-gray-600'>{$s['desc']}</p>
                      </div>";
            }
            ?>
        </div>
    </div>
</section>




<!-- Testimonials Section -->
<section id="testimonials" class="py-24 bg-white">
    <div class="max-w-7xl mx-auto px-6 text-center">
        <h3 class="text-4xl font-bold mb-4">Testimonials</h3>
        <p class="text-gray-600 mb-12 max-w-3xl mx-auto">What our customers say about AdSphere.</p>

        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-10">
            <?php
            $testimonials = [
                ['name'=>'Alice', 'text'=>'This platform revolutionized our ad campaigns!'],
                ['name'=>'Bob', 'text'=>'AI-generated ads saved us weeks of work.'],
                ['name'=>'Carol', 'text'=>'Revenue increased 35% after using AdSphere.']
            ];

            foreach($testimonials as $t){
                $initial = strtoupper($t['name'][0]);
                echo "<div class='bg-gray-50 rounded-2xl p-8 shadow-lg hover:shadow-2xl transform hover:-translate-y-3 transition duration-300'>
                        <div class='w-16 h-16 rounded-full bg-indigo-500 text-white flex items-center justify-center mx-auto text-xl font-bold mb-4'>{$initial}</div>
                        <svg class='w-8 h-8 mx-auto mb-4 text-indigo-500' fill='none' stroke='currentColor' viewBox='0 0 24 24'>
                            <path stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M7 8h10M7 12h10m-4 4h4'></path>
                        </svg>
                        <p class='text-gray-700 mb-4'>\"{$t['text']}\"</p>
                        <strong class='text-gray-900'>{$t['name']}</strong>
                      </div>";
            }
            ?>
        </div>
    </div>
</section>






<!-- Industry-Specific Ad Solutions Section -->
<section id="industries" class="py-20 bg-gray-50">
    <h3 class="text-4xl font-bold text-center mb-12">Industry-Specific Ad Solutions</h3>

    <div class="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        <?php
        $industries = [
            [
                'name' => 'E-Commerce',
                'products' => 'Fashion, electronics, beauty, gadgets, fitness',
                'ads' => 'Product ads, carousel, retargeting, catalogue'
            ],
            [
                'name' => 'Real Estate',
                'products' => 'Properties, land, rentals, developers',
                'ads' => 'Lead forms, WhatsApp inquiries, video tours'
            ],
            [
                'name' => 'Farming & Agriculture',
                'products' => 'Seeds, fertilizers, machines, livestock',
                'ads' => 'Product ads, lead ads, training promotions'
            ],
            [
                'name' => 'Beauty & Personal Services',
                'products' => 'Salons, spas, clinics',
                'ads' => 'Booking ads, offers, before/after'
            ],
            [
                'name' => 'Food, Restaurants & Catering',
                'products' => 'Restaurants, fast food, catering',
                'ads' => 'Menu ads, promos, order-now ads'
            ],
            [
                'name' => 'Construction & Home Improvement',
                'products' => 'Hardware, décor, contractors',
                'ads' => 'Product showcases, lead forms, portfolios'
            ],
            [
                'name' => 'Local Businesses',
                'products' => 'Gyms, boutiques, car washes, events',
                'ads' => 'Awareness, promos, bookings'
            ],
            [
                'name' => 'Education & Training',
                'products' => 'Schools, courses, coaching',
                'ads' => 'Enrollment ads, webinars, lead ads'
            ],
            [
                'name' => 'Automotive',
                'products' => 'Dealers, rentals, parts, repairs',
                'ads' => 'Catalogue ads, test-drive leads, video ads'
            ],
            [
                'name' => 'Health & Wellness',
                'products' => 'Clinics, hospitals, fitness',
                'ads' => 'Booking, info, awareness'
            ]
        ];

        foreach($industries as $ind){
            echo "<div class='bg-white p-6 rounded-xl shadow hover:shadow-lg transition'>
                    <h4 class='text-xl font-semibold mb-2'>{$ind['name']}</h4>
                    <p class='text-gray-600 mb-2'><strong>Products:</strong> {$ind['products']}</p>
                    <p class='text-gray-600'><strong>Ad Types:</strong> {$ind['ads']}</p>
                </div>";
        }
        ?>
    </div>

    <!-- Additional Industries -->
    <div class="mt-12 text-center">
        <h4 class="text-2xl font-bold mb-4">Additional Industries Supported</h4>
        <p class="text-gray-600 max-w-3xl mx-auto">
            Travel & tourism, Events & entertainment, Technology & SaaS, Finance & insurance, NGOs & non-profits, Sports & fitness, Fashion & lifestyle, Pets & animals, Home services, Arts & crafts, Media & entertainment, Transport & logistics, Legal & consulting, Personal branding, Medical & cosmetic services
        </p>
    </div>
</section>


<!-- Blog/Resources Section -->
<section id="blog" class="py-24 bg-white">
    <div class="max-w-7xl mx-auto px-6 text-center">
        <h3 class="text-4xl font-bold mb-4">Resources & Blog</h3>
        <p class="text-gray-600 mb-12 max-w-3xl mx-auto">Explore guides, tips, and insights to maximize your ad campaigns.</p>

        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-10">
            <?php
            $blogs = [
                ['title'=>'Top 5 Ad Strategies', 'desc'=>'Boost ROI with these proven strategies.', 'link'=>'#'],
                ['title'=>'AI in Marketing', 'desc'=>'How AI is transforming ad campaigns.', 'link'=>'#'],
                ['title'=>'Optimizing Social Ads', 'desc'=>'Tips for social media ad performance.', 'link'=>'#']
            ];

            foreach($blogs as $b){
                echo "<div class='bg-gray-50 rounded-2xl p-8 shadow-lg hover:shadow-2xl transform hover:-translate-y-3 transition duration-300 text-left'>
                        <h4 class='text-xl font-semibold mb-2'>{$b['title']}</h4>
                        <p class='text-gray-700 mb-4'>{$b['desc']}</p>
                        <a href='{$b['link']}' class='text-indigo-600 font-semibold hover:underline'>Read More →</a>
                      </div>";
            }
            ?>
        </div>
    </div>
</section>




<!-- Partners / Logos Section -->
<section id="partners" class="py-24 bg-gray-50">
    <div class="max-w-7xl mx-auto px-6 text-center">
        <h3 class="text-4xl font-bold mb-12">Trusted by</h3>
        <div class="flex flex-wrap justify-center items-center gap-10">
            <?php
            $partners = [
                ['src'=>'https://via.placeholder.com/100x50?text=Logo1','alt'=>'Logo1'],
                ['src'=>'https://via.placeholder.com/100x50?text=Logo2','alt'=>'Logo2'],
                ['src'=>'https://via.placeholder.com/100x50?text=Logo3','alt'=>'Logo3'],
                ['src'=>'https://via.placeholder.com/100x50?text=Logo4','alt'=>'Logo4']
            ];
            foreach($partners as $p){
                echo "<div class='p-4 transition transform hover:scale-110'><img src='{$p['src']}' alt='{$p['alt']}' class='h-12 object-contain filter grayscale hover:grayscale-0 transition'/></div>";
            }
            ?>
        </div>
    </div>
</section>




<!-- FAQ Section -->
<section id="faq" class="py-24 bg-gray-50">
    <div class="max-w-4xl mx-auto px-6 text-center">
        <h3 class="text-4xl font-bold mb-6">Frequently Asked Questions</h3>
        <p class="text-gray-600 mb-12">Find answers to common questions about AdSphere.</p>

        <div class="space-y-4 text-left">
            <?php
            $faqs = [
                ['q'=>'Is there a free trial?', 'a'=>'Yes, a 14-day free trial is available for new users.'],
                ['q'=>'Can I integrate with my CRM?', 'a'=>'Yes, we support multiple CRM and analytics integrations.'],
                ['q'=>'Are the ads optimized automatically?', 'a'=>'Yes, AI models continuously optimize campaigns for best performance.']
            ];

            foreach($faqs as $index => $f){
                echo "<div class='border rounded-xl shadow-sm bg-white'>
                        <button class='w-full px-6 py-4 text-left flex justify-between items-center faq-toggle focus:outline-none'>
                            <span class='font-semibold'>{$f['q']}</span>
                            <span class='text-xl transform transition-transform duration-300'>+</span>
                        </button>
                        <div class='px-6 pb-4 hidden faq-content text-gray-700'>{$f['a']}</div>
                      </div>";
            }
            ?>
        </div>
    </div>
</section>

<script>
// Simple FAQ accordion
document.querySelectorAll('.faq-toggle').forEach(btn => {
    btn.addEventListener('click', () => {
        const content = btn.nextElementSibling;
        const icon = btn.querySelector('span:last-child');
        content.classList.toggle('hidden');
        icon.classList.toggle('rotate-45');
    });
});
</script>



<footer class="bg-black/80 text-gray-200">
  <div class="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">

    <div class="lg:flex lg:items-start lg:gap-10">

      <!-- Logo -->
      <div class="text-teal-500">
        <svg class="h-10" viewBox="0 0 28 24" fill="currentColor">
          <path d="M0.41 10.3847C..."></path>
        </svg>
      </div>

      <div class="mt-10 grid grid-cols-2 gap-12 lg:mt-0 lg:grid-cols-5 lg:gap-y-16">

        <!-- Text -->
        <div class="col-span-2">
          <h2 class="text-3xl font-bold text-white">Stay Updated</h2>
          <p class="mt-4 text-gray-400 text-lg">
            Subscribe to receive exclusive updates and announcements.
          </p>
        </div>

        <!-- Subscription -->
        <div class="col-span-2 lg:col-span-3 lg:flex lg:items-end">
          <form class="w-full">
            
            <div class="bg-white/10 backdrop-blur-md border border-white/20 
                        p-2 rounded-full flex items-center gap-2 shadow-xl">

              <input 
                type="email" 
                id="UserEmail" 
                placeholder="Enter your email address..."
                class="w-full bg-transparent text-gray-200 placeholder-gray-400 
                       px-4 py-3 rounded-full focus:outline-none text-lg"
              />

              <button 
                class="bg-teal-500 hover:bg-teal-600 
                       text-white font-semibold px-8 py-3 rounded-full text-lg shadow-md">
                Subscribe
              </button>

            </div>






          </form>
        </div>



        

        <!-- Services -->
        <div class="col-span-2 sm:col-span-1">
          <p class="font-semibold text-white text-lg">Services</p>
          <ul class="mt-6 space-y-3 text-sm">
            <li><a href="#" class="hover:text-teal-400"> 1on1 Coaching </a></li>
            <li><a href="#" class="hover:text-teal-400"> Company Review </a></li>
            <li><a href="#" class="hover:text-teal-400"> Accounts Review </a></li>
            <li><a href="#" class="hover:text-teal-400"> HR Consulting </a></li>
            <li><a href="#" class="hover:text-teal-400"> SEO Optimisation </a></li>
          </ul>
        </div>

        <!-- Other Columns (Company, Legal, etc.) -->
        <div class="col-span-2 sm:col-span-1">
          <p class="font-semibold text-white text-lg">Company</p>
          <ul class="mt-6 space-y-3 text-sm">
            <li><a href="#" class="hover:text-teal-400"> About </a></li>
            <li><a href="#" class="hover:text-teal-400"> Meet the Team </a></li>
            <li><a href="#" class="hover:text-teal-400"> Careers </a></li>
          </ul>
        </div>

        <div class="col-span-2 sm:col-span-1">
          <p class="font-semibold text-white text-lg">Helpful Links</p>
          <ul class="mt-6 space-y-3 text-sm">
            <li><a href="#" class="hover:text-teal-400"> Contact </a></li>
            <li><a href="#" class="hover:text-teal-400"> FAQs </a></li>
            <li><a href="#" class="hover:text-teal-400"> Support </a></li>
          </ul>
        </div>

        <div class="col-span-2 sm:col-span-1">
          <p class="font-semibold text-white text-lg">Legal</p>
          <ul class="mt-6 space-y-3 text-sm">
            <li><a href="#" class="hover:text-teal-400"> Accessibility </a></li>
            <li><a href="#" class="hover:text-teal-400"> Returns Policy </a></li>
            <li><a href="#" class="hover:text-teal-400"> Refund Policy </a></li>
          </ul>
        </div>

        <!-- Social Icons -->
        <ul class="col-span-2 flex justify-start gap-6 lg:col-span-5 lg:justify-end mt-10">
          <li><a href="#" class="text-gray-400 hover:text-teal-400"><i class="fab fa-facebook text-2xl"></i></a></li>
          <li><a href="#" class="text-gray-400 hover:text-teal-400"><i class="fab fa-instagram text-2xl"></i></a></li>
          <li><a href="#" class="text-gray-400 hover:text-teal-400"><i class="fab fa-twitter text-2xl"></i></a></li>
          <li><a href="#" class="text-gray-400 hover:text-teal-400"><i class="fab fa-github text-2xl"></i></a></li>
        </ul>

      </div>
    </div>

    <div class="mt-12 border-t border-white/10 pt-8">
      <div class="sm:flex sm:justify-between text-gray-400">
        <p class="text-sm">© 2025. Company Name. All rights reserved.</p>

        <ul class="mt-6 flex flex-wrap gap-6 text-sm sm:mt-0">
          <li><a href="#" class="hover:text-teal-400">Terms & Conditions</a></li>
          <li><a href="#" class="hover:text-teal-400">Privacy Policy</a></li>
          <li><a href="#" class="hover:text-teal-400">Cookies</a></li>
        </ul>
      </div>
    </div>

  </div>
</footer>


</body>
</html> 