<?php
/**
 * ADMIN SERVICE - System Logs
 */
if (session_status() === PHP_SESSION_NONE) session_start();

// Load path configuration
require_once dirname(dirname(__DIR__)) . '/python_shared/config/paths.php';

$logsDir = LOGS_PATH;
$logFiles = glob($logsDir . '/*.log');
rsort($logFiles);
$logFiles = array_slice($logFiles, 0, 10);

$selectedLog = $_GET['file'] ?? '';
$logContent = '';

if ($selectedLog && file_exists($logsDir . '/' . basename($selectedLog))) {
    $logContent = file_get_contents($logsDir . '/' . basename($selectedLog));
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Logs - AdSphere Admin</title>
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
        <h1 class="text-3xl font-bold mb-2">System Logs</h1>
        <p class="text-gray-400 mb-8">View system and security logs</p>

        <div class="grid grid-cols-4 gap-6">
            <div class="glass rounded-xl p-4">
                <h3 class="font-semibold mb-4">Log Files</h3>
                <div class="space-y-2">
                    <?php if (empty($logFiles)): ?>
                        <p class="text-gray-500 text-sm">No log files found</p>
                    <?php else: ?>
                        <?php foreach ($logFiles as $file): ?>
                            <?php $filename = basename($file); ?>
                            <a href="?file=<?= urlencode($filename) ?>"
                               class="block p-2 rounded hover:bg-white/10 transition <?= $selectedLog === $filename ? 'bg-white/10' : '' ?>">
                                <i class="fas fa-file-alt mr-2 text-gray-400"></i>
                                <span class="text-sm"><?= htmlspecialchars($filename) ?></span>
                            </a>
                        <?php endforeach; ?>
                    <?php endif; ?>
                </div>
            </div>

            <div class="col-span-3 glass rounded-xl p-4">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="font-semibold"><?= $selectedLog ? htmlspecialchars($selectedLog) : 'Select a log file' ?></h3>
                    <?php if ($selectedLog): ?>
                        <button onclick="location.reload()" class="text-blue-400 hover:text-blue-300">
                            <i class="fas fa-sync-alt mr-1"></i>Refresh
                        </button>
                    <?php endif; ?>
                </div>
                <div class="bg-black/50 rounded-lg p-4 h-[600px] overflow-auto font-mono text-xs">
                    <?php if ($logContent): ?>
                        <pre class="text-gray-300 whitespace-pre-wrap"><?= htmlspecialchars($logContent) ?></pre>
                    <?php else: ?>
                        <p class="text-gray-500">Select a log file to view its contents</p>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    </div>
</body>
</html>

