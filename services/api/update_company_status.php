<?php
/********************************************
 * Update Company Status API
 * Handles company status changes
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
    // Get POST data
    $companySlug = $_POST['company_slug'] ?? '';
    $action = $_POST['action'] ?? '';

    if (empty($companySlug) || empty($action)) {
        throw new Exception('Missing required parameters');
    }

    // Map actions to statuses
    $statusMap = [
        'suspend' => 'suspended',
        'activate' => 'active',
        'block' => 'blocked',
        'unblock' => 'active',
        'verify' => 'verified'
    ];

    if (!isset($statusMap[$action])) {
        throw new Exception('Invalid action');
    }

    $newStatus = $statusMap[$action];

    // Update company status
    $db->execute(
        "UPDATE companies SET status = ? WHERE company_slug = ?",
        [$newStatus, $companySlug]
    );

    // If blocking, also deactivate all their ads
    if ($action === 'block') {
        $db->execute(
            "UPDATE ads SET status = 'inactive' WHERE company_slug = ?",
            [$companySlug]
        );
    }

    // If activating/unblocking, reactivate their ads
    if ($action === 'activate' || $action === 'unblock') {
        $db->execute(
            "UPDATE ads SET status = 'active' WHERE company_slug = ?",
            [$companySlug]
        );
    }

    // Clean output buffer
    ob_end_clean();

    // Return response
    echo json_encode([
        'success' => true,
        'message' => "Company {$action}d successfully",
        'company_slug' => $companySlug,
        'new_status' => $newStatus
    ]);

} catch (Exception $e) {
    // Clean output buffer
    ob_end_clean();

    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}

exit;

