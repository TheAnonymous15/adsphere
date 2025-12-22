<?php
/********************************************
 * Image Moderator API
 * Advanced image-only moderation endpoint
 ********************************************/

require_once __DIR__ . '/../../includes/AIContentModerator.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

// This endpoint expects files via multipart/form-data under key `images[]`

try {
    if (empty($_FILES['images'])) {
        throw new Exception('No images uploaded');
    }

    $uploadedPaths = [];
    $tempDir = sys_get_temp_dir() . '/adsphere_mod_images';
    if (!is_dir($tempDir)) {
        @mkdir($tempDir, 0775, true);
    }

    // Normalize files array
    $files = $_FILES['images'];
    $count = is_array($files['name']) ? count($files['name']) : 0;

    for ($i = 0; $i < $count; $i++) {
        if ($files['error'][$i] !== UPLOAD_ERR_OK) continue;

        $tmpName = $files['tmp_name'][$i];
        $name = basename($files['name'][$i]);
        $target = $tempDir . '/' . uniqid('img_', true) . '_' . preg_replace('/[^a-zA-Z0-9._-]/', '_', $name);

        if (!move_uploaded_file($tmpName, $target)) continue;
        $uploadedPaths[] = $target;
    }

    if (empty($uploadedPaths)) {
        throw new Exception('Failed to save any uploaded images');
    }

    $moderator = new AIContentModerator();
    $modResult = $moderator->moderateAd('IMAGE_ONLY', 'IMAGE_ONLY', $uploadedPaths);
    $dummyCopyright = ['risk' => 'low', 'concerns' => []];
    $report = $moderator->generateReport($modResult, $dummyCopyright);

    echo json_encode([
        'success' => true,
        'type' => 'image',
        'moderation' => $modResult,
        'report' => $report
    ], JSON_PRETTY_PRINT);

} catch (Throwable $e) {
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}

