<?php
}
    ]);
        'error' => $e->getMessage()
        'success' => false,
    echo json_encode([
    http_response_code(400);
} catch (Throwable $e) {

    ], JSON_PRETTY_PRINT);
        'report' => $report
        'copyright' => $copyright,
        'moderation' => $modResult,
        'type' => 'text',
        'success' => true,
    echo json_encode([

    $report = $moderator->generateReport($modResult, $copyright);
    $copyright = $moderator->checkCopyrightRisk($title, $description);
    $modResult = $moderator->moderateAd($title, $description, []);
    $moderator = new AIContentModerator();

    $description = $payload['description'] ?? '';
    $title = $payload['title'] ?? '';

    }
        throw new Exception('Invalid JSON payload');
    if (!is_array($payload)) {

    $payload = json_decode($raw, true);
    $raw = file_get_contents('php://input');
try {

header('Access-Control-Allow-Origin: *');

}
    exit;
    http_response_code(204);
    header('Access-Control-Allow-Headers: Content-Type');
    header('Access-Control-Allow-Methods: POST, OPTIONS');
    header('Access-Control-Allow-Origin: *');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
// Basic CORS support for local tools/UI

header('Content-Type: application/json');

require_once __DIR__ . '/../../includes/AIContentModerator.php';

 ********************************************/
 * Advanced text-only moderation endpoint
 * Text Moderator API
/********************************************

