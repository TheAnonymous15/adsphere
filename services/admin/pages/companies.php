<?php
/**
 * ADMIN SERVICE - Companies Management
 * Manage all companies on the platform
 */

if (session_status() === PHP_SESSION_NONE) session_start();
if (!defined('BASE_PATH')) define('BASE_PATH', dirname(dirname(dirname(__DIR__))));

$adminUsername = $_SESSION['admin_username'] ?? 'Admin';

// Load companies from database
require_once BASE_PATH . '/services/shared/database/Database.php';
$db = Database::getInstance();
$companies = $db->query("SELECT * FROM companies ORDER BY created_at DESC")->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Companies Management - AdSphere Admin</title>
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
                <h1 class="text-3xl font-bold">Companies Management</h1>
                <p class="text-gray-400">Manage all registered companies</p>
            </div>
            <a href="/companies/new" class="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg transition">
                <i class="fas fa-plus mr-2"></i>Add Company
            </a>
        </div>

        <div class="glass rounded-xl p-6">
            <table class="w-full">
                <thead>
                    <tr class="text-left text-gray-400 border-b border-white/10">
                        <th class="pb-4">Company</th>
                        <th class="pb-4">Email</th>
                        <th class="pb-4">Status</th>
                        <th class="pb-4">Ads</th>
                        <th class="pb-4">Created</th>
                        <th class="pb-4">Actions</th>
                    </tr>
                </thead>
                <tbody id="companiesTable">
                    <?php if (empty($companies)): ?>
                        <tr><td colspan="6" class="py-8 text-center text-gray-500">No companies found</td></tr>
                    <?php else: ?>
                        <?php foreach ($companies as $company): ?>
                        <tr class="border-b border-white/5 hover:bg-white/5">
                            <td class="py-4">
                                <div class="font-semibold"><?= htmlspecialchars($company['name'] ?? $company['slug']) ?></div>
                                <div class="text-sm text-gray-500"><?= htmlspecialchars($company['slug']) ?></div>
                            </td>
                            <td class="py-4 text-gray-400"><?= htmlspecialchars($company['email'] ?? 'N/A') ?></td>
                            <td class="py-4">
                                <span class="px-3 py-1 rounded-full text-xs <?= ($company['status'] ?? 'active') === 'active' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400' ?>">
                                    <?= ucfirst($company['status'] ?? 'active') ?>
                                </span>
                            </td>
                            <td class="py-4"><?= $company['ad_count'] ?? 0 ?></td>
                            <td class="py-4 text-gray-400"><?= date('M j, Y', strtotime($company['created_at'] ?? 'now')) ?></td>
                            <td class="py-4">
                                <button class="text-blue-400 hover:text-blue-300 mr-3" title="Edit"><i class="fas fa-edit"></i></button>
                                <button class="text-yellow-400 hover:text-yellow-300 mr-3" title="Suspend"><i class="fas fa-ban"></i></button>
                                <button class="text-red-400 hover:text-red-300" title="Delete"><i class="fas fa-trash"></i></button>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>

