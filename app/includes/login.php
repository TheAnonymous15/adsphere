<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Next Level Login</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css" />
</head>
<body class="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 flex items-center justify-center p-4"
      style="background-image: url('/app/assets/images/ad.jpg');">


  <div class="relative w-full max-w-md backdrop-blur-2xl bg-white/10 border border-white/20 rounded-3xl shadow-2xl p-8 overflow-hidden">

    <!-- Glow Effects -->
    <div class="absolute -top-10 -right-10 w-40 h-40 bg-pink-500/30 blur-3xl rounded-full"></div>
    <div class="absolute -bottom-10 -left-10 w-40 h-40 bg-indigo-500/30 blur-3xl rounded-full"></div>

    <!-- Logo / Title -->
    <div class="text-center mb-8">
      <img src="/app/assets/images/icon.png" 
           class="w-30 h-25 drop-shadow-[0_0_15px_rgba(255,255,255,0.8)]">
    </div>

    <!-- Login Form -->
    <form id="loginForm" class="space-y-6">
      <div id="errorMsg" class="hidden text-red-400 text-center"></div>

      <div>
        <label class="text-white text-sm font-medium">Email</label>
        <div class="mt-2 relative">
          <i class="fa-solid fa-envelope text-white/50 absolute left-3 top-3"></i>
          <input type="email" name="email" required placeholder="you@example.com"
            class="w-full pl-10 pr-4 py-3 bg-black/20 text-white placeholder-white/40 rounded-xl border border-white/20 focus:ring-2 focus:ring-pink-400 focus:outline-none">
        </div>
      </div>

      <div>
        <label class="text-white text-sm font-medium">Password</label>
        <div class="mt-2 relative">
          <i class="fa-solid fa-lock text-white/50 absolute left-3 top-3"></i>
          <input type="password" name="password" required placeholder="••••••••"
            class="w-full pl-10 pr-4 py-3 bg-black/20 text-white placeholder-white/40 rounded-xl border border-white/20 focus:ring-2 focus:ring-indigo-400 focus:outline-none">
        </div>
      </div>

      <div class="flex items-center">
        <label class="inline-flex items-center text-white/80 text-sm">
          <input type="checkbox" name="remember" class="mr-2">
          Remember Me
        </label>
      </div>

      <!-- Login Button -->
      <button type="submit"
        class="w-full bg-gradient-to-r from-pink-500 to-indigo-600 hover:from-pink-600 hover:to-indigo-700 text-white py-3 rounded-xl font-semibold shadow-lg transition-transform hover:scale-105">
        Login
      </button>

      <!-- Divider -->
      <div class="flex items-center gap-3 mt-6">
        <div class="h-px flex-1 bg-white/20"></div>
        <span class="text-white/40 text-sm">OR</span>
        <div class="h-px flex-1 bg-white/20"></div>
      </div>

      <!-- Social Login -->
      <div class="grid grid-cols-2 gap-4 mt-4">
        <button type="button" class="flex items-center justify-center gap-2 bg-white/10 text-white py-3 rounded-xl border border-white/20 hover:bg-white/20 transition">
          <i class="fa-brands fa-google"></i> Google
        </button>
        <button type="button" class="flex items-center justify-center gap-2 bg-white/10 text-white py-3 rounded-xl border border-white/20 hover:bg-white/20 transition">
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
        csrf_token: '<?= csrf_token() ?>' // if your backend generates it dynamically
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
      } catch (err) {
        errorMsg.textContent = 'Network error. Try again.';
        errorMsg.classList.remove('hidden');
      }
    });
  </script>

</body>
</html>
