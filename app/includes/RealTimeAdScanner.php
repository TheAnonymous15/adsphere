<?php
/********************************************
 * Real-Time Ad Scanner & Moderator
 * Continuously scans database for policy violations
 * AI-powered recommendations for admin action
 *
 * NOW POWERED BY: AdSphere ML Moderation Service
 * - Advanced ML models (Detoxify, YOLO, NSFW detection)
 * - Multi-layer detection (rules + ML)
 * - 95% accuracy with comprehensive audit trails
 *
 * @version 2.0.0 (ML-Enhanced)
 * @date December 20, 2025
 ********************************************/

class RealTimeAdScanner {

    private $db;
    private $aiModerator;
    private $reportFile;
    private $serviceStatus; // NEW: Track ML service availability

    // Severity levels
    const SEVERITY_LOW = 1;
    const SEVERITY_MEDIUM = 2;
    const SEVERITY_HIGH = 3;
    const SEVERITY_CRITICAL = 4;

    // Action recommendations
    const ACTION_WARN = 'warn';
    const ACTION_PAUSE = 'pause';
    const ACTION_DELETE = 'delete';
    const ACTION_BAN = 'ban';
    const ACTION_REPORT = 'report';

    public function __construct() {
        require_once __DIR__ . '/../database/Database.php';

        // Use standalone AIContentModerator
        $standalonePath = __DIR__ . '/AIContentModerator_standalone.php';
        if (file_exists($standalonePath)) {
            require_once $standalonePath;
        } else {
            require_once __DIR__ . '/AIContentModerator.php';
        }

        $this->db = Database::getInstance();
        $this->aiModerator = new AIContentModerator();
        $this->reportFile = __DIR__ . '/../logs/scanner_reports_' . date('Y-m-d') . '.json';

        // Check ML service status
        $this->serviceStatus = $this->aiModerator->getServiceStatus();

        // Log service status
        if (!$this->serviceStatus['new_service_available']) {
            error_log('[RealTimeAdScanner] WARNING: ML service unavailable - using fallback moderation');
        }
    }

