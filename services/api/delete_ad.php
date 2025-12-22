<?php
/********************************************
 * Delete Ad API
 * Handles single and bulk ad deletion
 ********************************************/
session_start();
header("Content-Type: application/json");

// Security check
if (!isset($_SESSION['company'])) {
    http_response_code(401);
    echo json_encode([
        'success' => false,
        'message' => 'Unauthorized access'
    ]);
    exit;
}

$companySlug = $_SESSION['company'];

// Get request data
$input = json_decode(file_get_contents('php://input'), true);
$adIds = $input['ad_ids'] ?? [];

if (empty($adIds)) {
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'message' => 'No ad IDs provided'
    ]);
    exit;
}

// Ensure ad_ids is an array
if (!is_array($adIds)) {
    $adIds = [$adIds];
}

$dataBase = __DIR__ . "/../companies/data/";
$deletedCount = 0;
$errors = [];

foreach ($adIds as $adId) {
    $found = false;

    // Search for the ad in all categories
    foreach (scandir($dataBase) as $category) {
        if ($category === '.' || $category === '..') continue;

        $categoryPath = "$dataBase/$category";
        if (!is_dir($categoryPath)) continue;

        $companyPath = "$categoryPath/$companySlug";
        if (!is_dir($companyPath)) continue;

        $adPath = "$companyPath/$adId";
        if (is_dir($adPath)) {
            // Verify ownership by checking meta.json
            $metaFile = "$adPath/meta.json";
            if (file_exists($metaFile)) {
                $meta = json_decode(file_get_contents($metaFile), true);

                if ($meta && $meta['company'] === $companySlug) {
                    // Delete the entire ad directory
                    deleteDirectory($adPath);
                    $deletedCount++;
                    $found = true;
                    break;
                }
            }
        }
    }

    if (!$found) {
        $errors[] = "Ad not found or unauthorized: $adId";
    }
}

// Helper function to delete directory recursively
function deleteDirectory($dir) {
    if (!is_dir($dir)) return false;

    $files = array_diff(scandir($dir), ['.', '..']);
    foreach ($files as $file) {
        $path = "$dir/$file";
        is_dir($path) ? deleteDirectory($path) : unlink($path);
    }

    return rmdir($dir);
}

// Response
if ($deletedCount > 0) {
    echo json_encode([
        'success' => true,
        'message' => "$deletedCount ad(s) deleted successfully",
        'deleted_count' => $deletedCount,
        'errors' => $errors
    ]);
} else {
    http_response_code(404);
    echo json_encode([
        'success' => false,
        'message' => 'No ads were deleted',
        'errors' => $errors
    ]);
}

