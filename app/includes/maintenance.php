<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Maintenance | AdSphere</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css" integrity="sha512-papcTL2qU7su3yJr0xdvEbsP2ELGH/sPfH3pJZlXLh6jwXCM6wFM6cVqHkXlY7yY2yAx3Er1Rhw58Vbxdl0M5g==" crossorigin="anonymous" referrerpolicy="no-referrer" />

  <style>
    /* Floating background orbs */
    @keyframes float {
      0% { transform: translateY(0); }
      50% { transform: translateY(-10px); }
      100% { transform: translateY(0); }
    }

    .float-orb { animation: float 6s ease-in-out infinite; }

    /* Pulse glow animation */
    @keyframes pulse-glow {
      0%, 100% { opacity: 0.4; transform: scale(1); }
      50% { opacity: 1; transform: scale(1.1); }
    }

    .pulse-orb { animation: pulse-glow 4s ease-in-out infinite; }
  </style>
</head>
<body class="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-gray-800 to-gray-950 text-gray-100 font-sans relative px-4 overflow-hidden"
      style="background-image: url('/app/assets/images/ad.jpg'); background-size: cover;">

  <!-- Floating background orbs -->
  <div class="absolute top-10 left-10 w-80 h-80 bg-indigo-600/20 rounded-full blur-3xl pulse-orb"></div>
  <div class="absolute bottom-10 right-10 w-96 h-96 bg-pink-600/20 rounded-full blur-3xl pulse-orb"></div>

  <!-- Maintenance card -->
  <div class="max-w-lg w-full mx-auto bg-white/10 backdrop-blur-xl rounded-3xl p-8 shadow-[0_0_50px_rgba(255,255,255,0.2)] border border-white/20 text-center relative overflow-hidden">
    
    <!-- Floating pulsing image -->
    <div class="mx-auto w-32 h-32 relative rounded-full bg-white/10 backdrop-blur-md border border-white/20 mb-6 shadow-lg overflow-hidden">
      <!-- Glow behind the image -->
      <div class="absolute inset-0 rounded-full bg-gradient-to-tr from-indigo-400/40 via-pink-400/30 to-purple-400/40 filter blur-2xl animate-pulse"></div>
      <!-- Maintenance Image -->
      <img src="/app/assets/images/maintenance.jpg" 
           alt="Maintenance" 
           class="w-full h-full object-cover rounded-full relative z-10">
    </div>

    <!-- Title -->
    <h1 class="text-5xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-pink-300 to-indigo-300 drop-shadow-xl mb-4">
      Maintenance Mode
    </h1>

    <!-- Subtitle -->
    <p class="text-lg text-indigo-100 mb-6 leading-relaxed">
      We’re currently performing scheduled maintenance.<br>
      Thank you for your patience.
    </p>

    <!-- Urgent inquiry section -->
    <div class="mt-6 text-center">
      <p class="text-sm text-white/70 mb-4">
        For urgent inquiries, reach out:
      </p>



<div class="flex justify-center gap-2 mt-4 flex-wrap">
  <!-- Call Now -->
  <a href="tel:+254726781724"
     class="inline-flex items-center justify-center gap-2 bg-green-500 hover:bg-green-600 text-white rounded-xl font-semibold transition-transform hover:scale-105 shadow-lg backdrop-blur-md border border-white/20"
     style="width:100px; height:30px;">
    <i class="fas fa-phone-alt text-sm"></i>
    <span class="text-xs">Call</span>
  </a>

  <!-- Send SMS -->
  <a href="sms:+254726781724"
     class="inline-flex items-center justify-center gap-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-xl font-semibold transition-transform hover:scale-105 shadow-lg backdrop-blur-md border border-white/20"
     style="width:100px; height:30px;">
    <i class="fas fa-comment-alt text-sm"></i>
    <span class="text-xs">SMS</span>
  </a>

  <!-- Email Us -->
  <a href="mailto:support@adsphere.com"
     class="inline-flex items-center justify-center gap-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-xl font-semibold transition-transform hover:scale-105 shadow-lg backdrop-blur-md border border-white/20"
     style="width:100px; height:30px;">
    <i class="fas fa-envelope text-sm"></i>
    <span class="text-xs">Email</span>
  </a>
</div>





    </div>

    <!-- Footer -->
    <div class="mt-8 text-white/50 text-sm">
      &copy; <span id="currentYear"></span> AdSphere • Elevating Digital Intelligence
    </div>
  </div>

  <script>
    document.getElementById('currentYear').textContent = new Date().getFullYear();
  </script>
</body>
</html>
