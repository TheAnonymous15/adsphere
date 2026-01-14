<?php
/********************************************
 * get_ads.php - Hybrid Database System
 * Fetches ads from SQLite database
 ********************************************/

// Suppress all warnings and notices
error_reporting(E_ERROR | E_PARSE);
ini_set('display_errors', '0');

// Start output buffering to catch any stray output
ob_start();

header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");

// Load database system
require_once __DIR__ . '/../shared/database/Database.php';
require_once __DIR__ . '/../shared/database/AdModel.php';

$db = Database::getInstance();
$adModel = new AdModel();

// Get parameters
$page = max(1, intval($_GET["page"] ?? 1));
$q = trim($_GET["q"] ?? "");
$category = trim($_GET["category"] ?? "");
$company = trim($_GET["company"] ?? ""); // Add company filter
$sort = $_GET["sort"] ?? "date";
$pageSize = 12;

try {
    // Build SQL query
    $sql = "SELECT
                a.*,
                c.category_name,
                comp.company_name
            FROM ads a
            LEFT JOIN categories c ON a.category_slug = c.category_slug
            LEFT JOIN companies comp ON a.company_slug = comp.company_slug
            WHERE a.status = 'active'";

    $params = [];

    // Company filter (for my_ads.php and dashboard)
    if (!empty($company)) {
        $sql .= " AND a.company_slug = ?";
        $params[] = $company;
    }

    // Search filter
    if (!empty($q)) {
        $sql .= " AND (a.title LIKE ? OR a.description LIKE ?)";
        $searchTerm = "%$q%";
        $params[] = $searchTerm;
        $params[] = $searchTerm;
    }

    // Category filter
    if (!empty($category)) {
        $sql .= " AND a.category_slug = ?";
        $params[] = $category;
    }

    // Sorting
    switch ($sort) {
        case 'views':
            $sql .= " ORDER BY a.views_count DESC, a.created_at DESC";
            break;
        case 'favs':
            $sql .= " ORDER BY a.favorites_count DESC, a.created_at DESC";
            break;
        case 'ai':
            $sql .= " ORDER BY a.likes_count DESC, a.views_count DESC, a.created_at DESC";
            break;
        case 'date':
        default:
            $sql .= " ORDER BY a.created_at DESC";
            break;
    }

    // Get total count
    $countSql = str_replace('SELECT a.*, c.category_name, comp.company_name', 'SELECT COUNT(*) as total',
                           substr($sql, 0, strpos($sql, 'ORDER BY') ?: strlen($sql)));

    $totalResult = $db->queryOne($countSql, $params);
    $total = $totalResult['total'] ?? 0;

    // Pagination
    $offset = ($page - 1) * $pageSize;
    $sql .= " LIMIT ? OFFSET ?";
    $params[] = $pageSize;
    $params[] = $offset;

    // Execute query
    $ads = $db->query($sql, $params);

    // Format ads for frontend
    $formattedAds = [];
    foreach ($ads as $ad) {
        // Build media path
        $mediaPath = "/services/company/data/" . $ad['media_path'];

        // Parse media files (if multiple)
        $mediaFiles = [];
        if (!empty($ad['media_filename'])) {
            // Check if it's a JSON array or single file
            if (strpos($ad['media_filename'], '[') === 0) {
                $mediaFiles = json_decode($ad['media_filename'], true) ?? [$ad['media_filename']];
            } else {
                $mediaFiles = [$ad['media_filename']];
            }
        }

        // Build full media URLs
        $mediaUrls = array_map(function($file) use ($ad) {
            return "/services/company/data/{$ad['category_slug']}/{$ad['company_slug']}/{$ad['ad_id']}/$file";
        }, $mediaFiles);

        $formattedAds[] = [
            'ad_id' => $ad['ad_id'],
            'title' => $ad['title'],
            'description' => $ad['description'],
            'category' => $ad['category_slug'],
            'category_name' => $ad['category_name'] ?? ucfirst($ad['category_slug']),
            'company' => $ad['company_slug'],
            'company_name' => $ad['company_name'] ?? ucfirst($ad['company_slug']),
            'media' => $mediaUrls[0] ?? '', // Primary media
            'media_files' => $mediaUrls, // All media files
            'media_type' => $ad['media_type'] ?? 'image',
            'timestamp' => $ad['created_at'],
            'views' => (int)($ad['views_count'] ?? 0),
            'likes' => (int)($ad['likes_count'] ?? 0),
            'favorites' => (int)($ad['favorites_count'] ?? 0),
            'contacts' => (int)($ad['contacts_count'] ?? 0),
            'contact' => [
                'phone' => $ad['contact_phone'] ?? '',
                'sms' => $ad['contact_sms'] ?? '',
                'email' => $ad['contact_email'] ?? '',
                'whatsapp' => $ad['contact_whatsapp'] ?? ''
            ]
        ];
    }

    // Return response
    $response = [
        'success' => true,
        'ads' => $formattedAds,
        'page' => $page,
        'pageSize' => $pageSize,
        'total' => $total,
        'totalPages' => ceil($total / $pageSize)
    ];

} catch (Exception $e) {
    http_response_code(500);
    $response = [
        'success' => false,
        'error' => 'Failed to fetch ads',
        'message' => $e->getMessage()
    ];
}

// Clean output buffer
ob_end_clean();

// Output JSON
echo json_encode($response);
exit;
