<?php
/********************************************
 * register_company.php - Backend Handler
 * Hybrid Database System Integration
 * Creates companies in database + file system
 ********************************************/

header('Content-Type: application/json');

// Load database system
require_once __DIR__ . '/../../database/Database.php';

$db = Database::getInstance();

try {
    // Validate request method
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        throw new Exception('Invalid request method');
    }

    // Get form data
    $companyName = trim($_POST['company_name'] ?? '');
    $website = trim($_POST['website'] ?? '');
    $description = trim($_POST['description'] ?? '');

    $phone = trim($_POST['phone'] ?? '');
    $sms = trim($_POST['sms'] ?? '');
    $email = trim($_POST['email'] ?? '');
    $whatsapp = trim($_POST['whatsapp'] ?? '');

    $category = trim($_POST['category'] ?? ''); // Single category

    $promoSocial = isset($_POST['promo_social']) ? 1 : 0;
    $promoFeatured = isset($_POST['promo_featured']) ? 1 : 0;

    // Validate required fields
    if (empty($companyName)) {
        throw new Exception('Company name is required');
    }

    if (empty($category)) {
        throw new Exception('Please select a category');
    }

    // Generate company slug
    $companySlug = strtolower(trim(preg_replace('/[^a-zA-Z0-9]+/', '-', $companyName), '-'));

    // Check if company already exists
    $existing = $db->queryOne("SELECT company_slug FROM companies WHERE company_slug = ?", [$companySlug]);
    if ($existing) {
        throw new Exception('Company with this name already exists');
    }

    // Acquire lock for company creation
    $lock = $db->acquireLock('company_create');
    if (!$lock) {
        throw new Exception('Could not acquire lock. Please try again.');
    }

    try {
        // Start transaction
        $db->beginTransaction();

        // Insert company into database
        $sql = "INSERT INTO companies
                (company_slug, company_name, email, phone, sms, whatsapp, created_at, updated_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')";

        $now = time();
        $params = [
            $companySlug,
            $companyName,
            $email ?: null,
            $phone ?: null,
            $sms ?: null,
            $whatsapp ?: null,
            $now,
            $now
        ];

        $db->execute($sql, $params);

        // Assign single category
        $catSql = "INSERT INTO company_categories (company_slug, category_slug, assigned_at)
                   VALUES (?, ?, ?)";
        $db->execute($catSql, [$companySlug, $category, $now]);

        // Create company metadata file (backward compatibility)
        $metaDir = __DIR__ . '/../metadata/';
        if (!is_dir($metaDir)) {
            mkdir($metaDir, 0755, true);
        }

        $metaData = [
            'company_name' => $companyName,
            'company_slug' => $companySlug,
            'website' => $website,
            'description' => $description,
            'contact' => [
                'phone' => $phone,
                'sms' => $sms,
                'email' => $email,
                'whatsapp' => $whatsapp
            ],
            'category' => $category, // Single category
            'promotions' => [
                'social_media' => $promoSocial,
                'featured' => $promoFeatured
            ],
            'created_at' => $now,
            'status' => 'active'
        ];

        file_put_contents(
            $metaDir . $companySlug . '.json',
            json_encode($metaData, JSON_PRETTY_PRINT),
            LOCK_EX
        );

        // Create company directory in file system for the selected category
        $adsBase = __DIR__ . '/../data/';
        $companyDir = $adsBase . $category . '/' . $companySlug;
        if (!is_dir($companyDir)) {
            mkdir($companyDir, 0755, true);
        }

        // Log activity
        $logDir = __DIR__ . '/../logs/';
        if (!is_dir($logDir)) {
            mkdir($logDir, 0755, true);
        }

        $logFile = $logDir . 'company_' . date('Y-m-d') . '.log';
        $logEntry = sprintf(
            "[%s] COMPANY_CREATED | Slug: %s | Name: %s | Category: %s\n",
            date('Y-m-d H:i:s'),
            $companySlug,
            $companyName,
            $category
        );
        file_put_contents($logFile, $logEntry, FILE_APPEND | LOCK_EX);

        // Commit transaction
        $db->commit();

        // Release lock
        $db->releaseLock($lock);

        // Clear cache
        $db->cacheDelete('all_companies');
        $db->cacheClear('categories_');

        // Success response
        echo json_encode([
            'success' => true,
            'message' => "✅ Company '{$companyName}' registered successfully in {$category}!",
            'company_slug' => $companySlug,
            'category' => $category
        ]);

    } catch (Exception $e) {
        // Rollback transaction
        $db->rollback();

        // Release lock
        if ($lock) {
            $db->releaseLock($lock);
        }

        throw $e;
    }

} catch (Exception $e) {
    // Error response
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'message' => '❌ ' . $e->getMessage()
    ]);
}

