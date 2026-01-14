<?php
/********************************************
 * Ad Scheduling API
 * Set start and end dates for ads
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
$adId = $input['ad_id'] ?? '';
$startDate = $input['start_date'] ?? null;
$endDate = $input['end_date'] ?? null;
$autoRenew = $input['auto_renew'] ?? false;

if (empty($adId)) {
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'message' => 'No ad ID provided'
    ]);
    exit;
}

// Validate dates
if ($startDate && !strtotime($startDate)) {
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'message' => 'Invalid start date format'
    ]);
    exit;
}

if ($endDate && !strtotime($endDate)) {
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'message' => 'Invalid end date format'
    ]);
    exit;
}

$dataBase = __DIR__ . "/../companies/data/";
$found = false;

// Search for the ad
foreach (scandir($dataBase) as $category) {
    if ($category === '.' || $category === '..') continue;

    $categoryPath = "$dataBase/$category";
    if (!is_dir($categoryPath)) continue;

    $companyPath = "$categoryPath/$companySlug";
    if (!is_dir($companyPath)) continue;

    $adPath = "$companyPath/$adId";
    if (is_dir($adPath)) {
        $metaFile = "$adPath/meta.json";

        if (file_exists($metaFile)) {
            $meta = json_decode(file_get_contents($metaFile), true);

            if ($meta && $meta['company'] === $companySlug) {
                // Update scheduling
                $meta['schedule'] = [
                    'start_date' => $startDate ? strtotime($startDate) : null,
                    'end_date' => $endDate ? strtotime($endDate) : null,
                    'auto_renew' => $autoRenew,
                    'updated_at' => time()
                ];

                // Auto-set status based on dates
                $now = time();
                if ($startDate && strtotime($startDate) > $now) {
                    $meta['status'] = 'scheduled';
                } elseif ($endDate && strtotime($endDate) < $now) {
                    $meta['status'] = 'expired';
                } else {
                    $meta['status'] = 'active';
                }

                // Save updated metadata
                file_put_contents($metaFile, json_encode($meta, JSON_PRETTY_PRINT));

                echo json_encode([
                    'success' => true,
                    'message' => 'Schedule updated successfully',
                    'ad_id' => $adId,
                    'schedule' => $meta['schedule'],
                    'status' => $meta['status']
                ]);

                $found = true;
                break;
            }
        }
    }
}

if (!$found) {
    http_response_code(404);
    echo json_encode([
        'success' => false,
        'message' => 'Ad not found or unauthorized'
    ]);
}

