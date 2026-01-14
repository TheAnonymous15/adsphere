<footer class="w-full bg-black/20 backdrop-blur-md shadow-inner text-white mt-20 py-10">
  <div class="max-w-sm mx-auto flex flex-col items-center text-center gap-6 px-4">

    <h2 class="text-lg font-semibold bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 via-pink-400 to-purple-400">
      The future of digital advertising
    </h2>

    <div class="border-t border-white/20 w-full pt-4 text-xs text-white/70">
      &copy; <span id="year"></span> AdSphere. All rights reserved.
    </div>

  </div>

  <script>
    document.getElementById("year").textContent = new Date().getFullYear();
  </script>
</footer>