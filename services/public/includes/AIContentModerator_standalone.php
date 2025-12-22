<?php
/********************************************
 * AI Content Moderator - UPGRADED VERSION
 * Now powered by AI/ML Moderation Microservice
 *
 * This class acts as an adapter/wrapper that maintains
 * backward compatibility while using the new production-grade
 * moderation service.
 *
 * Legacy code that calls AIContentModerator will continue
 * to work but will now benefit from:
 * - Advanced ML models (Detoxify, YOLO, etc.)
 * - Real-time processing (50-100ms)
 * - Multi-layer detection (rules + ML)
 * - Comprehensive audit trails
 *
 * @version 2.0.0 (Powered by AdSphere ML Service)
 * @date December 20, 2025
 ********************************************/

class AIContentModerator {

    /**
     * @var ModerationServiceClient The new ML-powered moderation client
     */
    private $moderationClient;

    /**
     * @var bool Whether to use the new service or fall back to legacy
     */
    private $useNewService = true;

    /**
     * @var array Cache for performance
     */
    private $cache = [];

    /**
     * Constructor - Initializes the new moderation service
     */
    public function __construct() {
        // Load the new moderation service client
        $clientPath = __DIR__ . '/../../moderator_services/ModerationServiceClient.php';

        if (file_exists($clientPath)) {
            require_once $clientPath;

            // Initialize with service URL
            $serviceUrl = getenv('MODERATION_SERVICE_URL') ?: 'http://localhost:8002';
            $this->moderationClient = new ModerationServiceClient($serviceUrl, 10);

            // Test if service is available
            if (!$this->testServiceAvailability()) {
                error_log('[AIContentModerator] New service unavailable - using fallback mode');
                $this->useNewService = false;
            }
        } else {
            error_log('[AIContentModerator] ModerationServiceClient not found - using fallback mode');
            $this->useNewService = false;
        }
    }

    /**
     * Test if the new moderation service is available
     * @return bool
     */
    private function testServiceAvailability() {
        try {
            // Quick health check (with short timeout)
            $ch = curl_init($this->moderationClient->getBaseUrl() . '/health');
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_TIMEOUT, 2);
            curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 2);

            $response = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
            curl_close($ch);

