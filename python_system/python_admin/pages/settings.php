<?php
/**
 * ADMIN SERVICE - Settings
 */
if (session_status() === PHP_SESSION_NONE) session_start();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Settings - AdSphere Admin</title>
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
        <h1 class="text-3xl font-bold mb-2">System Settings</h1>
        <p class="text-gray-400 mb-8">Configure platform settings</p>

        <div class="space-y-6">
            <div class="glass rounded-xl p-6">
                <h2 class="text-xl font-semibold mb-4">Security Settings</h2>
                <div class="space-y-4">
                    <div class="flex justify-between items-center">
                        <div>
                            <p class="font-medium">Require 2FA for Admins</p>
                            <p class="text-sm text-gray-400">Force all admins to use 2FA</p>
                        </div>
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" checked class="sr-only peer">
                            <div class="w-11 h-6 bg-gray-600 rounded-full peer peer-checked:bg-blue-600 after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"></div>
                        </label>
                    </div>
                    <div class="flex justify-between items-center">
                        <div>
                            <p class="font-medium">Session Timeout</p>
                            <p class="text-sm text-gray-400">Auto-logout after inactivity</p>
                        </div>
                        <select class="bg-white/10 border border-white/20 rounded px-4 py-2">
                            <option>30 minutes</option>
                            <option selected>1 hour</option>
                            <option>2 hours</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="glass rounded-xl p-6">
                <h2 class="text-xl font-semibold mb-4">Moderation Settings</h2>
                <div class="space-y-4">
                    <div class="flex justify-between items-center">
                        <div>
                            <p class="font-medium">Auto-Moderation</p>
                            <p class="text-sm text-gray-400">Automatically scan new ads</p>
                        </div>
                        <label class="relative inline-flex items-center cursor-pointer">
                            <input type="checkbox" checked class="sr-only peer">
                            <div class="w-11 h-6 bg-gray-600 rounded-full peer peer-checked:bg-blue-600 after:content-[''] after:absolute after:top-0.5 after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:after:translate-x-full"></div>
                        </label>
                    </div>
                    <div class="flex justify-between items-center">
                        <div>
                            <p class="font-medium">Moderation Strictness</p>
                            <p class="text-sm text-gray-400">How strict to flag content</p>
                        </div>
                        <select class="bg-white/10 border border-white/20 rounded px-4 py-2">
                            <option>Low</option>
                            <option selected>Medium</option>
                            <option>High</option>
                        </select>
                    </div>
                </div>
            </div>

            <div class="glass rounded-xl p-6">
                <h2 class="text-xl font-semibold mb-4">Service Status</h2>
                <div class="grid grid-cols-3 gap-4">
                    <div class="bg-green-500/10 border border-green-500/30 rounded-lg p-4 text-center">
                        <i class="fas fa-server text-green-400 text-2xl mb-2"></i>
                        <p class="text-sm">API Service</p>
                        <p class="text-green-400 text-xs">Online</p>
                    </div>
                    <div class="bg-green-500/10 border border-green-500/30 rounded-lg p-4 text-center">
                        <i class="fas fa-database text-green-400 text-2xl mb-2"></i>
                        <p class="text-sm">Database</p>
                        <p class="text-green-400 text-xs">Online</p>
                    </div>
                    <div class="bg-green-500/10 border border-green-500/30 rounded-lg p-4 text-center">
                        <i class="fas fa-robot text-green-400 text-2xl mb-2"></i>
                        <p class="text-sm">Moderation AI</p>
                        <p class="text-green-400 text-xs">Online</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>

