<?php
$currentPage = '403';

?>


<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
  <title>403 - Access Denied | AdSphere</title>

  <style>
    @keyframes float {
      0% { transform: translateY(0px); }
      50% { transform: translateY(-12px); }
      100% { transform: translateY(0px); }
    }
    @keyframes pulse-glow {
      0%, 100% { opacity: 0.4; transform: scale(1); }
      50% { opacity: 1; transform: scale(1.15); }
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
  </style>
</head>

<body class="min-h-screen flex flex-col items-center justify-center text-white font-sans overflow-hidden
             bg-cover bg-center relative"
      style="background-image: url('/static/images/ad.jpg');">

  <!-- Floating blurry orbs -->
  <div class="absolute top-10 left-10 w-72 h-72 bg-pink-400/30 blur-3xl rounded-full animate-pulse-glow"></div>
  <div class="absolute bottom-10 right-10 w-96 h-96 bg-indigo-400/30 blur-[120px] rounded-full animate-pulse-glow"></div>

  <!-- Main card -->
  <div class="relative bg-white/10 backdrop-blur-xl p-10 rounded-3xl shadow-[0_0_60px_rgba(255,255,255,0.25)] max-w-lg text-center animate-fadeIn border border-white/20">

    <!-- Floating lock icon -->
    <div class="mx-auto mb-6 w-24 h-24 rounded-full bg-white/10 backdrop-blur-md flex items-center justify-center border border-white/20 shadow-xl animate-float">
      <svg class="w-14 h-14 text-white/80" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round"
          d="M16 10V8a4 4 0 10-8 0v2m-2 0h12a2 2 0 012 2v7a2 
             2 0 01-2 2H6a2 2 0 01-2-2v-7a2 2 0 012-2z" />
      </svg>
    </div>

    <h1 class="text-7xl sm:text-8xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-pink-300 to-indigo-300 drop-shadow-xl">
      403
    </h1>

    <p class="mt-4 text-lg text-indigo-100 leading-relaxed">
      <span class="font-semibold">Access Restricted.</span><br>
      This area is locked and requires special permissions.
    </p>

    <!-- Button -->
    <a href="/" 
       class="mt-6 inline-block bg-white/20 hover:bg-white/30 text-white px-10 py-3 rounded-xl font-semibold transition-transform hover:scale-110 backdrop-blur-md shadow-lg border border-white/20">
      Return Home
    </a>

    <!-- Footer -->
    <div class="mt-10 text-white/70 text-sm">
      &copy; <?= date('Y') ?> AdSphere • Elevating Digital Intelligence
    </div>

  </div>

</body>
</html>
