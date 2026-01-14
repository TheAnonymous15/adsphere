<?php
/********************************************
 * Get Companies API
 * Fetches all companies from database AND file system
 ********************************************/

header("Content-Type: application/json");
header("Access-Control-Allow-Origin: *");

require_once __DIR__ . '/../shared/database/Database.php';

try {
    $db = Database::getInstance();

    // Fetch companies from database
    $dbCompanies = $db->query("
        SELECT
            c.*,
            COUNT(DISTINCT a.ad_id) as total_ads,
            COALESCE(SUM(a.views_count), 0) as total_views,
            COALESCE(SUM(a.likes_count), 0) as total_likes,
            COALESCE(SUM(a.favorites_count), 0) as total_favorites
        FROM companies c
        LEFT JOIN ads a ON c.company_slug = a.company_slug
        GROUP BY c.company_slug
        ORDER BY c.created_at DESC
    ");

    // Index database companies by slug for easy lookup
    $companiesBySlug = [];
    foreach ($dbCompanies as $company) {
        $companiesBySlug[$company['company_slug']] = $company;
    }

    // Also fetch from file system (for any companies not in database)
    $companiesDir = __DIR__ . '/../company/data/companies/';
    if (is_dir($companiesDir)) {
        $dirs = scandir($companiesDir);
        foreach ($dirs as $dir) {
            if ($dir === '.' || $dir === '..') continue;

            $companyJsonPath = $companiesDir . $dir . '/company.json';
            if (file_exists($companyJsonPath)) {
                $fileData = json_decode(file_get_contents($companyJsonPath), true);
                if ($fileData && !isset($companiesBySlug[$dir])) {
                    // Company exists in file system but not in database - add it
                    $companiesBySlug[$dir] = [
                        'company_slug' => $fileData['company_slug'] ?? $dir,
                        'company_name' => $fileData['company_name'] ?? $dir,
                        'email' => $fileData['email'] ?? '',
                        'phone' => $fileData['phone'] ?? '',
                        'status' => $fileData['status'] ?? 'active',
                        'created_at' => is_numeric($fileData['created_at']) ? $fileData['created_at'] : strtotime($fileData['created_at'] ?? 'now'),
                        'total_ads' => 0,
                        'total_views' => 0,
                        'total_likes' => 0,
                        'total_favorites' => 0
                    ];

                    // Sync to database
                    try {
                        $now = time();
                        $createdAt = is_numeric($fileData['created_at']) ? $fileData['created_at'] : strtotime($fileData['created_at'] ?? 'now');
                        $db->execute(
                            "INSERT OR IGNORE INTO companies (company_slug, company_name, email, phone, created_at, updated_at, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            [
                                $fileData['company_slug'] ?? $dir,
                                $fileData['company_name'] ?? $dir,
                                $fileData['email'] ?? '',
                                $fileData['phone'] ?? '',
                                $createdAt,
                                $now,
                                $fileData['status'] ?? 'active'
                            ]
                        );
                    } catch (Exception $syncErr) {
                        // Ignore sync errors
                    }
                }
            }
        }
    }

    // Convert to indexed array
    $companies = array_values($companiesBySlug);

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
            default:
                $stats['active']++;
                break;
        }
    }

    // Format companies data
    $formattedCompanies = array_map(function($company) {
        return [
            'company_slug' => $company['company_slug'],
            'company_name' => $company['company_name'],
            'email' => $company['email'] ?? '',
            'phone' => $company['phone'] ?? '',
            'status' => $company['status'] ?? 'active',
            'created_at' => $company['created_at'],
            'total_ads' => (int)($company['total_ads'] ?? 0),
            'total_views' => (int)($company['total_views'] ?? 0),
            'total_likes' => (int)($company['total_likes'] ?? 0),
            'total_favorites' => (int)($company['total_favorites'] ?? 0)
        ];
    }, $companies);

    // Return response
    echo json_encode([
        'success' => true,
        'companies' => $formattedCompanies,
        'stats' => $stats,
        'timestamp' => time()
    ]);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => 'Failed to fetch companies',
        'message' => $e->getMessage()
    ]);
}


