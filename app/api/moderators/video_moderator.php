<?php
/********************************************
 * Video Moderator API (Stub)
 * Designed for future video frame analysis
 ********************************************/

require_once __DIR__ . '/../../includes/AIContentModerator.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

// NOTE: This is a stub for now. In the future, you can:
// 1. Extract key frames from the video
// 2. Pass those frames to AIContentModerator->advancedImageModeration
// 3. Aggregate results across frames

try {
    if (empty($_FILES['video'])) {
        throw new Exception('No video uploaded');
    }

    $file = $_FILES['video'];
    if ($file['error'] !== UPLOAD_ERR_OK) {
        throw new Exception('Upload error: ' . $file['error']);
    }

    // For now, just acknowledge receipt and mark for manual review
    echo json_encode([
        'success' => true,
        'type' => 'video',
        'status' => 'received',
        'message' => 'Video moderation not yet fully implemented. This upload should be queued for manual review.',
    ], JSON_PRETTY_PRINT);

} catch (Throwable $e) {
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}

