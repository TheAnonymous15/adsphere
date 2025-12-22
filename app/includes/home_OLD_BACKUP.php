


<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AdSphere | Power</title>
    <link rel="icon" type="image/png" href="icon.png">
  <script src="https://cdn.tailwindcss.com"></script>
<link rel="stylesheet" href="/app/assets/css/all.min.css">
    <style>
        /* Shared classes */
        .nav-link { @apply text-white/90 hover:text-white font-medium transition-all hover:-translate-y-0.5; }
        .mobile-link { @apply block px-6 py-3 text-gray-800/90 hover:bg-white/30 hover:text-indigo-600 transition; }
        .animate-spin-slow { animation: spin-slow 60s linear infinite; }
        .animate-spin-slow-reverse { animation: spin-slow-reverse 60s linear infinite; }
        @keyframes spin-slow { from {transform: rotate(0deg);} to {transform: rotate(360deg);} }
        @keyframes spin-slow-reverse { from {transform: rotate(360deg);} to {transform: rotate(0deg);} }
    </style>
</head>
<body class="bg-gray-50 text-gray-900 font-sans leading-relaxed scroll-smooth">


<?php

// $pages = ["ad_page"];
$pages = ["header", "hero", "ad_page", "footer"];

foreach ($pages as $page) {include $page . ".php";}?>

<style>
body {
  background: linear-gradient(135deg, #0b927e, #0b343b, #119585);
  background-size: 400% 400%;
  animation: gradientShift 20s ease infinite;
}

@keyframes gradientShift {
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
}
</style>
</body>
</html>