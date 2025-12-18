<?php
header("Content-Type: application/json");

ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);

require_once __DIR__ . "/make_directories.php";

/**
 * Safe request getter
 */
function req($k, $default = null){
    return isset($_POST[$k]) ? trim($_POST[$k]) : $default;
}

/**
 * Validate required fields
 */
if (!isset($_POST['company_name']) || trim($_POST['company_name']) === "") {
    echo json_encode([
        "success" => false,
        "message" => "company_name is required"
    ]);
    exit;
}

$metaBase = __DIR__ . "/../metadata/";
if (!is_dir($metaBase)) mkdir($metaBase, 0775, true);

/**
 * Build slug
 */
$slug = strtolower($_POST['company_name']);
$slug = preg_replace("/[^a-z0-9\s-]/", "", $slug);
$slug = preg_replace("/\s+/", "-", $slug);

$meta = [
    "company_name" => req("company_name"),
    "slug" => $slug,
    "created_at" => date("Y-m-d H:i:s"),

    "website" => req("website"),
    "description" => req("description"),

    "contact" => [
        "phone" => req("phone"),
        "sms" => req("sms"),
        "email" => req("email"),
        "whatsapp" => req("whatsapp")
    ],

    "promotion" => [
        "allow_social_share" => isset($_POST['promo_social']),
        "allow_featured" => isset($_POST['promo_featured']),
    ],

    "categories" => isset($_POST['categories']) ? $_POST['categories'] : [],

    "other_data" => [
        "client_ip" => $_SERVER['REMOTE_ADDR'] ?? null,
        "user_agent" => $_SERVER['HTTP_USER_AGENT'] ?? null,
        "php_session" => session_id(),
        "server_timestamp" => microtime(true)
    ]
];

/**
 * Write metadata JSON file
 */
$savePath = $metaBase . $slug . ".json";
$saved = file_put_contents($savePath, json_encode($meta, JSON_PRETTY_PRINT));

if (!$saved) {
    echo json_encode([
        "success" => false,
        "message" => "Failed to save metadata"
    ]);
    exit;
}

/**
 * Create directories for company
 */
if (function_exists("createCompanyDirectories")) {
    createCompanyDirectories($slug, $meta["categories"]);
}

echo json_encode([
    "success" => true,
    "message" => "Company registered successfully",
    "slug" => $slug,
    "saved_to" => $savePath
]);
exit;
