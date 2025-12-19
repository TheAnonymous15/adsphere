<?php
/********************************************
 * Scanner API Endpoint
 * Triggers real-time scanning and returns results
 ********************************************/

header('Content-Type: application/json');

require_once __DIR__ . '/../includes/RealTimeAdScanner.php';

try {
    $scanner = new RealTimeAdScanner();

    $action = $_GET['action'] ?? 'scan';

    switch ($action) {
        case 'scan':
            // Run full scan
            $results = $scanner->scanAllAds();
            echo json_encode([
                'success' => true,
                'data' => $results
            ], JSON_PRETTY_PRINT);
            break;

        case 'report':
            // Get latest report
            $report = $scanner->getLatestReport();
            echo json_encode([
                'success' => true,
                'data' => $report ?? ['message' => 'No reports available']
            ], JSON_PRETTY_PRINT);
            break;

        default:
            throw new Exception('Invalid action');
    }

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ], JSON_PRETTY_PRINT);
}

