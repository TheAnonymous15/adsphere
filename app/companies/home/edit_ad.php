<?php
/********************************************
 * Edit Ad Page
 * Edit existing advertisement
 ********************************************/
session_start();

// Block unauthorized access
if(!isset($_SESSION['company'])) {
    header("Location: /app/companies/handlers/login.php");
    exit();
}

$companySlug = $_SESSION['company'];
$companyName = $_SESSION['company_name'] ?? ucfirst($companySlug);

// Get ad ID
$adId = $_GET['id'] ?? '';

if (empty($adId)) {
    header("Location: my_ads.php");
    exit();
}

// Load ad data
$dataBase = __DIR__ . "/../data/";
$adData = null;
$adCategory = '';

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
                $adData = $meta;
                $adCategory = $category;
                break;
            }
        }
    }
}

if (!$adData) {
    $_SESSION['error'] = "Ad not found or unauthorized";
    header("Location: my_ads.php");
    exit();
}

// Load company metadata for categories
$metaFile = __DIR__ . "/../metadata/{$companySlug}.json";
$companyData = [];
if (file_exists($metaFile)) {
    $companyData = json_decode(file_get_contents($metaFile), true);
}
$categories = $companyData['categories'] ?? [];

$message = $_SESSION['message'] ?? '';
$error = $_SESSION['error'] ?? '';
unset($_SESSION['message'], $_SESSION['error']);
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edit Ad - AdSphere</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
</head>

<body class="bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900 text-white min-h-screen">

<!-- NAVBAR -->
<nav class="bg-slate-900/80 backdrop-blur-lg border-b border-white/10 sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
            <div class="flex items-center gap-3">
                <a href="my_ads.php" class="flex items-center gap-3 hover:opacity-80 transition">
                    <div class="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                        <i class="fas fa-edit text-white text-xl"></i>
                    </div>
                    <div>
                        <h1 class="text-xl font-bold text-white">Edit Ad</h1>
                        <p class="text-xs text-gray-400"><?= htmlspecialchars($companyName) ?></p>
                    </div>
                </a>
            </div>

            <div class="flex items-center gap-4">
                <a href="my_ads.php" class="flex items-center gap-2 text-gray-300 hover:text-white transition">
                    <i class="fas fa-arrow-left"></i>
                    <span>Back to Ads</span>
                </a>
            </div>
        </div>
    </div>
</nav>

<!-- MAIN CONTENT -->
<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

    <?php if($message): ?>
        <div class="bg-green-500/10 border border-green-500/50 rounded-xl p-4 mb-6">
            <i class="fas fa-check-circle text-green-400 mr-2"></i>
            <?= htmlspecialchars($message) ?>
        </div>
    <?php endif; ?>

    <?php if($error): ?>
        <div class="bg-red-500/10 border border-red-500/50 rounded-xl p-4 mb-6">
            <i class="fas fa-exclamation-triangle text-red-400 mr-2"></i>
            <?= htmlspecialchars($error) ?>
        </div>
    <?php endif; ?>

    <div class="bg-slate-800/50 backdrop-blur rounded-2xl p-8 border border-white/10">
        <h2 class="text-2xl font-bold mb-6">Edit Advertisement</h2>

        <form method="POST" action="/app/companies/handlers/update_ad.php" enctype="multipart/form-data" class="space-y-6">
            <input type="hidden" name="ad_id" value="<?= htmlspecialchars($adId) ?>">
            <input type="hidden" name="old_category" value="<?= htmlspecialchars($adCategory) ?>">

            <!-- Title -->
            <div>
                <label class="block text-sm font-medium mb-2">
                    <i class="fas fa-heading mr-2"></i>Ad Title *
                </label>
                <input
                    type="text"
                    name="title"
                    value="<?= htmlspecialchars($adData['title'] ?? '') ?>"
                    required
                    maxlength="100"
                    class="w-full bg-slate-900 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="Enter ad title...">
            </div>

            <!-- Description -->
            <div>
                <label class="block text-sm font-medium mb-2">
                    <i class="fas fa-align-left mr-2"></i>Description *
                </label>
                <textarea
                    name="description"
                    rows="5"
                    required
                    maxlength="500"
                    class="w-full bg-slate-900 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                    placeholder="Describe your ad..."><?= htmlspecialchars($adData['description'] ?? '') ?></textarea>
                <p class="text-xs text-gray-400 mt-1">Maximum 500 characters</p>
            </div>

            <!-- Category -->
            <div>
                <label class="block text-sm font-medium mb-2">
                    <i class="fas fa-tag mr-2"></i>Category *
                </label>
                <select
                    name="category"
                    required
                    class="w-full bg-slate-900 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                    <?php foreach($categories as $cat): ?>
                        <option value="<?= htmlspecialchars($cat) ?>" <?= $cat === $adCategory ? 'selected' : '' ?>>
                            <?= htmlspecialchars(ucfirst($cat)) ?>
                        </option>
                    <?php endforeach; ?>
                </select>
            </div>

            <!-- Current Media -->
            <div>
                <label class="block text-sm font-medium mb-2">
                    <i class="fas fa-image mr-2"></i>Current Media
                </label>
                <div class="bg-slate-900 rounded-lg p-4 border border-gray-600">
                    <?php
                    $mediaPath = "/app/companies/data/$adCategory/$companySlug/$adId/" . ($adData['media'] ?? '');
                    $isVideo = preg_match('/\.(mp4|mov|webm)$/i', $mediaPath);
                    ?>
                    <?php if($isVideo): ?>
                        <video class="w-full max-w-md rounded-lg" controls>
                            <source src="<?= htmlspecialchars($mediaPath) ?>">
                        </video>
                    <?php else: ?>
                        <img src="<?= htmlspecialchars($mediaPath) ?>" alt="Current ad media" class="w-full max-w-md rounded-lg">
                    <?php endif; ?>
                </div>
            </div>

            <!-- New Media (Optional) -->
            <div>
                <label class="block text-sm font-medium mb-2">
                    <i class="fas fa-upload mr-2"></i>Replace Media (Optional)
                </label>
                <input
                    type="file"
                    name="media"
                    accept="image/*,video/*"
                    class="w-full bg-slate-900 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500">
                <p class="text-xs text-gray-400 mt-1">Leave empty to keep current media. Accepted: images and videos (max 10MB)</p>
            </div>

            <!-- Actions -->
            <div class="flex gap-4 pt-4">
                <button
                    type="submit"
                    class="flex-1 bg-indigo-600 hover:bg-indigo-700 py-3 rounded-lg font-semibold transition">
                    <i class="fas fa-save mr-2"></i>Save Changes
                </button>
                <a
                    href="my_ads.php"
                    class="flex-1 bg-gray-700 hover:bg-gray-600 py-3 rounded-lg font-semibold text-center transition">
                    <i class="fas fa-times mr-2"></i>Cancel
                </a>
            </div>
        </form>
    </div>
</div>

</body>
</html>

