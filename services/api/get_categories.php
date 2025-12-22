<?php
/********************************************
 * get_categories.php - Hybrid Database System
 * Fetches categories from SQLite database
 ********************************************/

header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");

// Load database system
require_once __DIR__ . '/../shared/database/Database.php';

$db = Database::getInstance();

try {
    // Get all categories from database
    $sql = "SELECT
                c.category_slug,
                c.category_name,
                c.description,
                COUNT(DISTINCT cc.company_slug) as company_count,
                COUNT(DISTINCT a.ad_id) as ad_count
            FROM categories c
            LEFT JOIN company_categories cc ON c.category_slug = cc.category_slug
            LEFT JOIN ads a ON c.category_slug = a.category_slug AND a.status = 'active'
            GROUP BY c.category_slug
            ORDER BY c.category_name";

    $categories = $db->query($sql);

    // Format for frontend
    $formattedCategories = [];
    foreach ($categories as $cat) {
        $formattedCategories[] = [
            'slug' => $cat['category_slug'],
            'name' => $cat['category_name'],
            'description' => $cat['description'] ?? '',
            'company_count' => (int)$cat['company_count'],
            'ad_count' => (int)$cat['ad_count']
        ];
    }

    echo json_encode([
        'success' => true,
        'categories' => $formattedCategories,
        'total' => count($formattedCategories)
    ], JSON_PRETTY_PRINT);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Failed to fetch categories',
        'message' => $e->getMessage()
    ], JSON_PRETTY_PRINT);
}
