<?php
/********************************************
 * Admin Users API
 * Get all users for admin dashboard
 ********************************************/
session_start();
header("Content-Type: application/json");

// Check if user is logged in (TODO: Add super admin check)
if (!isset($_SESSION['company'])) {
    http_response_code(401);
    echo json_encode(['success' => false, 'message' => 'Unauthorized']);
    exit;
}

// TODO: Connect to actual user database
// For now, scan registered companies as "users"

$metadataDir = __DIR__ . "/../../companies/metadata/";
$users = [];

if (is_dir($metadataDir)) {
    $files = scandir($metadataDir);

    foreach ($files as $file) {
        if ($file === '.' || $file === '..') continue;
        if (pathinfo($file, PATHINFO_EXTENSION) !== 'json') continue;

        $metaFile = $metadataDir . $file;
        $metadata = json_decode(file_get_contents($metaFile), true);

        if (!$metadata) continue;

        $companySlug = pathinfo($file, PATHINFO_FILENAME);

        // Extract user info from company metadata
        $users[] = [
            'id' => $companySlug,
            'name' => $metadata['company_name'] ?? ucfirst($companySlug),
            'email' => $metadata['contact_email'] ?? $companySlug . '@example.com',
            'role' => 'Company', // Can be enhanced with actual role system
            'status' => $metadata['status'] ?? 'active',
            'created_at' => $metadata['created_at'] ?? time(),
            'lastActive' => calculateLastActive($companySlug)
        ];
    }
}

// Sort by creation date (newest first)
usort($users, function($a, $b) {
    return $b['created_at'] - $a['created_at'];
});

echo json_encode([
    'success' => true,
    'users' => $users,
    'total' => count($users)
]);

function calculateLastActive($companySlug) {
    // Check recent ads from this company
    $dataDir = __DIR__ . "/../../companies/data/";

    if (!is_dir($dataDir)) return 'Never';

    $latestTimestamp = 0;

    // Scan all categories
    foreach (scandir($dataDir) as $category) {
        if ($category === '.' || $category === '..') continue;

        $companyPath = "$dataDir/$category/$companySlug";
        if (!is_dir($companyPath)) continue;

        // Check for recent ad folders
        foreach (scandir($companyPath) as $adFolder) {
            if ($adFolder === '.' || $adFolder === '..') continue;

            $metaFile = "$companyPath/$adFolder/meta.json";
            if (file_exists($metaFile)) {
                $adMeta = json_decode(file_get_contents($metaFile), true);
                if ($adMeta && isset($adMeta['timestamp'])) {
                    $latestTimestamp = max($latestTimestamp, $adMeta['timestamp']);
                }
            }
        }
    }

    if ($latestTimestamp === 0) return 'Never';

    $diff = time() - $latestTimestamp;

    if ($diff < 60) return 'Just now';
    if ($diff < 3600) return floor($diff / 60) . ' mins ago';
    if ($diff < 86400) return floor($diff / 3600) . ' hours ago';
    if ($diff < 604800) return floor($diff / 86400) . ' days ago';

    return date('M j, Y', $latestTimestamp);
}

