<?php
/**
 * ADMIN SERVICE - Ads Management
 * Manage all ads on the platform
 */

if (session_status() === PHP_SESSION_NONE) session_start();
if (!defined('BASE_PATH')) define('BASE_PATH', dirname(dirname(dirname(__DIR__))));

$adminUsername = $_SESSION['admin_username'] ?? 'Admin';

// Load ads from database
require_once BASE_PATH . '/services/shared/database/Database.php';
$db = Database::getInstance();
$ads = $db->query("SELECT * FROM ads ORDER BY created_at DESC LIMIT 100")->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ads Management - AdSphere Admin</title>
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
        <div class="flex justify-between items-center mb-8">
            <div>
                <h1 class="text-3xl font-bold">Ads Management</h1>
                <p class="text-gray-400">Manage all ads across the platform</p>
            </div>
            <div class="flex gap-4">
                <select class="bg-white/10 border border-white/20 rounded-lg px-4 py-2">
                    <option value="">All Status</option>
                    <option value="active">Active</option>
                    <option value="review">Under Review</option>
                    <option value="blocked">Blocked</option>
                </select>
                <button onclick="runScanner()" class="bg-purple-600 hover:bg-purple-700 px-6 py-2 rounded-lg transition">
                    <i class="fas fa-search mr-2"></i>Run Scanner
                </button>
            </div>
        </div>

        <div class="glass rounded-xl p-6">
            <table class="w-full">
                <thead>
                    <tr class="text-left text-gray-400 border-b border-white/10">
                        <th class="pb-4">Ad</th>
                        <th class="pb-4">Company</th>
                        <th class="pb-4">Category</th>
                        <th class="pb-4">Status</th>
                        <th class="pb-4">Views</th>
                        <th class="pb-4">Created</th>
                        <th class="pb-4">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($ads)): ?>
                        <tr><td colspan="7" class="py-8 text-center text-gray-500">No ads found</td></tr>
                    <?php else: ?>
                        <?php foreach ($ads as $ad): ?>
                        <tr class="border-b border-white/5 hover:bg-white/5">
                            <td class="py-4">
                                <div class="font-semibold"><?= htmlspecialchars(substr($ad['title'] ?? 'Untitled', 0, 40)) ?></div>
                                <div class="text-sm text-gray-500"><?= htmlspecialchars($ad['id']) ?></div>
                            </td>
                            <td class="py-4 text-gray-400"><?= htmlspecialchars($ad['company_id'] ?? 'Unknown') ?></td>
                            <td class="py-4 text-gray-400"><?= htmlspecialchars($ad['category'] ?? 'Uncategorized') ?></td>
                            <td class="py-4">
                                <?php
                                $status = $ad['status'] ?? 'active';
                                $statusClass = match($status) {
                                    'active' => 'bg-green-500/20 text-green-400',
                                    'review' => 'bg-yellow-500/20 text-yellow-400',
                                    'blocked' => 'bg-red-500/20 text-red-400',
                                    default => 'bg-gray-500/20 text-gray-400'
                                };
                                ?>
                                <span class="px-3 py-1 rounded-full text-xs <?= $statusClass ?>"><?= ucfirst($status) ?></span>
                            </td>
                            <td class="py-4"><?= number_format($ad['views'] ?? 0) ?></td>
                            <td class="py-4 text-gray-400"><?= date('M j, Y', strtotime($ad['created_at'] ?? 'now')) ?></td>
                            <td class="py-4">
                                <button class="text-blue-400 hover:text-blue-300 mr-2" title="View"><i class="fas fa-eye"></i></button>
                                <button class="text-green-400 hover:text-green-300 mr-2" title="Approve"><i class="fas fa-check"></i></button>
                                <button class="text-red-400 hover:text-red-300" title="Block"><i class="fas fa-ban"></i></button>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>

    <script>
    async function runScanner() {
        if (confirm('Run ad scanner now?')) {
            const response = await fetch('/api/scanner/run', { method: 'POST' });
            const result = await response.json();
            alert(result.message || 'Scanner started');
            location.reload();
        }
    }
    </script>
</body>
</html>

