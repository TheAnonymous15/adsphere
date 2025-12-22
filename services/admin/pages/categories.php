<?php
/**
 * ADMIN SERVICE - Categories Management
 */
if (session_status() === PHP_SESSION_NONE) session_start();
if (!defined('BASE_PATH')) define('BASE_PATH', dirname(dirname(dirname(__DIR__))));

require_once BASE_PATH . '/services/shared/database/Database.php';
$db = Database::getInstance();
$categories = $db->query("SELECT * FROM categories ORDER BY name ASC")->fetchAll(PDO::FETCH_ASSOC);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Categories - AdSphere Admin</title>
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
                <h1 class="text-3xl font-bold">Categories</h1>
                <p class="text-gray-400">Manage ad categories</p>
            </div>
            <button onclick="showAddModal()" class="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg">
                <i class="fas fa-plus mr-2"></i>Add Category
            </button>
        </div>

        <div class="grid grid-cols-4 gap-4">
            <?php foreach ($categories as $cat): ?>
            <div class="glass rounded-xl p-4">
                <div class="flex justify-between items-start mb-2">
                    <h3 class="font-semibold capitalize"><?= htmlspecialchars($cat['name']) ?></h3>
                    <div class="flex gap-2">
                        <button class="text-blue-400 hover:text-blue-300"><i class="fas fa-edit"></i></button>
                        <button class="text-red-400 hover:text-red-300"><i class="fas fa-trash"></i></button>
                    </div>
                </div>
                <p class="text-sm text-gray-400"><?= htmlspecialchars($cat['description'] ?? 'No description') ?></p>
                <p class="text-xs text-gray-500 mt-2"><?= $cat['ad_count'] ?? 0 ?> ads</p>
            </div>
            <?php endforeach; ?>

            <?php if (empty($categories)): ?>
            <div class="col-span-4 text-center py-12 text-gray-500">
                <i class="fas fa-tags text-4xl mb-4"></i>
                <p>No categories found</p>
            </div>
            <?php endif; ?>
        </div>
    </div>

    <script>
    function showAddModal() {
        const name = prompt('Enter category name:');
        if (name) {
            alert('Category creation to be implemented');
        }
    }
    </script>
</body>
</html>

