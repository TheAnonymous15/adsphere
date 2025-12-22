<?php
/********************************************
 * Update Ad Handler
 * Processes ad edit form submission
 ********************************************/
session_start();

if (!isset($_SESSION['company'])) {
    header("Location: /login");
    exit();
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header("Location: ../home/my_ads.php");
    exit();
}

$companySlug = $_SESSION['company'];
$adId = $_POST['ad_id'] ?? '';
$oldCategory = $_POST['old_category'] ?? '';
$newCategory = $_POST['category'] ?? '';
$title = trim($_POST['title'] ?? '');
$description = trim($_POST['description'] ?? '');

if (empty($adId) || empty($newCategory) || empty($title)) {
    $_SESSION['error'] = "Missing required fields";
    header("Location: ../home/edit_ad.php?id=" . urlencode($adId));
    exit();
}

$dataBase = __DIR__ . "/../data/";
$oldAdPath = "$dataBase/$oldCategory/$companySlug/$adId";

// Verify ad exists and belongs to company
if (!is_dir($oldAdPath)) {
    $_SESSION['error'] = "Ad not found";
    header("Location: ../home/my_ads.php");
    exit();
}

$metaFile = "$oldAdPath/meta.json";
if (!file_exists($metaFile)) {
    $_SESSION['error'] = "Ad metadata not found";
    header("Location: ../home/my_ads.php");
    exit();
}

$meta = json_decode(file_get_contents($metaFile), true);

if (!$meta || $meta['company'] !== $companySlug) {
    $_SESSION['error'] = "Unauthorized access";
    header("Location: ../home/my_ads.php");
    exit();
}

// Update metadata
$meta['title'] = $title;
$meta['description'] = $description;
$meta['updated_at'] = time();

// Handle media upload if provided
if (!empty($_FILES['media']['name'])) {
    $file = $_FILES['media'];

    // Validate file
    $maxSize = 10 * 1024 * 1024; // 10MB
    if ($file['size'] > $maxSize) {
        $_SESSION['error'] = "File too large. Maximum size is 10MB";
        header("Location: ../home/edit_ad.php?id=" . urlencode($adId));
        exit();
    }

    $allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'video/mp4', 'video/webm', 'video/quicktime'];
    if (!in_array($file['type'], $allowedTypes)) {
        $_SESSION['error'] = "Invalid file type. Only images and videos are allowed";
        header("Location: ../home/edit_ad.php?id=" . urlencode($adId));
        exit();
    }

    // Delete old media
    $oldMedia = $meta['media'] ?? '';
    if ($oldMedia && file_exists("$oldAdPath/$oldMedia")) {
        unlink("$oldAdPath/$oldMedia");
    }

    // Save new media
    $ext = pathinfo($file['name'], PATHINFO_EXTENSION);
    $newMediaName = "$adId.$ext";

    if (move_uploaded_file($file['tmp_name'], "$oldAdPath/$newMediaName")) {
        $meta['media'] = $newMediaName;
    } else {
        $_SESSION['error'] = "Failed to upload media file";
        header("Location: ../home/edit_ad.php?id=" . urlencode($adId));
        exit();
    }
}

// Handle category change (move ad to new category folder)
if ($oldCategory !== $newCategory) {
    $newAdPath = "$dataBase/$newCategory/$companySlug/$adId";

    // Create new directory if needed
    if (!is_dir("$dataBase/$newCategory/$companySlug")) {
        mkdir("$dataBase/$newCategory/$companySlug", 0775, true);
    }

    // Move ad directory to new category
    if (rename($oldAdPath, $newAdPath)) {
        $meta['category'] = $newCategory;
        $oldAdPath = $newAdPath;
        $metaFile = "$newAdPath/meta.json";
    } else {
        $_SESSION['error'] = "Failed to move ad to new category";
        header("Location: ../home/edit_ad.php?id=" . urlencode($adId));
        exit();
    }
} else {
    $meta['category'] = $newCategory;
}

// Save updated metadata
if (file_put_contents($metaFile, json_encode($meta, JSON_PRETTY_PRINT))) {
    $_SESSION['message'] = "Ad updated successfully";
} else {
    $_SESSION['error'] = "Failed to save changes";
}

header("Location: ../home/edit_ad.php?id=" . urlencode($adId));
exit();