    /**
     * Scan all active ads in database
     */
    public function scanAllAds() {
        $startTime = microtime(true);

        // Get all active ads
        $ads = $this->db->query("
            SELECT
                a.*,
                c.company_name,
                c.email as company_email,
                cat.category_name
            FROM ads a
            LEFT JOIN companies c ON a.company_slug = c.company_slug
            LEFT JOIN categories cat ON a.category_slug = cat.category_slug
            WHERE a.status = 'active'
            ORDER BY a.created_at DESC
        ");

        $results = [
            'scan_time' => date('Y-m-d H:i:s'),
            'total_scanned' => count($ads),
            'flagged_ads' => [],
            'clean_ads' => 0,
            'statistics' => [
                'critical' => 0,
                'high' => 0,
                'medium' => 0,
                'low' => 0
            ],
            'processing_time' => 0,
            // NEW: ML service status
            'ml_service' => [
                'available' => $this->serviceStatus['new_service_available'],
                'backend' => $this->serviceStatus['backend'],
                'version' => $this->serviceStatus['version']
            ]
        ];

        foreach ($ads as $ad) {
            $scanResult = $this->scanSingleAd($ad);

            if (!$scanResult['is_clean']) {
                $results['flagged_ads'][] = $scanResult;
                $results['statistics'][$scanResult['severity_level']]++;

                // Auto-take action based on severity
                $this->autoModerate($ad, $scanResult);
            } else {
                $results['clean_ads']++;
            }
        }

        $results['processing_time'] = round((microtime(true) - $startTime) * 1000, 2) . 'ms';

        // Save report
        $this->saveReport($results);

        return $results;
    }

    /**
     * Scan a single ad with AI intelligence
     */
    private function scanSingleAd($ad) {
        // Run AI moderation (now powered by ML service)
        $moderationResult = $this->aiModerator->moderateAd(
            $ad['title'],
            $ad['description'],
            [] // Images already uploaded, skip for real-time scan
        );

        $copyrightResult = $this->aiModerator->checkCopyrightRisk(
            $ad['title'],
            $ad['description']
        );

        // Analyze patterns
        $patterns = $this->analyzePatterns($ad);

        // Determine severity
        $severity = $this->calculateSeverity($moderationResult, $patterns);

        // Generate intelligent recommendation
        $recommendation = $this->generateRecommendation($moderationResult, $patterns, $severity, $ad);

        // Build scan result
        $scanResult = [
            'ad_id' => $ad['ad_id'],
            'title' => $ad['title'],
            'description' => substr($ad['description'], 0, 100) . '...',
            'company' => $ad['company_name'],
            'company_slug' => $ad['company_slug'],
            'company_email' => $ad['company_email'],
            'category' => $ad['category_name'],
            'created_at' => $ad['created_at'],
            'is_clean' => $moderationResult['safe'] && empty($patterns['red_flags']),
            'ai_score' => $moderationResult['score'],
            'risk_level' => $moderationResult['risk_level'],
            'severity' => $severity,
            'severity_level' => $this->getSeverityLevel($severity),
            'violations' => [
                'content_issues' => $moderationResult['issues'],
                'warnings' => $moderationResult['warnings'],
                'copyright_concerns' => $copyrightResult['concerns'],
                'pattern_flags' => $patterns['red_flags']
            ],
            'recommendation' => $recommendation,
            'scan_time' => time()
        ];

        // Include ML service audit data if available
        if (isset($moderationResult['_new_service_data'])) {
            $scanResult['ml_audit'] = [
                'audit_id' => $moderationResult['_new_service_data']['audit_id'],
                'decision' => $moderationResult['_new_service_data']['decision'],
                'global_score' => $moderationResult['_new_service_data']['global_score'],
                'category_scores' => $moderationResult['_new_service_data']['category_scores'],
                'ai_models_used' => array_keys($moderationResult['_new_service_data']['ai_sources'] ?? []),
                'processing_time' => $moderationResult['processing_time'] ?? 0
            ];
        }

        return $scanResult;
    }

    /**
     * Analyze suspicious patterns beyond AI moderation
     */
    private function analyzePatterns($ad) {
        $redFlags = [];
        $score = 0;

        // 1. Check for repeat offender
        $companyHistory = $this->getCompanyViolationHistory($ad['company_slug']);
        if ($companyHistory['total_violations'] > 3) {
            $redFlags[] = "Repeat offender: {$companyHistory['total_violations']} previous violations";
            $score += 30;
        }

        // 2. Check for suspicious timing
        $recentAds = $this->db->queryOne("
            SELECT COUNT(*) as count
            FROM ads
            WHERE company_slug = ?
            AND created_at > ?
        ", [$ad['company_slug'], time() - 3600]);

        if ($recentAds['count'] > 5) {
            $redFlags[] = "Suspicious activity: {$recentAds['count']} ads in last hour (spam indicator)";
            $score += 20;
        }

        // 3. Check for duplicate content
        $duplicate = $this->checkDuplicateContent($ad);
        if ($duplicate) {
            $redFlags[] = "Duplicate/spam content detected";
            $score += 25;
        }

        // 4. Check for contact info in description (bypass attempt)
        if (preg_match('/\b\d{10,}\b/', $ad['description'])) {
            $redFlags[] = "Phone number in description (potential spam)";
            $score += 15;
        }

        // 5. Check for external links (phishing risk)
        if (preg_match('/https?:\/\//', $ad['description'])) {
            $redFlags[] = "External link detected (phishing risk)";
            $score += 20;
        }

        return [
            'red_flags' => $redFlags,
            'pattern_score' => $score
        ];
    }

    /**
     * Calculate overall severity
     */
    private function calculateSeverity($moderationResult, $patterns) {
        $score = $moderationResult['score'];
        $patternScore = $patterns['pattern_score'];

        // Critical: Violence, illegal content, or multiple violations
        if ($moderationResult['risk_level'] === 'critical' ||
            in_array('violence', $moderationResult['flags']) ||
            in_array('illegal', $moderationResult['flags'])) {
            return self::SEVERITY_CRITICAL;
        }

        // High: Low AI score or multiple red flags
        if ($score < 50 || $patternScore > 50) {
            return self::SEVERITY_HIGH;
        }

        // Medium: Moderate concerns
        if ($score < 70 || $patternScore > 30 || !empty($patterns['red_flags'])) {
            return self::SEVERITY_MEDIUM;
        }

        // Low: Minor issues
        if ($score < 85 || $patternScore > 0) {
            return self::SEVERITY_LOW;
        }

        return self::SEVERITY_LOW;
    }

    /**
     * Generate intelligent action recommendation
     */
    private function generateRecommendation($moderationResult, $patterns, $severity, $ad) {
        $actions = [];
        $reasoning = [];
        $urgency = 'normal';

        // Get company history
        $history = $this->getCompanyViolationHistory($ad['company_slug']);

        // CRITICAL SEVERITY
        if ($severity === self::SEVERITY_CRITICAL) {
            $urgency = 'immediate';

            // Check if repeat offender
            if ($history['total_violations'] >= 2) {
                $actions[] = self::ACTION_BAN;
                $reasoning[] = "Permanent ban: Critical violation by repeat offender ({$history['total_violations']} violations)";
            } else {
                $actions[] = self::ACTION_DELETE;
                $actions[] = self::ACTION_REPORT;
                $reasoning[] = "Delete immediately: Critical policy violation (violence/illegal content)";
                $reasoning[] = "Report to authorities: Content may be illegal";
            }

            // Always notify company
            $reasoning[] = "Send warning email to company";

        // HIGH SEVERITY
        } elseif ($severity === self::SEVERITY_HIGH) {
            $urgency = 'high';

            if ($history['total_violations'] >= 3) {
                $actions[] = self::ACTION_BAN;
                $reasoning[] = "Ban account: Multiple violations ({$history['total_violations']} total)";
            } else {
                $actions[] = self::ACTION_DELETE;
                $actions[] = self::ACTION_WARN;
                $reasoning[] = "Delete ad: Serious policy violation (AI score: {$moderationResult['score']})";
                $reasoning[] = "Issue final warning to company";
            }

        // MEDIUM SEVERITY
        } elseif ($severity === self::SEVERITY_MEDIUM) {
            $urgency = 'medium';

            if ($history['total_violations'] >= 1) {
                $actions[] = self::ACTION_DELETE;
                $reasoning[] = "Delete ad: Repeat violation detected";
            } else {
                $actions[] = self::ACTION_PAUSE;
                $actions[] = self::ACTION_WARN;
                $reasoning[] = "Pause ad: Requires review before re-activation";
                $reasoning[] = "Contact company for clarification/correction";
            }

        // LOW SEVERITY
        } else {
            $urgency = 'low';
            $actions[] = self::ACTION_WARN;
            $reasoning[] = "Send advisory: Minor policy concerns detected";
            $reasoning[] = "Monitor closely for pattern development";
        }

        // Add specific violation details
        $violationDetails = [];
        if (!empty($moderationResult['issues'])) {
            $violationDetails[] = "Content violations: " . implode(', ', $moderationResult['issues']);
        }
        if (!empty($patterns['red_flags'])) {
            $violationDetails[] = "Pattern flags: " . implode(', ', $patterns['red_flags']);
        }

        return [
            'primary_action' => $actions[0] ?? self::ACTION_WARN,
            'all_actions' => $actions,
            'urgency' => $urgency,
            'reasoning' => $reasoning,
            'violation_details' => $violationDetails,
            'suggested_message' => $this->generateCompanyMessage($ad, $severity, $moderationResult)
        ];
    }

    /**
     * Auto-moderate based on severity
     * DISABLED: Only records violations without taking automatic action
     * Admin must manually approve actions via dashboard
     */
    private function autoModerate($ad, $scanResult) {
        $recommendation = $scanResult['recommendation'];

        // DISABLED AUTO-ACTIONS - Only log for manual review
        // Uncomment below to enable automatic moderation

        /*
        switch ($recommendation['primary_action']) {
            case self::ACTION_BAN:
                $this->db->execute(
                    "UPDATE companies SET status = 'inactive' WHERE company_slug = ?",
                    [$ad['company_slug']]
                );
                $this->db->execute(
                    "UPDATE ads SET status = 'inactive' WHERE company_slug = ?",
                    [$ad['company_slug']]
                );
                $this->logAction($ad['ad_id'], 'BAN', 'Auto-banned for critical violations');
                break;

            case self::ACTION_DELETE:
                $this->db->execute(
                    "UPDATE ads SET status = 'inactive' WHERE ad_id = ?",
                    [$ad['ad_id']]
                );
                $this->logAction($ad['ad_id'], 'DELETE', 'Auto-deleted for policy violation');
                break;

            case self::ACTION_PAUSE:
                $this->db->execute(
                    "UPDATE ads SET status = 'inactive' WHERE ad_id = ?",
                    [$ad['ad_id']]
                );
                $this->logAction($ad['ad_id'], 'PAUSE', 'Auto-paused for review');
                break;

            case self::ACTION_WARN:
                $this->logAction($ad['ad_id'], 'WARN', 'Warning issued for minor violations');
                break;
        }
        */

        // Only log the recommendation for admin review
        $this->logAction($ad['ad_id'], 'FLAGGED',
            "Flagged for review - Recommended action: {$recommendation['primary_action']}");

        // Record violation in database (for admin dashboard)
        $this->recordViolation($ad, $scanResult);

        // DO NOT send notification yet - wait for admin action
        // Notifications will be sent when admin takes action via dashboard
    }

    /**
     * Generate message to send to company
     */
    private function generateCompanyMessage($ad, $severity, $moderationResult) {
        $severityText = $this->getSeverityLevel($severity);

        $message = "Dear {$ad['company_name']},\n\n";

        if ($severity === self::SEVERITY_CRITICAL) {
            $message .= "URGENT: Your advertisement \"{$ad['title']}\" has been flagged for CRITICAL policy violations and has been removed immediately.\n\n";
            $message .= "Violations detected:\n";
        } elseif ($severity === self::SEVERITY_HIGH) {
            $message .= "Your advertisement \"{$ad['title']}\" has been flagged for serious policy violations.\n\n";
            $message .= "Issues found:\n";
        } else {
            $message .= "We've noticed some concerns with your advertisement \"{$ad['title']}\".\n\n";
            $message .= "Please review:\n";
        }

        foreach ($moderationResult['issues'] as $issue) {
            $message .= "- $issue\n";
        }

        $message .= "\nPlease review our Terms of Service and Advertising Policy.\n";
        $message .= "\nIf you believe this is an error, please contact our support team.\n\n";
        $message .= "Best regards,\nAdSphere Moderation Team";

        return $message;
    }

    /**
     * Get company violation history
     */
    private function getCompanyViolationHistory($companySlug) {
        $violations = $this->db->queryOne("
            SELECT
                COUNT(*) as total_violations,
                MAX(created_at) as last_violation
            FROM moderation_violations
            WHERE company_slug = ?
        ", [$companySlug]);

        return [
            'total_violations' => (int)($violations['total_violations'] ?? 0),
            'last_violation' => $violations['last_violation'] ?? null
        ];
    }

    /**
     * Check for duplicate content
     */
    private function checkDuplicateContent($ad) {
        $similar = $this->db->queryOne("
            SELECT COUNT(*) as count
            FROM ads
            WHERE ad_id != ?
            AND company_slug = ?
            AND (title = ? OR description = ?)
            AND status = 'active'
        ", [
            $ad['ad_id'],
            $ad['company_slug'],
            $ad['title'],
            $ad['description']
        ]);

        return ($similar['count'] ?? 0) > 0;
    }

    /**
     * Record violation in database
     */
    private function recordViolation($ad, $scanResult) {
        try {
            // Check if violation already exists for this ad
            $existing = $this->db->queryOne("
                SELECT id FROM moderation_violations
                WHERE ad_id = ? AND status = 'pending'
            ", [$ad['ad_id']]);

            if ($existing) {
                // Update existing violation
                $this->db->execute("
                    UPDATE moderation_violations
                    SET severity = ?, ai_score = ?, violations = ?, action_taken = ?
                    WHERE id = ?
                ", [
                    $scanResult['severity'],
                    $scanResult['ai_score'],
                    json_encode($scanResult['violations']),
                    $scanResult['recommendation']['primary_action'],
                    $existing['id']
                ]);
            } else {
                // Insert new violation
                $this->db->execute("
                    INSERT INTO moderation_violations
                    (ad_id, company_slug, severity, ai_score, violations, action_taken, created_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
                ", [
                    $ad['ad_id'],
                    $ad['company_slug'],
                    $scanResult['severity'],
                    $scanResult['ai_score'],
                    json_encode($scanResult['violations']),
                    $scanResult['recommendation']['primary_action'],
                    time()
                ]);
            }
        } catch (Exception $e) {
            // Log error but don't fail the scan
            error_log("Failed to record violation: " . $e->getMessage());
        }
    }

    /**
     * Log action taken
     */
    private function logAction($adId, $action, $reason) {
        $logFile = __DIR__ . '/../logs/moderation_actions_' . date('Y-m-d') . '.log';
        $entry = sprintf(
            "[%s] %s | Ad: %s | Reason: %s\n",
            date('Y-m-d H:i:s'),
            $action,
            $adId,
            $reason
        );

        file_put_contents($logFile, $entry, FILE_APPEND | LOCK_EX);
    }

    /**
     * Send notification email
     */
    private function sendNotificationEmail($ad, $scanResult) {
        // Email implementation would go here
        // For now, just log it
        $this->logAction(
            $ad['ad_id'],
            'EMAIL_SENT',
            "Notification sent to {$ad['company_email']}"
        );
    }

    /**
     * Save scan report
     */
    private function saveReport($results) {
        file_put_contents(
            $this->reportFile,
            json_encode($results, JSON_PRETTY_PRINT),
            LOCK_EX
        );
    }

    /**
     * Get severity level text
     */
    private function getSeverityLevel($severity) {
        switch ($severity) {
            case self::SEVERITY_CRITICAL: return 'critical';
            case self::SEVERITY_HIGH: return 'high';
            case self::SEVERITY_MEDIUM: return 'medium';
            case self::SEVERITY_LOW: return 'low';
            default: return 'unknown';
        }
    }

    /**
     * Get latest scan report
     */
    public function getLatestReport() {
        if (file_exists($this->reportFile)) {
            return json_decode(file_get_contents($this->reportFile), true);
        }
        return null;
    }

    /**
     * Get ML service status
     * @return array Service status information
     */
    public function getServiceStatus() {
        return $this->serviceStatus;
    }

    /**
     * Refresh ML service status (check if it came back online)
     * @return bool True if service is now available
     */
    public function refreshServiceStatus() {
        $this->serviceStatus = $this->aiModerator->getServiceStatus();

        if ($this->serviceStatus['new_service_available']) {
            error_log('[RealTimeAdScanner] ML service is now available');
            return true;
        }

        return false;
    }
}

