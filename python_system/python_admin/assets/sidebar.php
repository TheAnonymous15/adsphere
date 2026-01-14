<?php
/**
 * Admin Sidebar Component
 */
$currentPage = basename(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
if (empty($currentPage) || $currentPage === '/') $currentPage = 'dashboard';

function isActive($page) {
    global $currentPage;
    return strpos($currentPage, $page) !== false ? 'bg-white/10 border-l-4 border-blue-500' : '';
}
?>
<aside class="fixed left-0 top-0 w-64 h-screen bg-black/40 backdrop-blur-xl border-r border-white/10 z-50">
    <div class="p-6 border-b border-white/10">
        <a href="/dashboard" class="flex items-center gap-3">
            <div class="w-10 h-10 bg-gradient-to-br from-red-500 to-pink-600 rounded-lg flex items-center justify-center">
                <i class="fas fa-shield-alt text-white"></i>
            </div>
            <div>
                <h1 class="text-xl font-bold text-white">AdSphere</h1>
                <p class="text-xs text-gray-500">Admin Panel</p>
            </div>
        </a>
    </div>

    <nav class="p-4 space-y-1">
        <p class="text-xs text-gray-500 uppercase tracking-wider mb-3 px-3">Overview</p>

        <a href="/dashboard" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActive('dashboard') ?>">
            <i class="fas fa-tachometer-alt w-5"></i>
            <span>Dashboard</span>
        </a>

        <a href="/analytics" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActive('analytics') ?>">
            <i class="fas fa-chart-line w-5"></i>
            <span>Analytics</span>
        </a>

        <p class="text-xs text-gray-500 uppercase tracking-wider mt-6 mb-3 px-3">Management</p>

        <a href="/companies" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActive('companies') ?>">
            <i class="fas fa-building w-5"></i>
            <span>Companies</span>
        </a>

        <a href="/ads" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActive('ads') ?>">
            <i class="fas fa-ad w-5"></i>
            <span>All Ads</span>
        </a>

        <a href="/categories" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActive('categories') ?>">
            <i class="fas fa-tags w-5"></i>
            <span>Categories</span>
        </a>

        <p class="text-xs text-gray-500 uppercase tracking-wider mt-6 mb-3 px-3">Moderation</p>

        <a href="/moderation" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActive('moderation') ?>">
            <i class="fas fa-shield-alt w-5"></i>
            <span>Content Moderation</span>
        </a>

        <a href="/flagged" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActive('flagged') ?>">
            <i class="fas fa-flag w-5"></i>
            <span>Flagged Content</span>
        </a>

        <a href="/scanner" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActive('scanner') ?>">
            <i class="fas fa-radar w-5"></i>
            <span>Ad Scanner</span>
        </a>

        <p class="text-xs text-gray-500 uppercase tracking-wider mt-6 mb-3 px-3">System</p>

        <a href="/users" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActive('users') ?>">
            <i class="fas fa-users-cog w-5"></i>
            <span>Admin Users</span>
        </a>

        <a href="/settings" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActive('settings') ?>">
            <i class="fas fa-cog w-5"></i>
            <span>Settings</span>
        </a>

        <a href="/logs" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActive('logs') ?>">
            <i class="fas fa-file-alt w-5"></i>
            <span>System Logs</span>
        </a>

        <p class="text-xs text-gray-500 uppercase tracking-wider mt-6 mb-3 px-3">External</p>

        <a href="http://localhost:3000" target="_blank" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition">
            <i class="fas fa-chart-area w-5"></i>
            <span>Grafana</span>
            <i class="fas fa-external-link-alt text-xs ml-auto"></i>
        </a>

        <a href="http://localhost:8004/docs" target="_blank" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition">
            <i class="fas fa-book w-5"></i>
            <span>API Docs</span>
            <i class="fas fa-external-link-alt text-xs ml-auto"></i>
        </a>
    </nav>

    <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-white/10">
        <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
                <span class="text-white font-bold"><?= strtoupper(substr($_SESSION['admin_username'] ?? 'A', 0, 1)) ?></span>
            </div>
            <div>
                <p class="text-sm font-medium text-white"><?= htmlspecialchars($_SESSION['admin_username'] ?? 'Admin') ?></p>
                <p class="text-xs text-gray-500"><?= ucfirst($_SESSION['admin_role'] ?? 'admin') ?></p>
            </div>
        </div>
        <a href="/logout" class="flex items-center justify-center gap-2 w-full py-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition">
            <i class="fas fa-sign-out-alt"></i>
            <span>Logout</span>
        </a>
    </div>
</aside>

