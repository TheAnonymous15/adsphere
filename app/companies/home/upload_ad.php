<?php
/********************************************
 * ad_upload.php - Professional Multi-Media Upload
 * Hybrid SQLite + Files System
 * Features: Multiple images (up to 4), video upload, automatic compression
 ********************************************/
session_start();

if (!isset($_SESSION["logged_in"])) {
    header("Location: login.php");
    exit;
}

$loggedCompany = $_SESSION["company"];

$adsBase = __DIR__ . "/../data/";
$metaBase = __DIR__ . "/../metadata/";

// Load the new database system
require_once __DIR__ . '/../../database/AdModel.php';
$adModel = new AdModel();

// Load NEW AI/ML Moderation Service Client
require_once __DIR__ . '/../../moderator_services/ModerationServiceClient.php';
$moderationClient = new ModerationServiceClient('http://localhost:8002');

// Get company metadata with contact info (from database)
$companyData = Database::getInstance()->queryOne(
    "SELECT * FROM companies WHERE company_slug = ?",
    [$loggedCompany]
);

$contactInfo = [
    'phone' => $companyData['phone'] ?? null,
    'sms' => $companyData['sms'] ?? null,
    'email' => $companyData['email'] ?? null,
    'whatsapp' => $companyData['whatsapp'] ?? null
];

// Get assigned categories from database (with caching)
$categories = $adModel->getCompanyCategories($loggedCompany);

/******************************
 * IMAGE COMPRESSION FUNCTION
 * Compress images to <1MB while maintaining quality
 * Skip compression if already under 1MB
 ******************************/
function compressImage($sourcePath, $destPath, $maxSizeKB = 1024, $quality = 90) {
    // Check if source file exists
    if (!file_exists($sourcePath)) {
        return false;
    }

    // Get file size
    $sourceSize = filesize($sourcePath);

    // If already under max size, just copy it
    if ($sourceSize <= ($maxSizeKB * 1024)) {
        return copy($sourcePath, $destPath);
    }

    $imageInfo = getimagesize($sourcePath);
    if (!$imageInfo) return false;

    $mimeType = $imageInfo['mime'];

    // Create image resource based on type
    switch ($mimeType) {
        case 'image/jpeg':
            $image = @imagecreatefromjpeg($sourcePath);
            break;
        case 'image/png':
            $image = @imagecreatefrompng($sourcePath);
            break;
        case 'image/gif':
            $image = @imagecreatefromgif($sourcePath);
            break;
        case 'image/webp':
            $image = @imagecreatefromwebp($sourcePath);
            break;
        default:
            return copy($sourcePath, $destPath);
    }

    if (!$image) return false;

    // Get original dimensions
    $width = imagesx($image);
    $height = imagesy($image);

    // Calculate max dimensions (scale down if too large)
    $maxWidth = 1920;
    $maxHeight = 1920;

    if ($width > $maxWidth || $height > $maxHeight) {
        $ratio = min($maxWidth / $width, $maxHeight / $height);
        $newWidth = (int)($width * $ratio);
        $newHeight = (int)($height * $ratio);

        $resized = imagecreatetruecolor($newWidth, $newHeight);

        // Preserve transparency for PNG
        if ($mimeType === 'image/png') {
            imagealphablending($resized, false);
            imagesavealpha($resized, true);
            $transparent = imagecolorallocatealpha($resized, 255, 255, 255, 127);
            imagefilledrectangle($resized, 0, 0, $newWidth, $newHeight, $transparent);
        }

        imagecopyresampled($resized, $image, 0, 0, 0, 0, $newWidth, $newHeight, $width, $height);
        imagedestroy($image);
        $image = $resized;
    }

    // Progressive compression until under max size
    $tempPath = $destPath . '.tmp';
    $currentQuality = $quality;

    do {
        imagejpeg($image, $tempPath, $currentQuality);
        $fileSize = filesize($tempPath);

        if ($fileSize <= ($maxSizeKB * 1024)) {
            break;
        }

        $currentQuality -= 5;

    } while ($currentQuality > 40);

    imagedestroy($image);

    // Move temp to final destination
    if (file_exists($tempPath)) {
        rename($tempPath, $destPath);
        return filesize($destPath) <= ($maxSizeKB * 1024);
    }

    return false;
}

/******************************
 * PROCESS IMAGE THROUGH SECURITY PIPELINE
 * Pipeline: Scan → Sanitize → Compress → OCR
 * Returns processed (safe) image data
 ******************************/
