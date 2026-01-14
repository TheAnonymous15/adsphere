<?php
/**
 * 403 Forbidden
 */
http_response_code(403);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>403 Forbidden - AdSphere Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
</head>
<body class="bg-gradient-to-br from-slate-900 to-red-900 min-h-screen flex items-center justify-center">
    <div class="text-center text-white">
        <h1 class="text-9xl font-bold opacity-20">403</h1>
        <h2 class="text-3xl font-bold mb-4 -mt-10">Access Forbidden</h2>
        <p class="text-white/70 mb-8">You don't have permission to access this resource.</p>
        <a href="/dashboard" class="bg-red-500 text-white px-8 py-3 rounded-full font-semibold hover:bg-red-600 transition">
            Go to Dashboard
        </a>
    </div>
</body>
</html>

