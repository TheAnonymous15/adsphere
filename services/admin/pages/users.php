<?php
/**
 * ADMIN SERVICE - Admin Users Management
 */
if (session_status() === PHP_SESSION_NONE) session_start();

$adminsFile = __DIR__ . '/../config/admins.json';
$admins = file_exists($adminsFile) ? json_decode(file_get_contents($adminsFile), true) : [];
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Users - AdSphere Admin</title>
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
                <h1 class="text-3xl font-bold">Admin Users</h1>
                <p class="text-gray-400">Manage administrator accounts</p>
            </div>
            <button class="bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg">
                <i class="fas fa-plus mr-2"></i>Add Admin
            </button>
        </div>

        <div class="glass rounded-xl p-6">
            <table class="w-full">
                <thead>
                    <tr class="text-left text-gray-400 border-b border-white/10">
                        <th class="pb-4">Username</th>
                        <th class="pb-4">Email</th>
                        <th class="pb-4">Role</th>
                        <th class="pb-4">2FA</th>
                        <th class="pb-4">Created</th>
                        <th class="pb-4">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($admins as $username => $admin): ?>
                    <tr class="border-b border-white/5">
                        <td class="py-4 font-semibold"><?= htmlspecialchars($admin['username'] ?? $username) ?></td>
                        <td class="py-4 text-gray-400"><?= htmlspecialchars($admin['email'] ?? 'N/A') ?></td>
                        <td class="py-4">
                            <span class="px-3 py-1 rounded-full text-xs <?= ($admin['role'] ?? '') === 'super_admin' ? 'bg-purple-500/20 text-purple-400' : 'bg-blue-500/20 text-blue-400' ?>">
                                <?= ucfirst(str_replace('_', ' ', $admin['role'] ?? 'admin')) ?>
                            </span>
                        </td>
                        <td class="py-4">
                            <?php if ($admin['2fa_enabled'] ?? false): ?>
                                <span class="text-green-400"><i class="fas fa-check-circle"></i></span>
                            <?php else: ?>
                                <span class="text-gray-500"><i class="fas fa-times-circle"></i></span>
                            <?php endif; ?>
                        </td>
                        <td class="py-4 text-gray-400"><?= isset($admin['created_at']) ? date('M j, Y', $admin['created_at']) : 'N/A' ?></td>
                        <td class="py-4">
                            <button class="text-blue-400 hover:text-blue-300 mr-3"><i class="fas fa-edit"></i></button>
                            <button class="text-red-400 hover:text-red-300"><i class="fas fa-trash"></i></button>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>

