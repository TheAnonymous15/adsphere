<?php
/**
 * ADMIN SERVICE - Content Moderation
 */
if (session_status() === PHP_SESSION_NONE) session_start();

// Load path configuration
require_once dirname(dirname(__DIR__)) . '/python_shared/config/paths.php';
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Content Moderation - AdSphere Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        body { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
    </style>
</head>
<body class="text-white">
    <?php include __DIR__ . '/../assets/sidebar.php'; ?>

    <div class="ml-64 p-8">
        <h1 class="text-3xl font-bold mb-2">Content Moderation</h1>
        <p class="text-gray-400 mb-8">AI-powered content moderation dashboard</p>

        <div class="grid grid-cols-4 gap-6 mb-8">
            <div class="glass rounded-xl p-6 text-center">
                <div class="text-3xl font-bold text-green-400" id="approvedCount">0</div>
                <div class="text-gray-400 text-sm">Approved</div>
            </div>
            <div class="glass rounded-xl p-6 text-center">
                <div class="text-3xl font-bold text-yellow-400" id="reviewCount">0</div>
                <div class="text-gray-400 text-sm">Pending Review</div>
            </div>
            <div class="glass rounded-xl p-6 text-center">
                <div class="text-3xl font-bold text-red-400" id="blockedCount">0</div>
                <div class="text-gray-400 text-sm">Blocked</div>
            </div>
            <div class="glass rounded-xl p-6 text-center">
                <div class="text-3xl font-bold text-blue-400" id="scannerStatus">Idle</div>
                <div class="text-gray-400 text-sm">Scanner Status</div>
            </div>
        </div>

        <div class="glass rounded-xl p-6">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-semibold">Pending Review Queue</h2>
                <button onclick="runScanner()" class="bg-purple-600 hover:bg-purple-700 px-4 py-2 rounded-lg text-sm">
                    <i class="fas fa-play mr-2"></i>Run Scanner
                </button>
            </div>
            <div id="reviewQueue" class="space-y-4">
                <p class="text-center text-gray-500 py-8">Loading...</p>
            </div>
        </div>
    </div>

    <script>
    async function loadModerationData() {
        try {
            const response = await fetch('/api/moderation/flagged');
            const data = await response.json();
            // Update UI with data
            document.getElementById('reviewQueue').innerHTML = data.data?.length
                ? data.data.map(item => `<div class="glass p-4 rounded-lg">${item.title || item.id}</div>`).join('')
                : '<p class="text-center text-gray-500 py-8">No items pending review</p>';
        } catch (e) {
            console.error('Failed to load moderation data');
        }
    }

    async function runScanner() {
        document.getElementById('scannerStatus').textContent = 'Running...';
        try {
            await fetch('/api/scanner/run', { method: 'POST' });
            setTimeout(loadModerationData, 2000);
        } finally {
            document.getElementById('scannerStatus').textContent = 'Idle';
        }
    }

    document.addEventListener('DOMContentLoaded', loadModerationData);
    </script>
</body>
</html>

