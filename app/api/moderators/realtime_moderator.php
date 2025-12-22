<?php
/********************************************
 * Realtime Moderator API
 * Composite moderator for text + images + future signals
 ********************************************/

require_once __DIR__ . '/../../includes/AIContentModerator.php';
require_once __DIR__ . '/../../moderator_services/ModerationServiceClient.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

// This endpoint supports mixed JSON + file upload:
// - JSON field `meta` with title/description and optional context
// - Optional `images[]` files (we save locally; you may also expose URLs to microservice later)

try {
    $metaJson = $_POST['meta'] ?? '{}';
    $meta = json_decode($metaJson, true);
    if (!is_array($meta)) {
        throw new Exception('Invalid meta JSON');
    }

    $title = $meta['title'] ?? '';
    $description = $meta['description'] ?? '';

    // Handle optional images (local paths)
    $imagePaths = [];
    if (!empty($_FILES['images'])) {
        $files = $_FILES['images'];
        $count = is_array($files['name']) ? count($files['name']) : 0;
        $tempDir = sys_get_temp_dir() . '/adsphere_mod_images';
        if (!is_dir($tempDir)) {
            @mkdir($tempDir, 0775, true);
        }
        for ($i = 0; $i < $count; $i++) {
            if ($files['error'][$i] !== UPLOAD_ERR_OK) continue;
            $tmpName = $files['tmp_name'][$i];
            $name = basename($files['name'][$i]);
            $target = $tempDir . '/' . uniqid('img_', true) . '_' . preg_replace('/[^a-zA-Z0-9._-]/', '_', $name);
            if (!move_uploaded_file($tmpName, $target)) continue;
            $imagePaths[] = $target;
        }
    }

    // 1) Try external AI/ML microservice (FastAPI / Docker)
    $externalClient = new ModerationServiceClient();

    // For now we don't have public URLs for temp images; you can later adapt this
    // to pass CDN URLs or relative paths that the microservice can fetch.
    $externalImageUrls = [];

    $context = [
        'category' => $meta['category'] ?? 'general',
        'language' => $meta['language'] ?? 'auto',
        'user_id'  => $meta['user_id'] ?? null,
        'company'  => $meta['company'] ?? null,
        'ad_id'    => $meta['ad_id'] ?? null,
        'source'   => 'php_realtime_moderator',
    ];

    $externalResult = $externalClient->moderateRealtime($title, $description, $externalImageUrls, [], $context);

    $usedExternal = false;
    $modResult = null;

    if (is_array($externalResult) && !empty($externalResult['success'])) {
        // Normalize external result into the shape expected by existing frontends
        $usedExternal = true;

        $decision      = $externalResult['decision'] ?? 'review';
        $riskLevel     = $externalResult['risk_level'] ?? 'medium';
        $globalScore   = isset($externalResult['global_score']) ? (float)$externalResult['global_score'] : 0.0;
        $categoryScores = $externalResult['category_scores'] ?? [];
        $flags         = $externalResult['flags'] ?? [];
        $reasons       = $externalResult['reasons'] ?? [];

        // Map 0..1 global score to 0..100 style like AIContentModerator
        $score100 = max(0, min(100, (int)round($globalScore * 100)));

        $modResult = [
            'safe'            => $decision === 'approve',
            'score'           => $score100,
            'issues'          => $reasons,
            'warnings'        => [],
            'flags'           => $flags,
            'confidence'      => 90, // external AI confidence (placeholder)
            'risk_level'      => $riskLevel,
            'processing_time' => $externalResult['processing_time'] ?? 0,
            'source'          => 'external_ai',
            'raw_external'    => $externalResult,
            'category_scores' => $categoryScores,
        ];

    } else {
        // 2) Fallback: use local AIContentModerator rules engine
        $moderator = new AIContentModerator();
        $modResult = $moderator->moderateAd($title, $description, $imagePaths);
        $modResult['source'] = 'local_rules';
        $usedExternal = false;
    }

    // Always run local copyright check and report generation for consistency
    $localModerator = new AIContentModerator();
    $copyright = $localModerator->checkCopyrightRisk($title, $description);
    $report = $localModerator->generateReport($modResult, $copyright);

    echo json_encode([
        'success'        => true,
        'type'           => 'realtime',
        'used_external'  => $usedExternal,
        'moderation'     => $modResult,
        'copyright'      => $copyright,
        'report'         => $report
    ], JSON_PRETTY_PRINT);

} catch (Throwable $e) {
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'error'   => $e->getMessage()
    ]);
}
