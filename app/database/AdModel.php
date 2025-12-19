<?php
/********************************************
 * AdModel.php
 * Handle all ad-related database operations
 * with caching and file locking
 ********************************************/

require_once __DIR__ . '/Database.php';

class AdModel {

    private $db;
    private $adsBasePath;

    public function __construct() {
        $this->db = Database::getInstance();
        $this->adsBasePath = __DIR__ . '/../companies/data/';
    }

    /**
     * Create new ad (with file and database)
     */
    public function createAd($data) {
        $lock = $this->db->acquireLock('ad_create');
        if (!$lock) {
            return ['success' => false, 'error' => 'Could not acquire lock'];
        }

        try {
            $this->db->beginTransaction();

            // Insert into database
            $sql = "INSERT INTO ads
                    (ad_id, company_slug, category_slug, title, description,
                     media_filename, media_type, media_path,
                     contact_phone, contact_sms, contact_email, contact_whatsapp,
                     created_at, updated_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

            $params = [
                $data['ad_id'],
                $data['company_slug'],
                $data['category_slug'],
                $data['title'],
                $data['description'] ?? '',
                $data['media_filename'],
                $data['media_type'],
                $data['media_path'],
                $data['contact_phone'] ?? null,
                $data['contact_sms'] ?? null,
                $data['contact_email'] ?? null,
                $data['contact_whatsapp'] ?? null,
                time(),
                time(),
                $data['status'] ?? 'active'
            ];

            $this->db->execute($sql, $params);

            // Log activity
            $this->logActivity($data['company_slug'], $data['ad_id'], 'upload', [
                'title' => $data['title'],
                'category' => $data['category_slug']
            ]);

            // Clear relevant caches
            $this->db->cacheClear("ads_{$data['company_slug']}");
            $this->db->cacheClear("ads_{$data['category_slug']}");

            $this->db->commit();
            $this->db->releaseLock($lock);

            return ['success' => true, 'ad_id' => $data['ad_id']];

        } catch (Exception $e) {
            $this->db->rollback();
            $this->db->releaseLock($lock);
            return ['success' => false, 'error' => $e->getMessage()];
        }
    }

    /**
     * Get ad by ID
     */
    public function getAd($adId, $useCache = true) {
        if ($useCache) {
            $cached = $this->db->cacheGet("ad_$adId");
            if ($cached) return $cached;
        }

        $sql = "SELECT * FROM ads WHERE ad_id = ? AND status = 'active'";
        $ad = $this->db->queryOne($sql, [$adId]);

        if ($ad && $useCache) {
            $this->db->cacheSet("ad_$adId", $ad, 1800); // 30 minutes
        }

        return $ad;
    }

    /**
     * Get ads by company with pagination
     */
    public function getAdsByCompany($companySlug, $page = 1, $perPage = 20, $useCache = true) {
        $cacheKey = "ads_{$companySlug}_p{$page}_pp{$perPage}";

        if ($useCache) {
            $cached = $this->db->cacheGet($cacheKey);
            if ($cached) return $cached;
        }

        $offset = ($page - 1) * $perPage;

        $sql = "SELECT * FROM ads
                WHERE company_slug = ? AND status = 'active'
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?";

        $ads = $this->db->query($sql, [$companySlug, $perPage, $offset]);

        // Get total count
        $countSql = "SELECT COUNT(*) as total FROM ads
                     WHERE company_slug = ? AND status = 'active'";
        $count = $this->db->queryOne($countSql, [$companySlug])['total'];

        $result = [
            'ads' => $ads,
            'total' => $count,
            'page' => $page,
            'per_page' => $perPage,
            'total_pages' => ceil($count / $perPage)
        ];

        if ($useCache) {
            $this->db->cacheSet($cacheKey, $result, 300); // 5 minutes
        }

        return $result;
    }

    /**
     * Get ads by category
     */
    public function getAdsByCategory($categorySlug, $page = 1, $perPage = 20) {
        $offset = ($page - 1) * $perPage;

        $sql = "SELECT a.*, c.company_name
                FROM ads a
                LEFT JOIN companies c ON a.company_slug = c.company_slug
                WHERE a.category_slug = ? AND a.status = 'active'
                ORDER BY a.created_at DESC
                LIMIT ? OFFSET ?";

        return $this->db->query($sql, [$categorySlug, $perPage, $offset]);
    }

    /**
     * Search ads (full-text search)
     */
    public function searchAds($query, $filters = []) {
        $baseQuery = "
            SELECT a.* FROM ads a
            JOIN ads_fts ON ads_fts.ad_id = a.ad_id
            WHERE ads_fts MATCH ?
        ";

        $params = [$query];

        if (!empty($filters['company'])) {
            $baseQuery .= " AND a.company_slug = ?";
            $params[] = $filters['company'];
        }

        if (!empty($filters['category'])) {
            $baseQuery .= " AND a.category_slug = ?";
            $params[] = $filters['category'];
        }

        $baseQuery .= " ORDER BY rank LIMIT 50";

        return $this->db->query($baseQuery, $params);
    }

    /**
     * Update ad
     */
    public function updateAd($adId, $data) {
        $lock = $this->db->acquireLock("ad_update_$adId");
        if (!$lock) return false;

        $fields = [];
        $params = [];

        $allowedFields = ['title', 'description', 'status', 'scheduled_at', 'expires_at'];

        foreach ($allowedFields as $field) {
            if (isset($data[$field])) {
                $fields[] = "$field = ?";
                $params[] = $data[$field];
            }
        }

        if (empty($fields)) {
            $this->db->releaseLock($lock);
            return false;
        }

        $fields[] = "updated_at = ?";
        $params[] = time();
        $params[] = $adId;

        $sql = "UPDATE ads SET " . implode(', ', $fields) . " WHERE ad_id = ?";
        $result = $this->db->execute($sql, $params);

        // Clear cache
        $this->db->cacheDelete("ad_$adId");

        $this->db->releaseLock($lock);
        return $result;
    }

    /**
     * Delete ad (soft delete)
     */
    public function deleteAd($adId, $companySlug) {
        $lock = $this->db->acquireLock("ad_delete_$adId");
        if (!$lock) return false;

        // Soft delete - set status to inactive
        $sql = "UPDATE ads SET status = 'inactive', updated_at = ? WHERE ad_id = ? AND company_slug = ?";
        $result = $this->db->execute($sql, [time(), $adId, $companySlug]);

        // Log activity
        $this->logActivity($companySlug, $adId, 'delete');

        // Clear cache
        $this->db->cacheDelete("ad_$adId");
        $this->db->cacheClear("ads_$companySlug");

        $this->db->releaseLock($lock);
        return $result;
    }

    /**
     * Increment view count
     */
    public function incrementViews($adId, $deviceFingerprint, $ipAddress, $userAgent) {
        // Record view
        $sql = "INSERT INTO ad_views (ad_id, device_fingerprint, ip_address, user_agent, viewed_at)
                VALUES (?, ?, ?, ?, ?)";
        $this->db->execute($sql, [$adId, $deviceFingerprint, $ipAddress, $userAgent, time()]);

        // Update counter
        $this->db->execute("UPDATE ads SET views_count = views_count + 1 WHERE ad_id = ?", [$adId]);

        // Clear cache
        $this->db->cacheDelete("ad_$adId");
    }

    /**
     * Track reaction (like/dislike/favorite)
     */
    public function trackReaction($adId, $deviceFingerprint, $reactionType) {
        // Use INSERT OR REPLACE to handle duplicates
        $sql = "INSERT OR REPLACE INTO ad_reactions
                (ad_id, device_fingerprint, reaction_type, created_at)
                VALUES (?, ?, ?, ?)";

        $result = $this->db->execute($sql, [$adId, $deviceFingerprint, $reactionType, time()]);

        if ($result) {
            // Update counter
            $field = $reactionType . 's_count';
            $this->db->execute("UPDATE ads SET $field = (
                SELECT COUNT(*) FROM ad_reactions
                WHERE ad_id = ? AND reaction_type = ?
            ) WHERE ad_id = ?", [$adId, $reactionType, $adId]);

            // Clear cache
            $this->db->cacheDelete("ad_$adId");
        }

        return $result;
    }

    /**
     * Track contact method
     */
    public function trackContact($adId, $method, $deviceFingerprint, $ipAddress) {
        $sql = "INSERT INTO ad_contacts (ad_id, contact_method, device_fingerprint, ip_address, contacted_at)
                VALUES (?, ?, ?, ?, ?)";

        $result = $this->db->execute($sql, [$adId, $method, $deviceFingerprint, $ipAddress, time()]);

        if ($result) {
            // Update counter
            $this->db->execute("UPDATE ads SET contacts_count = contacts_count + 1 WHERE ad_id = ?", [$adId]);

            // Clear cache
            $this->db->cacheDelete("ad_$adId");
        }

        return $result;
    }

    /**
     * Get ad analytics
     */
    public function getAdAnalytics($adId) {
        $cacheKey = "analytics_$adId";
        $cached = $this->db->cacheGet($cacheKey);
        if ($cached) return $cached;

        $analytics = [
            'views' => $this->db->queryOne("SELECT COUNT(*) as count FROM ad_views WHERE ad_id = ?", [$adId])['count'],
            'likes' => $this->db->queryOne("SELECT COUNT(*) as count FROM ad_reactions WHERE ad_id = ? AND reaction_type = 'like'", [$adId])['count'],
            'dislikes' => $this->db->queryOne("SELECT COUNT(*) as count FROM ad_reactions WHERE ad_id = ? AND reaction_type = 'dislike'", [$adId])['count'],
            'favorites' => $this->db->queryOne("SELECT COUNT(*) as count FROM ad_reactions WHERE ad_id = ? AND reaction_type = 'favorite'", [$adId])['count'],
            'contacts' => [
                'call' => $this->db->queryOne("SELECT COUNT(*) as count FROM ad_contacts WHERE ad_id = ? AND contact_method = 'call'", [$adId])['count'],
                'sms' => $this->db->queryOne("SELECT COUNT(*) as count FROM ad_contacts WHERE ad_id = ? AND contact_method = 'sms'", [$adId])['count'],
                'email' => $this->db->queryOne("SELECT COUNT(*) as count FROM ad_contacts WHERE ad_id = ? AND contact_method = 'email'", [$adId])['count'],
                'whatsapp' => $this->db->queryOne("SELECT COUNT(*) as count FROM ad_contacts WHERE ad_id = ? AND contact_method = 'whatsapp'", [$adId])['count']
            ]
        ];

        $this->db->cacheSet($cacheKey, $analytics, 600); // 10 minutes
        return $analytics;
    }

    /**
     * Get company analytics
     */
    public function getCompanyAnalytics($companySlug, $days = 30) {
        $since = time() - ($days * 86400);

        return [
            'total_ads' => $this->db->queryOne("SELECT COUNT(*) as count FROM ads WHERE company_slug = ?", [$companySlug])['count'],
            'active_ads' => $this->db->queryOne("SELECT COUNT(*) as count FROM ads WHERE company_slug = ? AND status = 'active'", [$companySlug])['count'],
            'total_views' => $this->db->queryOne("SELECT SUM(views_count) as total FROM ads WHERE company_slug = ?", [$companySlug])['total'] ?? 0,
            'recent_views' => $this->db->queryOne("SELECT COUNT(*) as count FROM ad_views v JOIN ads a ON v.ad_id = a.ad_id WHERE a.company_slug = ? AND v.viewed_at > ?", [$companySlug, $since])['count'],
            'total_contacts' => $this->db->queryOne("SELECT COUNT(*) as count FROM ad_contacts c JOIN ads a ON c.ad_id = a.ad_id WHERE a.company_slug = ?", [$companySlug])['count'],
            'recent_contacts' => $this->db->queryOne("SELECT COUNT(*) as count FROM ad_contacts c JOIN ads a ON c.ad_id = a.ad_id WHERE a.company_slug = ? AND c.contacted_at > ?", [$companySlug, $since])['count']
        ];
    }

    /**
     * Get categories for company
     */
    public function getCompanyCategories($companySlug) {
        $cacheKey = "categories_$companySlug";
        $cached = $this->db->cacheGet($cacheKey);
        if ($cached) return $cached;

        $sql = "SELECT c.* FROM categories c
                JOIN company_categories cc ON c.category_slug = cc.category_slug
                WHERE cc.company_slug = ?
                ORDER BY c.category_name";

        $categories = $this->db->query($sql, [$companySlug]);

        $this->db->cacheSet($cacheKey, $categories, 3600); // 1 hour
        return $categories;
    }

    /**
     * Log activity
     */
    private function logActivity($companySlug, $adId, $action, $details = []) {
        $sql = "INSERT INTO activity_log (company_slug, ad_id, action, details, ip_address, created_at)
                VALUES (?, ?, ?, ?, ?, ?)";

        $params = [
            $companySlug,
            $adId,
            $action,
            json_encode($details),
            $_SERVER['REMOTE_ADDR'] ?? null,
            time()
        ];

        return $this->db->execute($sql, $params);
    }

    /**
     * Get full file path for media
     */
    public function getMediaPath($ad) {
        return $this->adsBasePath . $ad['media_path'];
    }
}

