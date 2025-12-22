<?php
/**
 * Company Sidebar Component
 */
$currentPage = basename(parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH));
if (empty($currentPage) || $currentPage === '/') $currentPage = 'dashboard';

function isActivePage($page) {
    global $currentPage;
    return strpos($currentPage, $page) !== false ? 'bg-white/10 border-l-4 border-blue-500' : '';
}

$companyName = $_SESSION['company_name'] ?? 'Company';
$companySlug = $_SESSION['company'] ?? '';
?>
<aside class="fixed left-0 top-0 w-64 h-screen bg-black/40 backdrop-blur-xl border-r border-white/10 z-50">
    <div class="p-6 border-b border-white/10">
        <a href="/dashboard" class="flex items-center gap-3">
            <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-lg flex items-center justify-center">
                <i class="fas fa-building text-white"></i>
            </div>
            <div>
                <h1 class="text-lg font-bold text-white truncate"><?= htmlspecialchars($companyName) ?></h1>
                <p class="text-xs text-gray-500">Company Portal</p>
            </div>
        </a>
    </div>

    <nav class="p-4 space-y-1">
        <p class="text-xs text-gray-500 uppercase tracking-wider mb-3 px-3">Overview</p>

        <a href="/dashboard" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActivePage('dashboard') ?>">
            <i class="fas fa-tachometer-alt w-5"></i>
            <span>Dashboard</span>
        </a>

        <a href="/analytics" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActivePage('analytics') ?>">
            <i class="fas fa-chart-line w-5"></i>
            <span>Analytics</span>
        </a>

        <p class="text-xs text-gray-500 uppercase tracking-wider mt-6 mb-3 px-3">Ads</p>

        <a href="/ads" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActivePage('ads') || isActivePage('my-ads') ?>">
            <i class="fas fa-ad w-5"></i>
            <span>My Ads</span>
        </a>

        <a href="/upload" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActivePage('upload') || isActivePage('new-ad') ?>">
            <i class="fas fa-plus-circle w-5"></i>
            <span>Upload New Ad</span>
        </a>

        <p class="text-xs text-gray-500 uppercase tracking-wider mt-6 mb-3 px-3">Account</p>

        <a href="/profile" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActivePage('profile') ?>">
            <i class="fas fa-user w-5"></i>
            <span>Profile</span>
        </a>

        <a href="/notifications" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActivePage('notifications') ?>">
            <i class="fas fa-bell w-5"></i>
            <span>Notifications</span>
        </a>

        <a href="/settings" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition <?= isActivePage('settings') ?>">
            <i class="fas fa-cog w-5"></i>
            <span>Settings</span>
        </a>

        <p class="text-xs text-gray-500 uppercase tracking-wider mt-6 mb-3 px-3">External</p>

        <a href="http://localhost:8001" target="_blank" class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-gray-300 hover:bg-white/5 transition">
            <i class="fas fa-globe w-5"></i>
            <span>View Public Site</span>
            <i class="fas fa-external-link-alt text-xs ml-auto"></i>
        </a>
    </nav>

    <div class="absolute bottom-0 left-0 right-0 p-4 border-t border-white/10">
        <div class="flex items-center gap-3 mb-4">
            <div class="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-full flex items-center justify-center">
                <span class="text-white font-bold"><?= strtoupper(substr($companyName, 0, 1)) ?></span>
            </div>
            <div>
                <p class="text-sm font-medium text-white truncate"><?= htmlspecialchars($companyName) ?></p>
                <p class="text-xs text-gray-500">Business Account</p>
            </div>
        </div>
        <a href="/logout" class="flex items-center justify-center gap-2 w-full py-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition">
            <i class="fas fa-sign-out-alt"></i>
            <span>Logout</span>
        </a>
    </div>
</aside>

