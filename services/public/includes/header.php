  <script src="https://cdn.tailwindcss.com"></script>


<header class="fixed top-0 left-0 w-full z-50 backdrop-blur-xl bg-white/10 border-b border-white/20 shadow-lg">
<nav class="max-w-7xl mx-auto px-6 flex items-center justify-between h-20">

    <!-- Branding -->
    <div class="flex items-center space-x-4 group cursor-pointer">
        <div class="p-1 rounded-xl bg-white/20 backdrop-blur-lg shadow-md transition-transform group-hover:scale-105">
            <img src="/services/assets/images/icc.png" alt="AdSphere Logo" class="h-12 w-auto object-contain">
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
    <a href="#login" class="mobile-link font-semibold text-indigo-600">Login</a>
</div>
</header>

<script>
const btn = document.getElementById('mobile-menu-button');
const menu = document.getElementById('mobile-menu');
btn.addEventListener('click', () => menu.classList.toggle('hidden'));

// Smooth scrolling
document.querySelectorAll('a.nav-link, a.mobile-link').forEach(link => {
    link.addEventListener('click', e => {
        e.preventDefault();
        const target = document.querySelector(link.getAttribute('href'));
        if(target){
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            if(!menu.classList.contains('hidden')) menu.classList.add('hidden');
        }
    });
});
</script>
