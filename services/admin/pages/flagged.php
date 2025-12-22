<?php
/**
 * ADMIN SERVICE - Flagged Content
 */
if (session_status() === PHP_SESSION_NONE) session_start();
if (!defined('BASE_PATH')) define('BASE_PATH', dirname(dirname(dirname(__DIR__))));

// Load flagged ads
$flaggedFile = BASE_PATH . '/services/data/flagged_ads.json';
$flaggedAds = file_exists($flaggedFile) ? json_decode(file_get_contents($flaggedFile), true) : [];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flagged Content - AdSphere Admin</title>
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
        <h1 class="text-3xl font-bold mb-2">Flagged Content</h1>
        <p class="text-gray-400 mb-8">Content flagged by AI moderation</p>

        <div class="glass rounded-xl p-6">
            <?php if (empty($flaggedAds)): ?>
                <div class="text-center py-12">
                    <i class="fas fa-check-circle text-6xl text-green-500 mb-4"></i>
                    <h3 class="text-xl font-semibold mb-2">All Clear!</h3>
                    <p class="text-gray-400">No flagged content at this time</p>
                </div>
            <?php else: ?>
                <div class="space-y-4">
                    <?php foreach ($flaggedAds as $ad): ?>
                    <div class="glass p-4 rounded-lg flex justify-between items-center">
                        <div>
                            <h3 class="font-semibold"><?= htmlspecialchars($ad['title'] ?? 'Untitled') ?></h3>
                            <p class="text-sm text-gray-400">Reason: <?= htmlspecialchars($ad['reason'] ?? 'Unknown') ?></p>
                            <p class="text-xs text-gray-500">Flagged: <?= date('M j, Y H:i', $ad['flagged_at'] ?? time()) ?></p>
                        </div>
                        <div class="flex gap-2">
                            <button class="bg-green-600 hover:bg-green-700 px-4 py-2 rounded text-sm">Approve</button>
                            <button class="bg-red-600 hover:bg-red-700 px-4 py-2 rounded text-sm">Block</button>
                        </div>
                    </div>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>
        </div>
    </div>
</body>
</html>

