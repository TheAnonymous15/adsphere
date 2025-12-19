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

// Load AI Content Moderator
require_once __DIR__ . '/../../includes/AIContentModerator.php';
$aiModerator = new AIContentModerator();

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

                        $imageName = $adId . "_" . ($i + 1) . ".jpg"; // Always save as JPG after compression
                        $tempPath = $_FILES["images"]["tmp_name"][$i];
                        $destPath = "$adDir/$imageName";

                        // Compress image (will skip if already under 1MB)
                        if (!compressImage($tempPath, $destPath, 1024, 90)) {
                            throw new Exception("❌ Failed to process image " . ($i + 1));
                        }

                        $finalSize = filesize($destPath);
                        $finalSizeKB = round($finalSize / 1024, 2);

                        $wasCompressed = $originalSize > (1024 * 1024);

                        $compressionInfo[] = [
                            'name' => $_FILES["images"]["name"][$i],
                            'original' => $originalSizeKB,
                            'final' => $finalSizeKB,
                            'compressed' => $wasCompressed
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

                // Build message with compression info
                $compressedCount = count(array_filter($compressionInfo, fn($info) => $info['compressed']));
                $msg = "✅ {$imageCount} image(s) uploaded successfully!";
                if ($compressedCount > 0) {
                    $msg .= " ({$compressedCount} compressed to <1MB)";
                }
            }

            // ===== AI CONTENT MODERATION =====
            // Scan text content
            $imagePaths = array_map(function($file) use ($adDir) {
                return "$adDir/$file";
            }, $uploadedFiles);

            $moderationResult = $aiModerator->moderateAd($title, $description, $imagePaths);
            $copyrightResult = $aiModerator->checkCopyrightRisk($title, $description);

            // Check if content is safe
            if (!$moderationResult['safe']) {
                throw new Exception(
                    "❌ Content Rejected by AI: Your ad contains policy violations. " .
                    implode(", ", $moderationResult['issues'])
                );
            }

            // If score is between 70-85, approve with warnings
            if ($moderationResult['score'] < 85 && $moderationResult['score'] >= 70) {
                $msg .= " ⚠️ Warnings: " . implode(", ", array_merge(
                    $moderationResult['warnings'],
                    $copyrightResult['concerns']
                ));
                $msgType = "warning";
            }

            // Generate AI report
            $aiReport = $aiModerator->generateReport($moderationResult, $copyrightResult);
            // ===== END AI MODERATION =====

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
                'status' => 'active'
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
                    "contact" => [
                        "phone" => $contactInfo["phone"] ?? null,
                        "sms" => $contactInfo["sms"] ?? null,
                        "email" => $contactInfo["email"] ?? null,
                        "whatsapp" => $contactInfo["whatsapp"] ?? null
                    ],
                    "ai_moderation" => $aiReport
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
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
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