function processImageThroughPipeline($inputPath, $outputPath, $moderationClient = null) {
    $result = [
        'success' => false,
        'sanitized' => false,
        'compressed' => false,
        'threats_found' => [],
        'warnings' => [],
        'ocr_text' => null
    ];

    // Method 1: Try the moderation service API
    if ($moderationClient !== null) {
        try {
            $apiResult = $moderationClient->processImage($inputPath, [
                'output_format' => 'webp',
                'target_size' => 1024 * 1024
            ]);

            if ($apiResult && isset($apiResult['success']) && $apiResult['success']) {
                // API returned processed image as base64
                if (isset($apiResult['processed_image'])) {
                    $imageData = base64_decode($apiResult['processed_image']);
                    if ($imageData && file_put_contents($outputPath, $imageData)) {
                        $result['success'] = true;
                        $result['sanitized'] = $apiResult['sanitized'] ?? true;
                        $result['compressed'] = $apiResult['compressed'] ?? true;
                        $result['threats_found'] = $apiResult['threats_found'] ?? [];
                        $result['warnings'] = $apiResult['warnings'] ?? [];
                        $result['ocr_text'] = $apiResult['ocr_text'] ?? null;
                        return $result;
                    }
                }
            }
        } catch (Exception $e) {
            error_log("[PIPELINE] API method failed: " . $e->getMessage());
        }
    }

    // Method 2: Try local Python CLI processing
    $pythonScript = __DIR__ . '/../../moderator_services/process_image_cli.py';

    if (file_exists($pythonScript)) {
        $cmd = sprintf(
            'python3 %s %s %s --json 2>&1',
            escapeshellarg($pythonScript),
            escapeshellarg($inputPath),
            escapeshellarg($outputPath)
        );

        $output = shell_exec($cmd);

        if ($output) {
            $jsonResult = json_decode($output, true);
            if ($jsonResult && isset($jsonResult['success']) && $jsonResult['success']) {
                if (file_exists($outputPath)) {
                    $result['success'] = true;
                    $result['sanitized'] = $jsonResult['sanitized'] ?? false;
                    $result['compressed'] = $jsonResult['compressed'] ?? false;
                    $result['threats_found'] = $jsonResult['threats_found'] ?? [];
                    $result['warnings'] = $jsonResult['warnings'] ?? [];
                    return $result;
                }
            }
        }

        error_log("[PIPELINE] Python CLI output: " . ($output ?? 'null'));
    }

    // Method 3: Fallback - just copy the file (no processing)
    if (copy($inputPath, $outputPath)) {
        $result['success'] = true;
        $result['warnings'][] = 'Pipeline unavailable, using original image';
        error_log("[PIPELINE] Using fallback copy for: " . $inputPath);
    }

    return $result;
}

// generate UUID
function generate_ad_id(){
    $micro = microtime(true);
    $d = new DateTime();
    $d->setTimestamp((int)$micro);
    $Y = $d->format("Y");
    $m = $d->format("m");
    $time = $d->format("His") . substr((string)$micro, -4);
    $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    $rand = "";
    for($i=0;$i<5;$i++){
        $rand .= $chars[random_int(0, strlen($chars)-1)];
    }
    return "AD-$Y$m-$time-$rand";
}

$msg = "";
$msgType = "success"; // success, error, warning

/******************************
 * HANDLE FORM POST
 ******************************/
