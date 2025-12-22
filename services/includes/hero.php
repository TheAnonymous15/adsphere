<section class="relative animated-gradient text-white overflow-hidden pt-24 w-full h-auto">


    <style>
        .animated-gradient {
  background: linear-gradient(
    135deg,
    #6366f1,
    #8b5cf6,
    #d946ef      );
  background-size: 400% 400%;
  animation: gradientShift 10s ease infinite;
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

    </style>

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
            <source src="/services/assets/videos/ad.webm" type="video/webm">
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

    </div>

  </div>

</section>


<script>
    // Mobile menu toggle
    const btn = document.getElementById('mobile-menu-button');
    const menu = document.getElementById('mobile-menu');
    btn.addEventListener('click', () => { menu.classList.toggle('hidden'); });
</script>