<?php
/**
 * ADMIN SERVICE - Analytics
 */
if (session_status() === PHP_SESSION_NONE) session_start();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analytics - AdSphere Admin</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); min-height: 100vh; }
        .glass { background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }
    </style>
</head>
<body class="text-white">
    <?php include __DIR__ . '/../assets/sidebar.php'; ?>

    <div class="ml-64 p-8">
        <h1 class="text-3xl font-bold mb-2">Platform Analytics</h1>
        <p class="text-gray-400 mb-8">Overview of platform performance</p>

        <div class="grid grid-cols-4 gap-6 mb-8">
            <div class="glass rounded-xl p-6 text-center">
                <div class="text-3xl font-bold text-blue-400" id="totalViews">0</div>
                <div class="text-gray-400 text-sm">Total Views</div>
            </div>
            <div class="glass rounded-xl p-6 text-center">
                <div class="text-3xl font-bold text-green-400" id="totalContacts">0</div>
                <div class="text-gray-400 text-sm">Total Contacts</div>
            </div>
            <div class="glass rounded-xl p-6 text-center">
                <div class="text-3xl font-bold text-purple-400" id="totalFavorites">0</div>
                <div class="text-gray-400 text-sm">Total Favorites</div>
            </div>
            <div class="glass rounded-xl p-6 text-center">
                <div class="text-3xl font-bold text-yellow-400" id="totalLikes">0</div>
                <div class="text-gray-400 text-sm">Total Likes</div>
            </div>
        </div>

        <div class="grid grid-cols-2 gap-6">
            <div class="glass rounded-xl p-6">
                <h2 class="text-xl font-semibold mb-4">Views Over Time</h2>
                <canvas id="viewsChart"></canvas>
            </div>
            <div class="glass rounded-xl p-6">
                <h2 class="text-xl font-semibold mb-4">Engagement by Category</h2>
                <canvas id="categoryChart"></canvas>
            </div>
        </div>
    </div>

    <script>
    // Initialize charts
    const viewsCtx = document.getElementById('viewsChart').getContext('2d');
    new Chart(viewsCtx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Views',
                data: [120, 190, 300, 250, 400, 350, 420],
                borderColor: '#3b82f6',
                tension: 0.4,
                fill: true,
                backgroundColor: 'rgba(59, 130, 246, 0.1)'
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.1)' } }, x: { grid: { display: false } } }
        }
    });

    const categoryCtx = document.getElementById('categoryChart').getContext('2d');
    new Chart(categoryCtx, {
        type: 'doughnut',
        data: {
            labels: ['Electronics', 'Vehicles', 'Property', 'Fashion', 'Other'],
            datasets: [{
                data: [30, 25, 20, 15, 10],
                backgroundColor: ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#6b7280']
            }]
        },
        options: { responsive: true }
    });

    // Load real data
    fetch('/api/analytics').then(r => r.json()).then(data => {
        if (data.success) {
            document.getElementById('totalViews').textContent = data.data.views?.toLocaleString() || 0;
            document.getElementById('totalContacts').textContent = data.data.contacts?.toLocaleString() || 0;
            document.getElementById('totalFavorites').textContent = data.data.favorites?.toLocaleString() || 0;
            document.getElementById('totalLikes').textContent = data.data.likes?.toLocaleString() || 0;
        }
    }).catch(console.error);
    </script>
</body>
</html>