if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    $category = $_POST['category'] ?? null;
    $title = trim($_POST['title'] ?? '');
    $description = trim($_POST['description'] ?? '');
    $mediaType = $_POST['media_type'] ?? 'images'; // 'images' or 'video'

    if (!$category || !$title) {
        $msg = "❌ Missing required fields.";
        $msgType = "error";
    } else {

        $adId = generate_ad_id();
        $adDir = "$adsBase/$category/$loggedCompany/$adId";

        if (!is_dir($adDir)) mkdir($adDir, 0775, true);

        $uploadedFiles = [];
        $mediaInfo = [];

        try {

            if ($mediaType === 'video') {
                // Handle single video upload
                if (!empty($_FILES["video"]["name"])) {
                    $ext = strtolower(pathinfo($_FILES["video"]["name"], PATHINFO_EXTENSION));
                    $allowedVideoExts = ['mp4', 'webm', 'mov', 'avi', 'mkv'];

                    if (!in_array($ext, $allowedVideoExts)) {
                        throw new Exception("❌ Unsupported video format. Allowed: " . implode(', ', $allowedVideoExts));
                    }

                    $videoName = $adId . ".{$ext}";
                    $destPath = "$adDir/$videoName";

                    if (!move_uploaded_file($_FILES["video"]["tmp_name"], $destPath)) {
                        throw new Exception("❌ Video upload failed!");
                    }

                    $uploadedFiles[] = $videoName;
                    $mediaInfo = [
                        'type' => 'video',
                        'primary' => $videoName,
                        'files' => [$videoName]
                    ];

                    $msg = "✅ Video uploaded successfully!";
                } else {
                    throw new Exception("❌ No video file selected.");
                }

            } else {
                // Handle multiple images upload (up to 4)
                // NEW: Uses security pipeline: Scan → Sanitize → Compress → OCR
                $imageCount = 0;
                $compressionInfo = [];
                $allowedImageExts = ['jpg', 'jpeg', 'png', 'gif', 'webp'];

                for ($i = 0; $i < 4; $i++) {
                    if (!empty($_FILES["images"]["name"][$i])) {
                        $ext = strtolower(pathinfo($_FILES["images"]["name"][$i], PATHINFO_EXTENSION));

                        if (!in_array($ext, $allowedImageExts)) {
                            throw new Exception("❌ Unsupported image format for image " . ($i + 1));
                        }

                        // Get original size
                        $originalSize = $_FILES["images"]["size"][$i];
                        $originalSizeKB = round($originalSize / 1024, 2);

                        // Save as WebP after pipeline processing
                        $imageName = $adId . "_" . ($i + 1) . ".webp";
                        $tempPath = $_FILES["images"]["tmp_name"][$i];
                        $destPath = "$adDir/$imageName";

                        // ===== NEW: Process through security pipeline =====
                        // Pipeline: Scan → Sanitize → Compress to WebP ≤ 1MB
                        $pipelineResult = processImageThroughPipeline($tempPath, $destPath, $moderationClient);

                        if (!$pipelineResult['success']) {
                            // Fallback to old compression method
                            error_log("[UPLOAD] Pipeline failed for image " . ($i + 1) . ", using fallback");
                            $imageName = $adId . "_" . ($i + 1) . ".jpg";
                            $destPath = "$adDir/$imageName";
                            if (!compressImage($tempPath, $destPath, 1024, 90)) {
                                throw new Exception("❌ Failed to process image " . ($i + 1));
                            }
                            $pipelineResult = [
                                'success' => true,
                                'sanitized' => false,
                                'compressed' => true,
                                'threats_found' => [],
                                'warnings' => ['Used fallback compression']
                            ];
                        }

                        $finalSize = filesize($destPath);
                        $finalSizeKB = round($finalSize / 1024, 2);

                        $wasCompressed = $originalSize > (1024 * 1024);
                        $wasSanitized = $pipelineResult['sanitized'] ?? false;
                        $threatsRemoved = $pipelineResult['threats_found'] ?? [];

                        $compressionInfo[] = [
                            'name' => $_FILES["images"]["name"][$i],
                            'original' => $originalSizeKB,
                            'final' => $finalSizeKB,
                            'compressed' => $wasCompressed,
                            'sanitized' => $wasSanitized,
                            'threats_removed' => $threatsRemoved,
                            'pipeline_warnings' => $pipelineResult['warnings'] ?? []
                        ];

                        $uploadedFiles[] = $imageName;
                        $imageCount++;
                    }
                }

                if ($imageCount === 0) {
                    throw new Exception("❌ Please upload at least one image.");
                }

                $mediaInfo = [
                    'type' => 'image',
                    'primary' => $uploadedFiles[0],
                    'files' => $uploadedFiles,
                    'count' => $imageCount
                ];

                // Build message with compression and security info
                $compressedCount = count(array_filter($compressionInfo, fn($info) => $info['compressed']));
                $sanitizedCount = count(array_filter($compressionInfo, fn($info) => $info['sanitized']));
                $threatsRemovedTotal = array_sum(array_map(fn($info) => count($info['threats_removed'] ?? []), $compressionInfo));

                $msg = "✅ {$imageCount} image(s) uploaded successfully!";

                $extras = [];
                if ($compressedCount > 0) {
                    $extras[] = "{$compressedCount} compressed to <1MB";
                }
                if ($sanitizedCount > 0) {
                    $extras[] = "{$sanitizedCount} security-sanitized";
                }
                if ($threatsRemovedTotal > 0) {
                    $extras[] = "{$threatsRemovedTotal} threat(s) removed";
                }
                if (!empty($extras)) {
                    $msg .= " (" . implode(", ", $extras) . ")";
                }
            }

            // ===== AI/ML CONTENT MODERATION (New Service) =====
            // Prepare media URLs for moderation based on media type
            $imageUrls = [];
            $videoUrls = [];

            foreach ($uploadedFiles as $file) {
                $filePath = "$adDir/$file";

                if ($mediaType === 'video') {
                    $videoUrls[] = $filePath;
                } else {
                    $imageUrls[] = $filePath;
                }
            }

            // Call the new moderation service with retry logic
            $moderationResult = null;
            $maxRetries = 2;
            $retryCount = 0;

            while ($retryCount <= $maxRetries && $moderationResult === null) {
                try {
                    $moderationResult = $moderationClient->moderateRealtime(
                        title: $title,
                        description: $description,
                        imageUrls: $imageUrls,
                        videoUrls: $videoUrls,
                        context: [
                            'ad_id' => $adId,
                            'company' => $loggedCompany,
                            'category' => $category,
                            'user_id' => $_SESSION['user_id'] ?? null,
                            'source' => 'ad_upload',
                            'media_type' => $mediaType
                        ]
                    );
                } catch (Exception $e) {
                    error_log("[MODERATION] Retry $retryCount failed: " . $e->getMessage());
                    $retryCount++;
                    if ($retryCount <= $maxRetries) {
                        usleep(500000); // Wait 500ms before retry
                    }
                }
            }

            // Check moderation result
            if ($moderationResult === null) {
                // Service unavailable - log warning but allow upload
                error_log("[MODERATION] Service unavailable for ad $adId - proceeding with upload");
                $msg .= " ⚠️ AI moderation temporarily unavailable";
                $msgType = "warning";
                $aiReport = [
                    'status' => 'service_unavailable',
                    'decision' => 'pending_review',
                    'message' => 'Moderation service unavailable - manual review required'
                ];
            } else {
                // Process moderation decision
                $decision = $moderationResult['decision'];
                $riskLevel = $moderationResult['risk_level'];
                $globalScore = $moderationResult['global_score'] ?? 0.0;
                $flags = $moderationResult['flags'] ?? [];
                $reasons = $moderationResult['reasons'] ?? [];

                // Block if decision is 'block'
                if ($decision === 'block') {
                    // Delete uploaded files
                    foreach ($uploadedFiles as $file) {
                        @unlink("$adDir/$file");
                    }
                    @rmdir($adDir);

                    throw new Exception(
                        "❌ Content Rejected by AI Moderation: " .
                        implode(", ", $reasons) .
                        " (Risk: " . strtoupper($riskLevel) . ")"
                    );
                }

                // Flag for review if decision is 'review'
                $adStatus = 'active'; // Default status

                if ($decision === 'review') {
                    $msg .= " ⚠️ Flagged for Review: " . implode(", ", $reasons);
                    $msgType = "warning";
                    $adStatus = 'pending_review'; // Set status to pending review
                }

                // Build AI report for storage
                $aiReport = [
                    'service' => 'adsphere_ml_moderation',
                    'version' => '1.0.0',
                    'decision' => $decision,
                    'risk_level' => $riskLevel,
                    'global_score' => $globalScore,
                    'category_scores' => $moderationResult['category_scores'] ?? [],
                    'flags' => $flags,
                    'reasons' => $reasons,
                    'audit_id' => $moderationResult['audit_id'] ?? null,
                    'processing_time_ms' => $moderationResult['processing_time'] ?? 0,
                    'timestamp' => date('Y-m-d H:i:s'),
                    'ai_sources' => $moderationResult['ai_sources'] ?? []
                ];

                // Log moderation decision
                error_log(sprintf(
                    "[MODERATION] Ad %s: Decision=%s, Risk=%s, Score=%.2f, Flags=%s",
                    $adId,
                    $decision,
                    $riskLevel,
                    $globalScore,
                    implode(',', $flags)
                ));
            }
            // ===== END AI MODERATION =====

            // Ensure adStatus is set (default to active if moderation was skipped)
            if (!isset($adStatus)) {
                $adStatus = 'active';
            }

            // Prepare data for database
            $adData = [
                'ad_id' => $adId,
                'company_slug' => $loggedCompany,
                'category_slug' => $category,
                'title' => $title,
                'description' => $description,
                'media_filename' => $mediaInfo['primary'],
                'media_type' => $mediaInfo['type'],
                'media_path' => "$category/$loggedCompany/$adId/{$mediaInfo['primary']}",
                'contact_phone' => $contactInfo['phone'],
                'contact_sms' => $contactInfo['sms'],
                'contact_email' => $contactInfo['email'],
                'contact_whatsapp' => $contactInfo['whatsapp'],
                'status' => $adStatus  // Use dynamic status based on moderation
            ];

            // Save to database using AdModel
            $result = $adModel->createAd($adData);

            if ($result['success']) {
                // Create meta.json for backward compatibility
                $jsonData = [
                    "ad_id" => $adId,
                    "title" => $title,
                    "description" => $description,
                    "category" => $category,
                    "company" => $loggedCompany,
                    "media" => $mediaInfo['files'],
                    "media_type" => $mediaInfo['type'],
                    "primary_media" => $mediaInfo['primary'],
                    "timestamp" => time(),
                    "status" => $adStatus,  // Include status in meta.json
                    "contact" => [
                        "phone" => $contactInfo["phone"] ?? null,
                        "sms" => $contactInfo["sms"] ?? null,
                        "email" => $contactInfo["email"] ?? null,
                        "whatsapp" => $contactInfo["whatsapp"] ?? null
                    ],
                    "ai_moderation" => $aiReport ?? null
                ];

                file_put_contents("$adDir/meta.json", json_encode($jsonData, JSON_PRETTY_PRINT));

                $msgType = "success";

            } else {
                throw new Exception("❌ Database error: " . ($result['error'] ?? 'Unknown error'));
            }

        } catch (Exception $e) {
            // Rollback: delete uploaded files and directory
            foreach ($uploadedFiles as $file) {
                @unlink("$adDir/$file");
            }
            @rmdir($adDir);

            $msg = $e->getMessage();
            $msgType = "error";
        }
    }
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload Ad - Professional</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        .animate-slide-in {
            animation: slideIn 0.5s ease-out;
        }

        .animate-fade-in {
            animation: fadeIn 0.3s ease-in;
        }

        .drag-over {
            border-color: #3b82f6 !important;
            background-color: rgba(59, 130, 246, 0.1) !important;
        }

        .preview-image {
            object-fit: cover;
            border-radius: 12px;
        }

        .glass-effect {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }

        .file-upload-area {
            transition: all 0.3s ease;
        }

        .file-upload-area:hover {
            border-color: #667eea;
            background-color: rgba(102, 126, 234, 0.05);
        }
    </style>
