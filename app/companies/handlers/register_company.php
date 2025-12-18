<?php
header("Content-Type: application/json");
ini_set("display_errors", 1);
error_reporting(E_ALL);

/**
 * Quick helpers
 */
function req($key, $default = null) {
    return isset($_POST[$key]) ? trim($_POST[$key]) : $default;
}

if ($_SERVER["REQUEST_METHOD"] !== "POST") {
    echo json_encode([
        "success" => false,
        "message" => "Invalid request method"
    ]);
    exit;
}

if (!req("company_name")) {
    echo json_encode([
        "success" => false,
        "message" => "Company name required"
    ]);
    exit;
}

/**
 * Build slug
 */
$slug = strtolower(req("company_name"));
$slug = preg_replace("/[^a-z0-9\s-]/", "", $slug);
$slug = preg_replace("/\s+/", "-", $slug);

/**
 * Build metadata array
 */
$categories = isset($_POST["categories"]) ? $_POST["categories"] : [];

$metadata = [
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
        "allow_social_share" => isset($_POST["promo_social"]),
        "allow_featured" => isset($_POST["promo_featured"]),
    ],

    "categories" => $categories,

    "other_data" => [
        "client_ip" => $_SERVER["REMOTE_ADDR"] ?? null,
        "user_agent" => $_SERVER["HTTP_USER_AGENT"] ?? null,
        "timestamp_micro" => microtime(true)
    ]
];

/**
 * Save metadata file
 */
$metaBase = __DIR__ . "/../metadata/";

if (!is_dir($metaBase)) mkdir($metaBase, 0775, true);

$savePath = $metaBase . $slug . ".json";
$saved = file_put_contents($savePath, json_encode($metadata, JSON_PRETTY_PRINT));

if (!$saved) {
    echo json_encode([
        "success" => false,
        "message" => "Failed writing metadata"
    ]);
    exit;
}

/**
 * Create company folders
 */
$dataBase = __DIR__ . "/../data/";
if (!is_dir($dataBase)) mkdir($dataBase, 0775, true);

foreach ($categories as $cat) {

    // sanitize category string
    $cat = preg_replace("/[^a-z0-9\-]/i", "", $cat);

    $path = $dataBase . $cat . "/" . $slug;
    if (!is_dir($path)) mkdir($path, 0775, true);
}

echo json_encode([
    "success" => true,
    "message" => "Company registered successfully",
    "slug" => $slug,
    "written_meta" => $savePath
]);

exit;
