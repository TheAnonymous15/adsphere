<?php
/**
 * ADMIN SERVICE - Ad Scanner
 */
if (session_status() === PHP_SESSION_NONE) session_start();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ad Scanner - AdSphere Admin</title>
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
        <h1 class="text-3xl font-bold mb-2">Ad Scanner</h1>
        <p class="text-gray-400 mb-8">Real-time content scanning system</p>

        <div class="grid grid-cols-3 gap-6 mb-8">
            <div class="glass rounded-xl p-6">
                <h3 class="text-lg font-semibold mb-4">Quick Scan</h3>
                <p class="text-gray-400 text-sm mb-4">Scan recent ads (last 24 hours)</p>
                <button onclick="runScan('incremental')" class="w-full bg-blue-600 hover:bg-blue-700 py-2 rounded-lg">
                    <i class="fas fa-bolt mr-2"></i>Run Quick Scan
                </button>
            </div>
            <div class="glass rounded-xl p-6">
                <h3 class="text-lg font-semibold mb-4">Full Scan</h3>
                <p class="text-gray-400 text-sm mb-4">Scan all ads in the database</p>
                <button onclick="runScan('full')" class="w-full bg-purple-600 hover:bg-purple-700 py-2 rounded-lg">
                    <i class="fas fa-search mr-2"></i>Run Full Scan
                </button>
            </div>
            <div class="glass rounded-xl p-6">
                <h3 class="text-lg font-semibold mb-4">Priority Scan</h3>
                <p class="text-gray-400 text-sm mb-4">Scan flagged & high-risk ads</p>
                <button onclick="runScan('priority')" class="w-full bg-red-600 hover:bg-red-700 py-2 rounded-lg">
                    <i class="fas fa-exclamation-triangle mr-2"></i>Run Priority Scan
                </button>
            </div>
        </div>

        <div class="glass rounded-xl p-6">
            <h2 class="text-xl font-semibold mb-4">Scanner Output</h2>
            <div id="scannerOutput" class="bg-black/50 rounded-lg p-4 h-96 overflow-y-auto font-mono text-sm">
                <p class="text-gray-500">Scanner output will appear here...</p>
            </div>
        </div>
    </div>

    <script>
    async function runScan(mode) {
        const output = document.getElementById('scannerOutput');
        output.innerHTML = `<p class="text-blue-400">[${new Date().toLocaleTimeString()}] Starting ${mode} scan...</p>`;

        try {
            const response = await fetch('/api/scanner/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode })
            });
            const result = await response.json();

            output.innerHTML += `<p class="text-green-400">[${new Date().toLocaleTimeString()}] ${result.message || 'Scan completed'}</p>`;
            if (result.data) {
                output.innerHTML += `<p class="text-gray-400">Scanned: ${result.data.scanned || 0}</p>`;
                output.innerHTML += `<p class="text-yellow-400">Flagged: ${result.data.flagged || 0}</p>`;
            }
        } catch (e) {
            output.innerHTML += `<p class="text-red-400">[${new Date().toLocaleTimeString()}] Error: ${e.message}</p>`;
        }
    }
    </script>
</body>
</html>

