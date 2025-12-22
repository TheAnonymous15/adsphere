<?php
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.tailwindcss.com"></script>
    <link rel="icon" type="image/png" href="/services/assets/images/icon.png">
    <link rel="stylesheet" href="/services/assets/css/all.min.css">
    <title>AdSphere | Coming Soon</title>
</head>

<body class="
             animated-gradient
             text-white font-sans min-h-screen flex flex-col">
    <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div class="absolute w-72 h-72 bg-white/10 rounded-full -top-16 -left-16 animate-spin-slow"></div>
        <div class="absolute w-96 h-96 bg-white/10 rounded-full -bottom-24 -right-24 animate-spin-slow-reverse"></div>
        <div class="absolute w-60 h-60 bg-white/5 rounded-full -bottom-12 left-1/3 animate-pulse-slow"></div>
    </div>





    <section class="max-w-7xl mx-auto gradient px-6 py-20 flex flex-col md:flex-row items-center gap-12 relative z-10">
        <div class="flex-1 text-center md:text-left space-y-6 bg-white/10 backdrop-blur-md rounded-3xl p-8 md:p-12 shadow-2xl animate-fadeIn">
          

            <img src="/services/assets/images/adic.png"
            class="h-30 w-aut mx-auto md:mx-0 transition-transform 
            duration-500 hover:scale-110 hover:rotate-3 hover:drop-shadow-[0_15px_35px_rgba(139,92,246,0.7)]"/><hr>
            <h1 class="text-5xl sm:text-6xl font-extrabold leading-tight
                       bg-clip-text text-transparent 
                       bg-gradient-to-r from-indigo-300 via-pink-400 to-purple-400 
                       drop-shadow-[0_5px_15px_rgba(0,0,0,0.5)]
                       animate-fadeIn">
                Coming Soon
            </h1>

            <p class="text-lg sm:text-xl text-indigo-100 drop-shadow-sm max-w-lg mx-auto md:mx-0">
                AdSphere is launching soon! Get ready for AI-powered digital advertising that automates your campaigns effortlessly.
            </p>
            <div class="flex justify-center md:justify-start gap-4 text-white text-2xl font-bold mt-4">
                <div class="bg-white/20 px-4 py-2 rounded-lg animate-pulse"><span id="days">00</span> Days</div>
                <div class="bg-white/20 px-4 py-2 rounded-lg animate-pulse"><span id="hours">00</span> Hrs</div>
                <div class="bg-white/20 px-4 py-2 rounded-lg animate-pulse"><span id="minutes">00</span> Min</div>
                <div class="bg-white/20 px-4 py-2 rounded-lg animate-pulse"><span id="seconds">00</span> Sec</div>
            </div>
            <form class="w-full mt-6">
                <div class="bg-white/10 backdrop-blur-md border border-white/20 p-2 rounded-xl flex items-center gap-2 shadow-xl">
                <input type="email" id="UserEmail" placeholder="Enter your email address..."
                           class="w-full bg-white text-black placeholder-gray-400 px-4 py-3 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-400 focus:ring-offset-1 transition duration-300 text-lg"/>
                <button class="bg-teal-500 hover:bg-teal-600 text-white font-semibold py-3 rounded-xl text-lg shadow-md px-10 min-w-[180px] whitespace-nowrap transition transform hover:scale-105 hover:shadow-lg">
                        Count me in
                </button>
                </div>
            </form>
            <div class="flex justify-center md:justify-center items-center gap-6 mt-6">
                <a href="#" class="group w-12 h-12 rounded-full bg-white/10 flex items-center justify-center text-white shadow-lg transition transform hover:scale-110 hover:bg-white hover:text-indigo-600">
                    <i class="fab fa-facebook-f group-hover:text-indigo-600 transition duration-300"></i>
                </a>
                <a href="#" class="group w-12 h-12 rounded-full bg-white/10 flex items-center justify-center text-white shadow-lg transition transform hover:scale-110 hover:bg-white hover:text-pink-500">
                    <i class="fab fa-twitter group-hover:text-pink-500 transition duration-300"></i>
                </a>
                <a href="#" class="group w-12 h-12 rounded-full bg-white/10 flex items-center justify-center text-white shadow-lg transition transform hover:scale-110 hover:bg-white hover:text-pink-400">
                    <i class="fab fa-instagram group-hover:text-pink-400 transition duration-300"></i>
                </a>
                <a href="#" class="group w-12 h-12 rounded-full bg-white/10 flex items-center justify-center text-white shadow-lg transition transform hover:scale-110 hover:bg-white hover:text-blue-500">
                    <i class="fab fa-linkedin-in group-hover:text-blue-500 transition duration-300"></i>
                </a>
            </div>

            <center><div class="mt-10 text-white/70 text-sm">&copy; 2025 AdSphere • Elevating Digital Intelligence</div></center>

        </div>

        <div class="flex-1 w-full max-w-lg shadow-2xl overflow-hidden relative group">
            <div class="relative h-72 md:h-96 w-full rounded-2xl overflow-hidden">
                <video autoplay loop muted playsinline class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105">
                    <source src="/services/assets/videos/ad.webm" type="video/webm">
                    Your browser does not support the video tag.
                </video>
                <div class="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-black/40 pointer-events-none"></div>
                <div class="absolute inset-0 rounded-2xl border-4 border-indigo-500/30 shadow-[0_0_60px_#8b5cf6] pointer-events-none"></div>
            </div>
            <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                <svg class="w-16 h-16 text-white/50 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                         <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                          d="M14.752 11.168l-6.518-3.759A1 1 0 007 8.216v7.568a1 1 0 001.234.97l6.518-1.568a1 1 0 00.618-.97v-4.048a1 1 0 00-.618-.97z"></path>
                </svg>
            </div>
        </div>
    </section>




    <script>
        const targetDate = new Date("Dec 31, 2025 00:00:00").getTime();
        const daysEl = document.getElementById('days');
        const hoursEl = document.getElementById('hours');
        const minutesEl = document.getElementById('minutes');
        const secondsEl = document.getElementById('seconds');

        setInterval(() => {
            const now = new Date().getTime();
            const distance = targetDate - now;

            const days = Math.floor(distance / (1000 * 60 * 60 * 24));
            const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000*60*60));
            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000*60));
            const seconds = Math.floor((distance % (1000 * 60)) / 1000);

            daysEl.innerText = days.toString().padStart(2,'0');
            hoursEl.innerText = hours.toString().padStart(2,'0');
            minutesEl.innerText = minutes.toString().padStart(2,'0');
            secondsEl.innerText = seconds.toString().padStart(2,'0');
        }, 1000);
    </script>

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

        @keyframes fadeIn { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
        .animate-fadeIn { animation: fadeIn 1s ease-out forwards; }

        @keyframes spin-slow { from{transform:rotate(0deg);} to{transform:rotate(360deg);} }
        @keyframes spin-slow-reverse { from{transform:rotate(360deg);} to{transform:rotate(0deg);} }
        @keyframes pulse-slow { 0%,100%{opacity:0.2;}50%{opacity:0.5;} }
        .animate-spin-slow { animation: spin-slow 60s linear infinite; }
        .animate-spin-slow-reverse { animation: spin-slow-reverse 90s linear infinite; }
        .animate-pulse-slow { animation: pulse-slow 6s ease-in-out infinite; }
    </style>
<footer class="mt-auto bg-white/10 backdrop-blur-md shadow-inner text-white w-full py-5">
  <div class="border-t border-white/20 pt-4 text-center flex flex-col items-center">

    <h2 class="text-lg sm:text-xl font-semibold bg-clip-text text-transparent 
               bg-gradient-to-r from-indigo-300 via-pink-400 to-purple-400">
      The future of digital advertising
    </h2>

    <p class="text-white/70 text-xs sm:text-sm mt-1">
      &copy; 2025 AdSphere. All rights reserved.
    </p>

  </div>
</footer>
</body>
</html>
