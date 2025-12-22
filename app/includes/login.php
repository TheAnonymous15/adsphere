<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Next Level Login</title>

  <script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="/app/assets/css/all.min.css">

  <style>
    @keyframes pulseGlow {
      0% { box-shadow: 0 0 30px rgba(255,0,120,0.6); }
      50% { box-shadow: 0 0 50px rgba(100,100,255,0.9); }
      100% { box-shadow: 0 0 30px rgba(255,0,120,0.6); }
    }
  </style>



</head>

<body class="min-h-screen flex items-center justify-center p-6 relative bg-black"

style="background-image: url(/app/assets/images/ad.jpg);" 
>

  <!-- Tech Background Image -->
  <div class="absolute inset-0 bg-cover bg-center opacity-60"
  >
  </div>

  <!-- Overlay Grid Effect -->
  <div class="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(0,0,0,0)_0%,rgba(0,0,0,0.85)_80%)]"></div>
  <div class="absolute inset-0 bg-[linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:40px]"></div>
  <div class="absolute inset-0 bg-[linear-gradient(0deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:40px]"></div>

  <!-- Circular Login Card -->
  <div class="relative w-100 h-100 md:w-[40rem] md:h-[40rem] rounded-full bg-white/10 backdrop-blur-3xl border border-white/20 shadow-2xl flex flex-col items-center justify-center overflow-hidden animate-[pulseGlow_4s_infinite]">

    <!-- Neon glows -->
    <div class="absolute -top-32 left-1/2 -translate-x-1/2 w-96 h-96 bg-pink-500/40 blur-[150px] rounded-full"></div>
    <div class="absolute -bottom-32 right-0 w-96 h-96 bg-indigo-500/40 blur-[150px] rounded-full"></div>

    <!-- Logo -->
      <img src="/app/assets/images/newad.png"class="w-32 mx-auto drop-shadow-[0_0_25px_rgba(255,255,255,0.8)]">

    <!-- Form -->
    <form id="loginForm" class="z-10 w-80 space-y-6 text-white">
      <div id="errorMsg" class="hidden text-red-400 text-center text-sm"></div>

      <!-- Email -->
      <div>
        <label class="text-white/80 text-sm">Email</label>
        <div class="mt-2 relative">
          <i class="fa-solid fa-envelope text-white/50 absolute left-4 top-3.5"></i>
          <input type="email" name="email" required placeholder="you@example.com"
            class="w-full pl-12 pr-4 py-3 bg-white/5 placeholder-white/40 rounded-xl border border-white/20 focus:ring-2 focus:ring-pink-400 focus:outline-none">
        </div>
      </div>

      <!-- Password -->
      <div>
        <label class="text-white/80 text-sm">Password</label>
        <div class="mt-2 relative">
          <i class="fa-solid fa-lock text-white/50 absolute left-4 top-3.5"></i>
          <input type="password" name="password" required placeholder="••••••••"
            class="w-full pl-12 pr-4 py-3 bg-white/5 placeholder-white/40 rounded-xl border border-white/20 focus:ring-2 focus:ring-indigo-400 focus:outline-none">
        </div>
      </div>

      <!-- Remember -->
      <label class="inline-flex items-center text-white/70 text-sm">
        <input type="checkbox" name="remember" class="mr-2">
        Remember Me
      </label>

      <!-- Login Button -->
      <button type="submit"
        class="w-full bg-gradient-to-r from-pink-500 to-indigo-600 hover:from-pink-600 hover:to-indigo-700 text-white py-3 rounded-xl font-semibold shadow-xl transition-transform hover:scale-105">
        Login
      </button>

      <!-- Divider -->
      <div class="flex items-center gap-3 mt-6">
        <div class="h-px flex-1 bg-white/20"></div>
        <span class="text-white/40 text-sm">OR</span>
        <div class="h-px flex-1 bg-white/20"></div>
      </div>

      <!-- Social Buttons -->
      <div class="grid grid-cols-2 gap-4">
        <button type="button" class="flex items-center justify-center gap-2 bg-white/5 text-white py-3 rounded-xl border border-white/20 hover:bg-white/10 transition">
          <i class="fa-brands fa-google"></i> Google
        </button>
        <button type="button" class="flex items-center justify-center gap-2 bg-white/5 text-white py-3 rounded-xl border border-white/20 hover:bg-white/10 transition">
          <i class="fa-brands fa-apple"></i> Apple
        </button>
      </div>

      <p class="text-center text-white/60 text-sm mt-6">
        Don't have an account? <a href="#" class="text-pink-400 hover:underline">Sign up</a>
      </p>
    </form>
  </div>

  <script>
    const form = document.getElementById('loginForm');
    const errorMsg = document.getElementById('errorMsg');

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      errorMsg.classList.add('hidden');
      const formData = new FormData(form);

      const payload = {
        email: formData.get('email'),
        password: formData.get('password'),
        remember: formData.get('remember') ? true : false,
        csrf_token: '<?= csrf_token() ?>'
      };

      try {
        const res = await fetch('login_backend.php', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (data.status === 1) {
          window.location.href = 'dashboard.html';
        } else {
          errorMsg.textContent = data.message;
          errorMsg.classList.remove('hidden');
        }
      } catch {
        errorMsg.textContent = 'Network error. Try again.';
        errorMsg.classList.remove('hidden');
      }
    });
  </script>

</body>
</html>
