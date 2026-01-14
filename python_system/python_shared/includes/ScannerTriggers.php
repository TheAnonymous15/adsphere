<?php
/********************************************
 * Event-Driven Ad Scanner Triggers
 *
 * Call these hooks from your application when ads are:
 * - Created
 * - Updated
 * - Reported by users
 *
 * This ensures immediate scanning of new/modified content
 * without waiting for the next scheduled scan.
 ********************************************/

class ScannerTriggers {

    private static $scanner = null;

    /**
     * Get scanner instance (lazy loading)
     */
    private static function getScanner() {
        if (self::$scanner === null) {
            require_once __DIR__ . '/RealTimeAdScanner.php';
            self::$scanner = new HighPerformanceAdScanner();
        }
        return self::$scanner;
    }

    /**
     * Trigger scan when a NEW ad is created
     *
     * Call this from your ad creation handler:
     * ScannerTriggers::onAdCreated($adId);
     *
     * @param string $adId The new ad ID
     * @param bool $async Whether to scan asynchronously
     * @return array Scan result
     */
    public static function onAdCreated($adId, $async = true) {
        $scanner = self::getScanner();

        if ($async && $scanner->isRemoteServiceAvailable()) {
            // Enqueue for async processing with HIGH priority
            return $scanner->enqueueAd($adId, 'high');
        }

        // Synchronous scan
        return $scanner->scanSingle($adId);
    }

    /**
     * Trigger scan when an ad is UPDATED
     *
     * Call this from your ad update handler:
     * ScannerTriggers::onAdUpdated($adId);
     *
     * @param string $adId The updated ad ID
     * @param bool $async Whether to scan asynchronously
     * @return array Scan result
     */
    public static function onAdUpdated($adId, $async = true) {
        $scanner = self::getScanner();

        if ($async && $scanner->isRemoteServiceAvailable()) {
            // Enqueue for async processing with NORMAL priority
            return $scanner->enqueueAd($adId, 'normal');
        }

        // Synchronous scan
        return $scanner->scanSingle($adId);
    }

    /**
     * Trigger URGENT scan when a user REPORTS an ad
     *
     * Call this from your ad reporting handler:
     * ScannerTriggers::onAdReported($adId, $reportReason);
     *
     * @param string $adId The reported ad ID
     * @param string $reason Report reason
     * @param bool $async Whether to scan asynchronously
     * @return array Scan result
     */
    public static function onAdReported($adId, $reason = '', $async = false) {
        $scanner = self::getScanner();

        // Log the report
        error_log("[ScannerTrigger] Ad reported: {$adId} - Reason: {$reason}");

        if ($async && $scanner->isRemoteServiceAvailable()) {
            // Enqueue for async processing with URGENT priority
            return $scanner->enqueueAd($adId, 'urgent');
        }

        // Synchronous scan (default for reports - we want immediate results)
        return $scanner->scanSingle($adId);
    }

    /**
     * Trigger bulk scan for a company's ads
     *
     * Use when a company is flagged or needs review:
     * ScannerTriggers::onCompanyFlagged($companySlug);
     *
     * @param string $companySlug Company slug
     * @param int $limit Max ads to scan
     * @return array Scan results
     */
    public static function onCompanyFlagged($companySlug, $limit = 100) {
        $scanner = self::getScanner();
        return $scanner->scanByCompany($companySlug, $limit);
    }

    /**
     * Trigger bulk scan for a category
     *
     * Use when a category needs review:
     * ScannerTriggers::onCategoryReview($categorySlug);
     *
     * @param string $categorySlug Category slug
     * @param int $limit Max ads to scan
     * @return array Scan results
     */
    public static function onCategoryReview($categorySlug, $limit = 100) {
        $scanner = self::getScanner();
        return $scanner->scanByCategory($categorySlug, $limit);
    }

    /**
     * Bulk enqueue multiple ads
     *
     * @param array $adIds Array of ad IDs
     * @param string $priority Priority level
     * @return array Result
     */
    public static function enqueueBulk($adIds, $priority = 'normal') {
        $scanner = self::getScanner();

        if ($scanner->isRemoteServiceAvailable()) {
            return $scanner->enqueueAds($adIds, $priority);
        }

        // Fallback to synchronous scanning (in batches)
        $results = [];
        foreach (array_chunk($adIds, 10) as $batch) {
            foreach ($batch as $adId) {
                $results[$adId] = $scanner->scanSingle($adId);
            }
        }

        return ['success' => true, 'scanned' => count($results), 'results' => $results];
    }

    /**
     * Check if an ad is clean (cached result)
     *
     * Use this for quick checks without rescanning:
     * if (ScannerTriggers::isAdClean($adId)) { ... }
     *
     * @param string $adId Ad ID
     * @return bool|null True if clean, false if flagged, null if not cached
     */
    public static function isAdClean($adId) {
        require_once __DIR__ . '/../database/Database.php';
        $db = Database::getInstance();

        $result = $db->queryOne(
            "SELECT is_clean FROM ad_scan_cache WHERE ad_id = ?",
            [$adId]
        );

        if ($result === null) {
            return null; // Not cached
        }

        return (bool) $result['is_clean'];
    }

    /**
     * Get cached scan result for an ad
     *
     * @param string $adId Ad ID
     * @return array|null Cached result or null
     */
    public static function getCachedResult($adId) {
        require_once __DIR__ . '/../database/Database.php';
        $db = Database::getInstance();

        $result = $db->queryOne(
            "SELECT scan_result, last_scanned FROM ad_scan_cache WHERE ad_id = ?",
            [$adId]
        );

        if ($result === null) {
            return null;
        }

        return [
            'result' => json_decode($result['scan_result'], true),
            'last_scanned' => $result['last_scanned'],
            'age_seconds' => time() - $result['last_scanned']
        ];
    }

    /**
     * Force rescan of an ad (invalidate cache)
     *
     * @param string $adId Ad ID
     * @return array Scan result
     */
    public static function forceRescan($adId) {
        require_once __DIR__ . '/../database/Database.php';
        $db = Database::getInstance();

        // Remove from cache
        $db->execute("DELETE FROM ad_scan_cache WHERE ad_id = ?", [$adId]);

        // Scan immediately
        $scanner = self::getScanner();
        return $scanner->scanSingle($adId);
    }
}


/********************************************
 * Example Integration Points
 *
 * Add these calls to your existing code:
 ********************************************

// In your ad creation handler (e.g., upload_ad.php):
// After successfully saving the ad:
$adId = 'AD-123'; // The new ad ID
$scanResult = ScannerTriggers::onAdCreated($adId);
if (!$scanResult['is_clean']) {
    // Handle flagged ad (maybe set status to 'pending_review')
}

// In your ad update handler:
$adId = $_POST['ad_id'];
// After successfully updating the ad:
ScannerTriggers::onAdUpdated($adId);

// In your ad reporting handler:
$adId = $_POST['reported_ad_id'];
$reason = $_POST['report_reason'];
$scanResult = ScannerTriggers::onAdReported($adId, $reason);
// Take action based on scan result

// Quick check before displaying an ad:
$isClean = ScannerTriggers::isAdClean($adId);
if ($isClean === false) {
    // Don't display or show warning
}

********************************************/