            return $httpCode === 200;
        } catch (Exception $e) {
            return false;
        }
    }

    /**
     * Moderate advertisement content using NEW AI/ML SERVICE
     *
     * This method now calls the production-grade moderation microservice
     * which provides:
     * - Multi-layer detection (rule-based + ML)
     * - Advanced toxicity detection (Detoxify model)
     * - Image/video analysis (when models loaded)
     * - Comprehensive scoring and audit trails
     *
     * @param string $title Ad title
     * @param string $description Ad description
     * @param array $imagePaths Array of image file paths
     * @return array Moderation result (backward compatible format)
     */
    public function moderateAd($title, $description, $imagePaths = []) {
        $startTime = microtime(true);

        // Input validation
        if (empty($title) && empty($description)) {
            return [
                'safe' => false,
                'score' => 0,
                'issues' => ['Content is empty'],
                'warnings' => [],
                'flags' => ['empty_content'],
                'confidence' => 100,
                'risk_level' => 'critical',
                'processing_time' => 0
            ];
        }

        // Use new service if available
        if ($this->useNewService && $this->moderationClient) {
            try {
                $result = $this->moderateWithNewService($title, $description, $imagePaths);
                $result['processing_time'] = round((microtime(true) - $startTime) * 1000, 2);
                return $result;
            } catch (Exception $e) {
                error_log('[AIContentModerator] Service error: ' . $e->getMessage());
                // Fall through to legacy fallback
            }
        }

        // Fallback to basic moderation if service unavailable
        return $this->legacyModeration($title, $description, $imagePaths);
    }

    /**
     * Moderate using the NEW AI/ML SERVICE
     * @param string $title
     * @param string $description
     * @param array $imagePaths
     * @return array Backward-compatible result format
     */
    private function moderateWithNewService($title, $description, $imagePaths) {
        // Call the new moderation service
        $imageUrls = [];
        foreach ($imagePaths as $path) {
            if (file_exists($path)) {
                $imageUrls[] = $path;
            }
        }

        $response = $this->moderationClient->moderateRealtime(
            title: $title,
            description: $description,
            imageUrls: $imageUrls,
            videoUrls: [],
            context: [
                'source' => 'AIContentModerator_legacy',
                'category' => 'general'
            ]
        );

        if ($response === null) {
            throw new Exception('Moderation service returned null');
        }

        // Convert new service response to legacy format
        return $this->convertToLegacyFormat($response);
    }

    /**
     * Convert new service response to legacy format
     * Maintains backward compatibility with existing code
     *
     * @param array $newResponse Response from new service
     * @return array Legacy format response
     */
    private function convertToLegacyFormat($newResponse) {
        $decision = $newResponse['decision'] ?? 'review';
        $riskLevel = $newResponse['risk_level'] ?? 'medium';
        $globalScore = $newResponse['global_score'] ?? 0.5;
        $flags = $newResponse['flags'] ?? [];
        $reasons = $newResponse['reasons'] ?? [];

        // Convert global score (0.0-1.0) to legacy score (0-100)
        $legacyScore = round($globalScore * 100);

        // Determine if safe based on decision
        $safe = ($decision === 'approve');

        // Map reasons to issues/warnings
        $issues = [];
        $warnings = [];

        if ($decision === 'block') {
            $issues = $reasons;
        } elseif ($decision === 'review') {
            $warnings = $reasons;
        }

        // Calculate confidence (higher score = higher confidence)
        $confidence = min(95, max(60, $legacyScore));

        return [
            'safe' => $safe,
            'score' => $legacyScore,
            'issues' => $issues,
            'warnings' => $warnings,
            'flags' => $flags,
            'confidence' => $confidence,
            'risk_level' => $riskLevel,
            'processing_time' => $newResponse['processing_time'] ?? 0,
            // Include new service data for enhanced reporting
            '_new_service_data' => [
                'decision' => $decision,
                'global_score' => $globalScore,
                'category_scores' => $newResponse['category_scores'] ?? [],
                'audit_id' => $newResponse['audit_id'] ?? null,
                'ai_sources' => $newResponse['ai_sources'] ?? []
            ]
        ];
    }

    /**
     * LEGACY FALLBACK MODERATION
     * Used only when the new service is unavailable
     * Provides basic safety checks
     *
     * @param string $title
     * @param string $description
     * @param array $imagePaths
     * @return array
     */
    private function legacyModeration($title, $description, $imagePaths) {
        $startTime = microtime(true);

        $result = [
            'safe' => true,
            'score' => 100,
            'issues' => [],
            'warnings' => ['AI service unavailable - using basic fallback moderation'],
            'flags' => [],
            'confidence' => 50, // Low confidence with fallback
            'risk_level' => 'medium', // Conservative default
            'processing_time' => 0
        ];

        $text = strtolower(trim($title . ' ' . $description));

        // Basic keyword checking (critical only)
        $criticalWords = [
            'weapon', 'weapons', 'gun', 'guns', 'rifle', 'knife', 'bomb', 'explosive', 'kill', 'murder',
            'cocaine', 'heroin', 'meth', 'illegal', 'stolen', 'hack', 'firearm', 'ammunition'
        ];

        foreach ($criticalWords as $word) {
            if (strpos($text, $word) !== false) {
                $result['issues'][] = "Critical keyword detected: '$word'";
                $result['flags'][] = 'critical_keyword';
                $result['score'] -= 40;
                $result['risk_level'] = 'critical';
            }
        }

        // Basic spam detection
        if (substr_count($text, '!') > 5 || substr_count($text, '?') > 5) {
            $result['warnings'][] = "Excessive punctuation detected";
            $result['score'] -= 10;
        }

        // Determine safety - be strict!
        $result['safe'] = $result['score'] >= 70 && $result['risk_level'] !== 'critical';
        $result['processing_time'] = round((microtime(true) - $startTime) * 1000, 2);

        return $result;
    }

    /**
     * Check potential copyright issues
     *
     * @param string $title
     * @param string $description
     * @return array
     */
    public function checkCopyrightRisk($title, $description) {
        $text = strtolower($title . ' ' . $description);
        $risk = 'low';
        $concerns = [];

        // Check for brand names (basic list)
        $knownBrands = [
            'nike', 'adidas', 'apple', 'samsung', 'coca-cola', 'pepsi',
            'disney', 'marvel', 'mcdonalds', 'starbucks', 'microsoft',
            'google', 'amazon', 'facebook', 'netflix', 'sony'
        ];

        foreach ($knownBrands as $brand) {
            if (strpos($text, $brand) !== false) {
                $concerns[] = "Mentions brand name: '$brand' - ensure you have authorization";
                $risk = 'medium';
            }
        }

        // Check for copyright symbols
        if (strpos($text, '©') !== false || strpos($text, 'copyright') !== false) {
            $concerns[] = "Contains copyright mentions - verify ownership";
            $risk = 'medium';
        }

        // Check for trademark symbols
        if (strpos($text, '™') !== false || strpos($text, '®') !== false) {
            $concerns[] = "Contains trademark symbols - verify rights";
            $risk = 'medium';
        }

        return [
            'risk' => $risk,
            'concerns' => $concerns
        ];
    }

    /**
     * Generate comprehensive safety report
     *
     * @param array $moderationResult Result from moderateAd()
     * @param array $copyrightResult Result from checkCopyrightRisk()
     * @return array
     */
    public function generateReport($moderationResult, $copyrightResult) {
        $report = [
            'timestamp' => date('Y-m-d H:i:s'),
            'service_version' => '2.0.0 (ML-Powered)',
            'overall_status' => $moderationResult['safe'] ? 'APPROVED' : 'REJECTED',
            'safety_score' => $moderationResult['score'],
            'processing_time' => $moderationResult['processing_time'] . 'ms',
            'issues_found' => count($moderationResult['issues']),
            'warnings_found' => count($moderationResult['warnings']),
            'flags' => $moderationResult['flags'],
            'risk_level' => $moderationResult['risk_level'],
            'confidence' => $moderationResult['confidence'] . '%',
            'copyright_risk' => $copyrightResult['risk'],
            'details' => [
                'content_issues' => $moderationResult['issues'],
                'warnings' => $moderationResult['warnings'],
                'copyright_concerns' => $copyrightResult['concerns']
            ]
        ];

        // Include new service data if available
        if (isset($moderationResult['_new_service_data'])) {
            $report['ml_service'] = [
                'used' => true,
                'decision' => $moderationResult['_new_service_data']['decision'],
                'global_score' => $moderationResult['_new_service_data']['global_score'],
                'category_scores' => $moderationResult['_new_service_data']['category_scores'],
                'audit_id' => $moderationResult['_new_service_data']['audit_id'],
                'ai_models_used' => array_keys($moderationResult['_new_service_data']['ai_sources'] ?? [])
            ];
        } else {
            $report['ml_service'] = [
                'used' => false,
                'reason' => 'Service unavailable - fallback mode used'
            ];
        }

        return $report;
    }

    /**
     * Get service status
     * @return array
     */
    public function getServiceStatus() {
        return [
            'new_service_available' => $this->useNewService,
            'service_url' => $this->useNewService ?
                ($this->moderationClient ? 'http://localhost:8002' : 'N/A') :
                'N/A',
            'version' => '2.0.0',
            'backend' => $this->useNewService ? 'ML Microservice' : 'Legacy Fallback'
        ];
    }
}