</head>

<body class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen">

<div class="container mx-auto px-4 py-8">

    <!-- Header -->
    <div class="glass-effect rounded-2xl p-6 mb-6 animate-slide-in">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-3xl font-bold text-white flex items-center gap-3">
                    <i class="fas fa-cloud-upload-alt text-purple-400"></i>
                    Upload New Advertisement
                </h1>
                <p class="text-gray-400 mt-2">Create stunning ads with multiple images or video</p>
            </div>
            <div class="text-right">
                <p class="text-sm text-gray-400">Logged in as</p>
                <p class="text-lg font-bold text-purple-400"><?= htmlspecialchars($loggedCompany) ?></p>
                <a href="logout.php" class="text-sm text-red-400 hover:text-red-300 transition">
                    <i class="fas fa-sign-out-alt mr-1"></i>Logout
                </a>
            </div>
        </div>
    </div>

    <!-- Success/Error Message -->
    <?php if ($msg): ?>
        <div class="glass-effect rounded-2xl p-6 mb-6 animate-fade-in border-l-4 <?= $msgType === 'success' ? 'border-green-500' : 'border-red-500' ?>">
            <div class="flex items-center gap-3">
                <i class="fas <?= $msgType === 'success' ? 'fa-check-circle text-green-400' : 'fa-exclamation-circle text-red-400' ?> text-2xl"></i>
                <p class="text-white text-lg"><?= $msg ?></p>
            </div>
        </div>
    <?php endif; ?>

    <?php if (empty($categories)): ?>
        <!-- No Categories -->
        <div class="glass-effect rounded-2xl p-12 text-center">
            <i class="fas fa-folder-open text-6xl text-yellow-400 mb-4"></i>
            <h2 class="text-2xl font-bold text-white mb-2">No Categories Assigned</h2>
            <p class="text-gray-400">Please contact your administrator to assign categories to your account.</p>
        </div>

    <?php else: ?>
        <!-- Upload Form -->
        <form method="POST" enctype="multipart/form-data" id="uploadForm" class="space-y-6">

            <!-- Category & Title Section -->
            <div class="glass-effect rounded-2xl p-6 animate-slide-in">
                <h3 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <i class="fas fa-info-circle text-blue-400"></i>
                    Basic Information
                </h3>

                <div class="grid md:grid-cols-2 gap-6">
                    <!-- Category -->
                    <div>
                        <label class="block text-sm font-semibold text-gray-300 mb-2">
                            <i class="fas fa-folder mr-2 text-purple-400"></i>Category *
                        </label>
                        <select name="category" required
                                class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 transition">
                            <option value="">Select a category</option>
                            <?php foreach ($categories as $cat): ?>
                                <option value="<?= htmlspecialchars($cat['category_slug']) ?>" class="bg-slate-800">
                                    <?= htmlspecialchars($cat['category_name']) ?>
                                </option>
                            <?php endforeach; ?>
                        </select>
                    </div>

                    <!-- Title -->
                    <div>
                        <label class="block text-sm font-semibold text-gray-300 mb-2">
                            <i class="fas fa-heading mr-2 text-purple-400"></i>Ad Title *
                        </label>
                        <input type="text" name="title" required maxlength="100"
                               placeholder="e.g., Brand New iPhone 15 Pro Max"
                               class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 transition">
                    </div>
                </div>

                <!-- Description -->
                <div class="mt-6">
                    <label class="block text-sm font-semibold text-gray-300 mb-2">
                        <i class="fas fa-align-left mr-2 text-purple-400"></i>Description *
                    </label>
                    <textarea name="description" required rows="4" maxlength="1000"
                              placeholder="Describe your product or service in detail..."
                              class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 transition resize-none"></textarea>
                    <p class="text-xs text-gray-500 mt-1">Maximum 1000 characters</p>
                </div>
            </div>

            <!-- Media Type Selection -->
            <div class="glass-effect rounded-2xl p-6">
                <h3 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <i class="fas fa-photo-video text-purple-400"></i>
                    Media Type
                </h3>

                <div class="grid md:grid-cols-2 gap-4">
                    <!-- Images Option -->
                    <div class="relative">
                        <input type="radio" name="media_type" value="images" id="media_images" checked
                               class="peer hidden">
                        <label for="media_images"
                               class="flex items-center gap-4 p-6 bg-white/5 border-2 border-white/20 rounded-xl cursor-pointer hover:border-purple-500 peer-checked:border-purple-500 peer-checked:bg-purple-500/20 transition">
                            <div class="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                                <i class="fas fa-images text-3xl text-white"></i>
                            </div>
                            <div>
                                <h4 class="text-lg font-bold text-white">Multiple Images</h4>
                                <p class="text-sm text-gray-400">Upload up to 4 images</p>
                                <p class="text-xs text-purple-400 mt-1">Auto-compressed to &lt;1MB</p>
                            </div>
                        </label>
                    </div>

                    <!-- Video Option -->
                    <div class="relative">
                        <input type="radio" name="media_type" value="video" id="media_video"
                               class="peer hidden">
                        <label for="media_video"
                               class="flex items-center gap-4 p-6 bg-white/5 border-2 border-white/20 rounded-xl cursor-pointer hover:border-purple-500 peer-checked:border-purple-500 peer-checked:bg-purple-500/20 transition">
                            <div class="w-16 h-16 bg-gradient-to-br from-pink-500 to-orange-600 rounded-xl flex items-center justify-center">
                                <i class="fas fa-video text-3xl text-white"></i>
                            </div>
                            <div>
                                <h4 class="text-lg font-bold text-white">Single Video</h4>
                                <p class="text-sm text-gray-400">Upload one video file</p>
                                <p class="text-xs text-orange-400 mt-1">MP4, WebM, MOV supported</p>
                            </div>
                        </label>
                    </div>
                </div>
            </div>

            <!-- Images Upload Section -->
            <div id="imagesSection" class="glass-effect rounded-2xl p-6">
                <h3 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <i class="fas fa-images text-blue-400"></i>
                    Upload Images (Max 4)
                </h3>

                <div class="grid md:grid-cols-2 gap-4" id="imagePreviewGrid">
                    <?php for ($i = 0; $i < 4; $i++): ?>
                        <div class="image-upload-box">
                            <input type="file" name="images[]" id="image_<?= $i ?>" accept="image/*"
                                   class="hidden image-input" data-index="<?= $i ?>">
                            <label for="image_<?= $i ?>"
                                   class="file-upload-area block border-2 border-dashed border-white/30 rounded-xl p-8 text-center cursor-pointer hover:border-purple-500 transition">
                                <div class="preview-container-<?= $i ?>">
                                    <i class="fas fa-cloud-upload-alt text-4xl text-gray-500 mb-3"></i>
                                    <p class="text-white font-semibold">Image <?= $i + 1 ?></p>
                                    <p class="text-sm text-gray-400 mt-1">Click or drag to upload</p>
                                    <p class="text-xs text-gray-500 mt-2">JPG, PNG, GIF, WebP</p>
                                </div>
                            </label>
                        </div>
                    <?php endfor; ?>
                </div>

                <div class="mt-4 p-4 bg-blue-500/20 border border-blue-500/50 rounded-xl">
                    <p class="text-blue-300 text-sm flex items-start gap-2">
                        <i class="fas fa-info-circle mt-1"></i>
                        <span><strong>Note:</strong> All images will be automatically compressed to under 1MB while maintaining quality. First image will be the primary/cover image.</span>
                    </p>
                </div>
            </div>

            <!-- Video Upload Section -->
            <div id="videoSection" class="glass-effect rounded-2xl p-6 hidden">
                <h3 class="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <i class="fas fa-video text-pink-400"></i>
                    Upload Video
                </h3>

                <div>
                    <input type="file" name="video" id="videoInput" accept="video/*" class="hidden">
                    <label for="videoInput"
                           class="file-upload-area block border-2 border-dashed border-white/30 rounded-xl p-12 text-center cursor-pointer hover:border-pink-500 transition">
                        <div id="videoPreviewContainer">
                            <i class="fas fa-film text-6xl text-gray-500 mb-4"></i>
                            <p class="text-white text-lg font-semibold mb-2">Click to select video</p>
                            <p class="text-gray-400 mb-4">or drag and drop here</p>
                            <p class="text-sm text-gray-500">MP4, WebM, MOV, AVI, MKV supported</p>
                            <p class="text-xs text-gray-600 mt-2">Max size: 100MB recommended</p>
                        </div>
                    </label>
                </div>
            </div>

            <!-- Submit Button -->
            <div class="glass-effect rounded-2xl p-6">
                <!-- Terms of Service Agreement -->
                <div class="mb-6 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-xl">
                    <label class="flex items-start gap-3 cursor-pointer">
                        <input type="checkbox"
                               id="termsCheckbox"
                               required
                               class="mt-1 w-5 h-5 text-purple-600 bg-white/10 border-white/30 rounded focus:ring-purple-500 focus:ring-2">
                        <div class="flex-1">
                            <p class="text-white font-semibold mb-1">
                                <i class="fas fa-file-contract text-yellow-400 mr-2"></i>
                                Terms Agreement
                            </p>
                            <p class="text-gray-300 text-sm">
                                By uploading, you agree to our
                                <a href="/app/includes/terms_of_service.php"
                                   target="_blank"
                                   class="text-yellow-400 hover:text-yellow-300 underline font-semibold">
                                    Terms of Service and Advertising Policy
                                </a>.
                                Your ad will be automatically screened by our AI system for content safety and compliance.
                            </p>
                        </div>
                    </label>
                </div>

                <!-- Submit Section -->
                <div class="flex items-center justify-between">
                    <div class="text-gray-400 text-sm">
                        <i class="fas fa-shield-alt text-green-400 mr-2"></i>
                        Your data is secure and encrypted
                        <br>
                        <i class="fas fa-robot text-purple-400 mr-2"></i>
                        AI content moderation active
                    </div>
                    <button type="submit"
                            id="submitBtn"
                            class="btn-primary px-8 py-4 rounded-xl text-white font-bold text-lg shadow-lg hover:shadow-2xl transition flex items-center gap-3">
                        <i class="fas fa-upload"></i>
                        <span>Upload Advertisement</span>
                    </button>
                </div>
            </div>

        </form>
    <?php endif; ?>

