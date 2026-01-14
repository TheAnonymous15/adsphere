<?php
$currentPage = '500';

?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
  <title>500 - System Failure | AdSphere</title>

  <style>
    /* Power icon shake */
    @keyframes shake {
      0% { transform: translate(0); }
      25% { transform: translate(-2px, 2px); }
      50% { transform: translate(2px, -2px); }
      75% { transform: translate(-2px, -1px); }
      100% { transform: translate(0); }
    }

    /* Crack effect */
    .crack {
      background-size: contain;
      background-repeat: no-repeat;
      background-position: center;
      opacity: 0.25;
      pointer-events: none;
    }
  </style>
</head>

<body class="bg-gradient-to-br from-purple-900 via-indigo-800/50 to-black bg-cover text-white font-sans min-h-screen flex flex-col items-center justify-center text-center px-6"
      style="background-image: url('/static/images/ad.jpg');">

  <div class="relative bg-white/10 backdrop-blur-xl rounded-3xl p-12 shadow-2xl max-w-lg animate-fadeIn border border-white/10 overflow-hidden">

    <!-- crack overlay -->
    <div class="absolute inset-0 crack"></div>

    <!-- POWER DISCONNECT ICON -->
    <div class="text-6xl mb-4 animate-shake">
      🔌
    </div>

    <!-- CLEAN STATIC 500 -->
    <h1 class="text-8xl font-extrabold drop-shadow-2xl">
      500
    </h1>

    <!-- subtitle text -->
    <p class="mt-6 text-xl text-indigo-200 leading-relaxed opacity-90">
      The system just <span class="text-pink-300 font-bold">lost power</span>.<br>
      Every circuit, node, and advertising particle just… <br>
      <span class="text-white font-semibold">disconnected.</span>
    </p>

    <!-- Warning pulse -->
    <p class="mt-3 text-sm text-red-300 tracking-widest animate-pulse">
      ⚠ CORE FAILURE — SIGNAL LOST
    </p>

    <!-- Button -->
    <a href="/" 
      class="mt-8 inline-block bg-white/20 hover:bg-white/30 text-white px-8 py-3 rounded-xl font-semibold 
            transition-transform hover:scale-110 backdrop-blur-md">
      Reboot System
    </a>

    <!-- floating particles -->
    <div class="absolute top-4 right-4 text-pink-300 opacity-50 animate-ping">●</div>
    <div class="absolute bottom-6 left-10 text-cyan-300 opacity-40 animate-ping">●</div>

    <!-- Footer -->
    <div class="mt-10 text-white/70 text-sm">
      &copy; <?= date('Y') ?> AdSphere • Elevating Digital Intelligence
    </div>

  </div>

</body>
</html>
