<?php
/********************************************
 * Get Companies API
 * Fetches all companies from database
 ********************************************/

// Suppress warnings
error_reporting(E_ERROR | E_PARSE);
ini_set('display_errors', '0');

// Start output buffering
ob_start();

header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");

require_once __DIR__ . '/../shared/database/Database.php';

$db = Database::getInstance();

try {
    // Fetch all companies
    $companies = $db->query("
        SELECT
            c.*,
            COUNT(DISTINCT a.ad_id) as total_ads,
            SUM(a.views_count) as total_views,
            SUM(a.likes_count) as total_likes,
            SUM(a.favorites_count) as total_favorites
        FROM companies c
        LEFT JOIN ads a ON c.company_slug = a.company_slug
        GROUP BY c.company_slug
        ORDER BY c.created_at DESC
    ");

    // Calculate statistics
    $stats = [
        'total' => count($companies),
        'verified' => 0,
        'inactive' => 0,
        'suspended' => 0,
        'blocked' => 0,
        'active' => 0
    ];

    foreach ($companies as $company) {
        $status = $company['status'] ?? 'active';
        switch ($status) {
            case 'verified':
                $stats['verified']++;
                break;
            case 'inactive':
                $stats['inactive']++;
                break;
            case 'suspended':
                $stats['suspended']++;
                break;
            case 'blocked':
            case 'banned':
                $stats['blocked']++;
                break;
            case 'active':
                $stats['active']++;
                break;
        }
    }

    // Format companies data
    $formattedCompanies = array_map(function($company) {
        return [
            'company_slug' => $company['company_slug'],
            'company_name' => $company['company_name'],
            'email' => $company['email'],
            'phone' => $company['phone'] ?? '',
            'status' => $company['status'] ?? 'active',
            'created_at' => $company['created_at'],
            'total_ads' => (int)($company['total_ads'] ?? 0),
            'total_views' => (int)($company['total_views'] ?? 0),
            'total_likes' => (int)($company['total_likes'] ?? 0),
            'total_favorites' => (int)($company['total_favorites'] ?? 0),
            'categories' => json_decode($company['categories'] ?? '[]', true)
        ];
    }, $companies);

    // Clean output buffer
    ob_end_clean();

    // Return response
    $response = [
        'success' => true,
        'companies' => $formattedCompanies,
        'stats' => $stats,
        'timestamp' => time()
    ];

    echo json_encode($response);

} catch (Exception $e) {
    // Clean output buffer
    ob_end_clean();

    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Failed to fetch companies',
        'message' => $e->getMessage()
    ]);
}

exit;