</div>

<script>
// Media type toggle
document.querySelectorAll('input[name="media_type"]').forEach(radio => {
    radio.addEventListener('change', function() {
        const imagesSection = document.getElementById('imagesSection');
        const videoSection = document.getElementById('videoSection');

        if (this.value === 'images') {
            imagesSection.classList.remove('hidden');
            videoSection.classList.add('hidden');
            document.getElementById('videoInput').value = '';
        } else {
            imagesSection.classList.add('hidden');
            videoSection.classList.remove('hidden');
            document.querySelectorAll('.image-input').forEach(input => input.value = '');
        }
    });
});

// Image preview functionality
document.querySelectorAll('.image-input').forEach(input => {
    input.addEventListener('change', function(e) {
        const index = this.dataset.index;
        const file = e.target.files[0];
        const previewContainer = document.querySelector(`.preview-container-${index}`);

        if (file && file.type.startsWith('image/')) {
            const fileSizeKB = (file.size / 1024).toFixed(0);
            const fileSizeMB = (file.size / 1024 / 1024).toFixed(2);
            const needsCompression = file.size > (1024 * 1024);

            const reader = new FileReader();
            reader.onload = function(e) {
                const compressionNote = needsCompression
                    ? `${fileSizeKB} KB → Will compress to <1MB`
                    : `${fileSizeKB} KB (No compression needed)`;

                previewContainer.innerHTML = `
                    <div class="relative">
                        <img src="${e.target.result}" class="preview-image w-full h-48 object-cover mb-2">
                        <div class="absolute top-2 right-2 bg-green-500 text-white px-2 py-1 rounded text-xs">
                            <i class="fas fa-check mr-1"></i>Ready
                        </div>
                        <p class="text-white text-sm font-semibold truncate" title="${file.name}">${file.name}</p>
                        <p class="text-xs ${needsCompression ? 'text-yellow-400' : 'text-green-400'}">${compressionNote}</p>
                    </div>
                `;
            };
            reader.onerror = function() {
                previewContainer.innerHTML = `
                    <div class="text-center">
                        <i class="fas fa-exclamation-triangle text-red-500 text-4xl mb-2"></i>
                        <p class="text-red-400 text-sm">Failed to load preview</p>
                    </div>
                `;
            };
            reader.readAsDataURL(file);
        } else if (file) {
            previewContainer.innerHTML = `
                <div class="text-center">
                    <i class="fas fa-exclamation-triangle text-yellow-500 text-4xl mb-2"></i>
                    <p class="text-yellow-400 text-sm">Please select an image file</p>
                </div>
            `;
        }
    });
});

