<?php
/**
 * 500 Internal Server Error
 */
http_response_code(500);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>500 Server Error - AdSphere Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
</head>
<body class="bg-gradient-to-br from-slate-900 to-orange-900 min-h-screen flex items-center justify-center">
    <div class="text-center text-white">
        <h1 class="text-9xl font-bold opacity-20">500</h1>
        <h2 class="text-3xl font-bold mb-4 -mt-10">Server Error</h2>
        <p class="text-white/70 mb-8">Something went wrong. Please try again later.</p>
        <a href="/dashboard" class="bg-orange-500 text-white px-8 py-3 rounded-full font-semibold hover:bg-orange-600 transition">
            Go to Dashboard
        </a>
    </div>
</body>
</html>