// Video preview functionality
document.getElementById('videoInput').addEventListener('change', function(e) {
    const file = e.target.files[0];
    const container = document.getElementById('videoPreviewContainer');

    if (file && file.type.startsWith('video/')) {
        const sizeMB = (file.size / 1024 / 1024).toFixed(2);
        container.innerHTML = `
            <div class="text-center">
                <div class="inline-block bg-pink-500/20 p-6 rounded-2xl mb-4">
                    <i class="fas fa-check-circle text-6xl text-pink-400"></i>
                </div>
                <p class="text-white text-xl font-bold mb-2">${file.name}</p>
                <p class="text-gray-400 mb-2">Size: ${sizeMB} MB</p>
                <p class="text-green-400 text-sm"><i class="fas fa-check mr-1"></i>Ready to upload</p>
            </div>
        `;
    }
});

// Form submission loading state
document.getElementById('uploadForm').addEventListener('submit', function(e) {
    // Check terms agreement
    const termsCheckbox = document.getElementById('termsCheckbox');
    if (!termsCheckbox.checked) {
        e.preventDefault();
        alert('⚠️ Please agree to the Terms of Service and Advertising Policy before uploading.');
        return;
    }

    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    btn.innerHTML = `
        <i class="fas fa-spinner fa-spin"></i>
        <span>Uploading & AI Scanning...</span>
    `;
});

// Drag and drop support
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    document.querySelectorAll('.file-upload-area').forEach(area => {
        area.addEventListener(eventName, preventDefaults, false);
    });
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

document.querySelectorAll('.file-upload-area').forEach(area => {
    area.addEventListener('dragenter', () => area.classList.add('drag-over'));
    area.addEventListener('dragleave', () => area.classList.remove('drag-over'));
    area.addEventListener('drop', () => area.classList.remove('drag-over'));
});
</script>

</body>
</html>
