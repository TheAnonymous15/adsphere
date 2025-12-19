<?php
/********************************************
 * AI Content Moderator
 * Intelligent content scanning for ads
 * Checks text, images for policy violations
 ********************************************/

class AIContentModerator {

    private $violentWords = [
        'kill', 'murder', 'attack', 'bomb', 'weapon', 'gun', 'knife', 'violence',
        'hurt', 'harm', 'death', 'assault', 'terrorist', 'destroy', 'explosive',
        'shoot', 'stab', 'blow up', 'execution', 'massacre', 'torture', 'combat'
    ];

    // Word variations to catch creative spelling
    private $violentVariations = [
        'k1ll', 'murd3r', 'b0mb', 'we4pon', 'att@ck', 'de@th'
    ];

    private $abusiveWords = [
        'hate', 'racist', 'discriminate', 'slur', 'offensive', 'insult',
        'derogatory', 'bigot', 'prejudice', 'harassment', 'bully'
    ];

    private $illegalKeywords = [
        'drugs', 'cocaine', 'heroin', 'meth', 'illegal', 'counterfeit',
        'stolen', 'hack', 'crack', 'pirated', 'scam', 'fraud', 'fake',
        'laundering', 'contraband', 'smuggle', 'blackmail', 'extort'
    ];

    // Suspicious phrase patterns
    private $suspiciousPatterns = [
        'no questions asked', 'cash only', 'untraceable', 'off the books',
        'under the table', 'guaranteed profit', 'risk free', 'get rich quick',
        'work from home', 'make money fast', 'lose weight fast'
    ];

    // Cache for performance
    private $cache = [];

    /**
     * Moderate advertisement content with ADVANCED INTELLIGENCE
     * Returns safety score and issues found
     */
    public function moderateAd($title, $description, $imagePaths = []) {
        $startTime = microtime(true);

        $result = [
            'safe' => true,
            'score' => 100,
            'issues' => [],
            'warnings' => [],
            'flags' => [],
            'confidence' => 0,
            'risk_level' => 'low',
            'processing_time' => 0
        ];

        // 1. Advanced Text Moderation with Context Analysis
        $textResult = $this->advancedTextModeration($title, $description);
        $result['score'] -= $textResult['penalty'];
        $result['issues'] = array_merge($result['issues'], $textResult['issues']);
        $result['flags'] = array_merge($result['flags'], $textResult['flags']);

        // 2. Sentiment Analysis
        $sentimentResult = $this->analyzeSentiment($title . ' ' . $description);
        $result['score'] -= $sentimentResult['penalty'];
        if (!empty($sentimentResult['warning'])) {
            $result['warnings'][] = $sentimentResult['warning'];
        }

        // 3. Suspicious Pattern Detection
        $patternResult = $this->detectSuspiciousPatterns($title . ' ' . $description);
        $result['score'] -= $patternResult['penalty'];
        $result['warnings'] = array_merge($result['warnings'], $patternResult['warnings']);

        // 4. Advanced Image Moderation
        if (!empty($imagePaths)) {
            $imageResult = $this->advancedImageModeration($imagePaths);
            $result['score'] -= $imageResult['penalty'];
            $result['issues'] = array_merge($result['issues'], $imageResult['issues']);
            $result['warnings'] = array_merge($result['warnings'], $imageResult['warnings']);
        }

        // 5. Calculate confidence and risk level
        $result['confidence'] = $this->calculateConfidence($result['score'], $result['issues']);
        $result['risk_level'] = $this->calculateRiskLevel($result['score'], $result['flags']);

        // 6. Determine if safe
        $result['safe'] = $result['score'] >= 70 && $result['risk_level'] !== 'critical';

        // Processing time
        $result['processing_time'] = round((microtime(true) - $startTime) * 1000, 2);

        return $result;
    }

    /**
     * ADVANCED TEXT MODERATION with context awareness
     */
    private function advancedTextModeration($title, $description) {
        $fullText = strtolower($title . ' ' . $description);
        $issues = [];
        $flags = [];
        $penalty = 0;

        // 1. Check for violent words with context
        foreach ($this->violentWords as $word) {
            if ($this->contextAwareMatch($fullText, $word)) {
                $context = $this->getWordContext($fullText, $word);
                $issues[] = "Violent language: '$word' in context: '$context'";
                $flags[] = 'violence';
                $penalty += 25;
            }
        }

        // 2. Check for word variations (l33t speak, etc.)
        foreach ($this->violentVariations as $variation) {
            if (strpos($fullText, $variation) !== false) {
                $issues[] = "Suspicious spelling variation detected: '$variation'";
                $flags[] = 'violence_variant';
                $penalty += 30; // Higher penalty for trying to bypass
            }
        }

        // 3. Check for abusive words
        foreach ($this->abusiveWords as $word) {
            if ($this->contextAwareMatch($fullText, $word)) {
                $issues[] = "Abusive language: '$word'";
                $flags[] = 'abusive';
                $penalty += 30;
            }
        }

        // 4. Check for illegal keywords with intelligence
        foreach ($this->illegalKeywords as $word) {
            if ($this->contextAwareMatch($fullText, $word)) {
                // Check if it's in a legitimate context
                if (!$this->isLegitimateContext($fullText, $word)) {
                    $issues[] = "Illegal content keyword: '$word'";
                    $flags[] = 'illegal';
                    $penalty += 40;
                }
            }
        }

        // 5. Advanced spam detection
        $spamScore = $this->advancedSpamDetection($fullText);
        if ($spamScore > 50) {
            $issues[] = "High spam probability detected (score: $spamScore%)";
            $flags[] = 'spam';
            $penalty += ($spamScore / 5);
        }

        // 6. Excessive caps with intelligence
        $capsRatio = $this->calculateCapsRatio($title . ' ' . $description);
        if ($capsRatio > 0.5 && strlen($title . $description) > 10) {
            $issues[] = "Excessive capitals detected";
            $penalty += 10;
        }

        return [
            'penalty' => min($penalty, 100),
            'issues' => $issues,
            'flags' => array_unique($flags)
        ];
    }

    /**
     * Context-aware matching (checks if word is in suspicious context)
     * Now matches word stems to catch plurals: weapon → weapons
     */
    private function contextAwareMatch($text, $word) {
        // Match exact word
        $pattern = '/\b' . preg_quote($word, '/') . '\b/';
        if (preg_match($pattern, $text) === 1) {
            return true;
        }

        // Also check for plural (word + 's')
        $pluralPattern = '/\b' . preg_quote($word, '/') . 's?\b/';
        if (preg_match($pluralPattern, $text) === 1) {
            return true;
        }

        // Check for common variations
        $variations = [
            $word . 's',   // weapons
            $word . 'es',  // knifes
            $word . 'ing', // killing
            $word . 'ed'   // killed
        ];

        foreach ($variations as $variation) {
            if (strpos($text, $variation) !== false) {
                return true;
            }
        }

        return false;
    }

    /**
     * Get context around a word
     */
    private function getWordContext($text, $word, $contextLength = 30) {
        $pos = strpos($text, $word);
        if ($pos === false) return '';

        $start = max(0, $pos - $contextLength);
        $length = strlen($word) + ($contextLength * 2);

        return '...' . substr($text, $start, $length) . '...';
    }

    /**
     * Check if word is in legitimate context
     */
    private function isLegitimateContext($text, $word) {
        // Some words might be legitimate in certain contexts
        $legitimateContexts = [
            'fake' => ['fake news article', 'fake flowers', 'fake grass'],
            'crack' => ['crack in wall', 'cracking sound'],
            'illegal' => ['illegal immigration law', 'illegal parking fine']
        ];

        if (isset($legitimateContexts[$word])) {
            foreach ($legitimateContexts[$word] as $legitPhrase) {
                if (strpos($text, $legitPhrase) !== false) {
                    return true;
                }
            }
        }

        return false;
    }

    /**
     * SENTIMENT ANALYSIS - Detect negative/aggressive tone
     */
    private function analyzeSentiment($text) {
        $text = strtolower($text);
        $negativeScore = 0;
        $penalty = 0;
        $warning = '';

        // Negative words
        $negativeWords = ['terrible', 'awful', 'horrible', 'disgusting', 'worst',
                         'hate', 'angry', 'furious', 'rage', 'destroy'];

        foreach ($negativeWords as $word) {
            if (strpos($text, $word) !== false) {
                $negativeScore += 10;
            }
        }

        // Aggressive punctuation
        $exclamationCount = substr_count($text, '!');
        if ($exclamationCount > 3) {
            $negativeScore += ($exclamationCount * 2);
        }

        // Determine sentiment
        if ($negativeScore > 30) {
            $warning = "Aggressive or negative tone detected";
            $penalty = min($negativeScore, 20);
        }

        return [
            'penalty' => $penalty,
            'warning' => $warning,
            'score' => $negativeScore
        ];
    }

    /**
     * DETECT SUSPICIOUS PATTERNS
     */
    private function detectSuspiciousPatterns($text) {
        $text = strtolower($text);
        $warnings = [];
        $penalty = 0;

        foreach ($this->suspiciousPatterns as $pattern) {
            if (strpos($text, $pattern) !== false) {
                $warnings[] = "Suspicious phrase: '$pattern'";
                $penalty += 15;
            }
        }

        // Check for phone number patterns (might indicate personal data selling)
        if (preg_match('/\b\d{10,}\b/', $text)) {
            $warnings[] = "Multiple phone numbers detected";
            $penalty += 5;
        }

        // Check for excessive URLs
        $urlCount = preg_match_all('/https?:\/\//', $text);
        if ($urlCount > 2) {
            $warnings[] = "Multiple external links detected";
            $penalty += 10;
        }

        return [
            'penalty' => min($penalty, 30),
            'warnings' => $warnings
        ];
    }

    /**
     * ADVANCED SPAM DETECTION with ML-like scoring
     */
    private function advancedSpamDetection($text) {
        $spamScore = 0;

        // 1. Repetitive characters
        if (preg_match('/(.)\1{4,}/', $text)) {
            $spamScore += 20;
        }

        // 2. Excessive punctuation
        $punctuationRatio = $this->calculatePunctuationRatio($text);
        if ($punctuationRatio > 0.15) {
            $spamScore += 15;
        }

        // 3. Common spam phrases
        $spamPhrases = ['click here', 'buy now', 'limited time', 'act now',
                       'free money', 'earn $', 'make $', 'guarantee'];
        $matchCount = 0;
        foreach ($spamPhrases as $phrase) {
            if (stripos($text, $phrase) !== false) {
                $matchCount++;
            }
        }
        $spamScore += ($matchCount * 10);

        // 4. All caps words
        $words = explode(' ', $text);
        $capsWords = 0;
        foreach ($words as $word) {
            if (strlen($word) > 3 && strtoupper($word) === $word) {
                $capsWords++;
            }
        }
        if ($capsWords > 3) {
            $spamScore += 10;
        }

        // 5. Number to text ratio
        $numberRatio = $this->calculateNumberRatio($text);
        if ($numberRatio > 0.3) {
            $spamScore += 10;
        }

        return min($spamScore, 100);
    }

    /**
     * Calculate punctuation ratio
     */
    private function calculatePunctuationRatio($text) {
        if (strlen($text) === 0) return 0;
        $punctuation = preg_match_all('/[!?.,:;]/', $text);
        return $punctuation / strlen($text);
    }

    /**
     * Calculate number ratio
     */
    private function calculateNumberRatio($text) {
        $text = preg_replace('/\s+/', '', $text);
        if (strlen($text) === 0) return 0;
        $numbers = preg_match_all('/\d/', $text);
        return $numbers / strlen($text);
    }

    /**
     * Calculate confidence level
     */
    private function calculateConfidence($score, $issues) {
        if (empty($issues)) {
            return 95; // High confidence if no issues
        }

        $issueCount = count($issues);
        $confidence = max(60, 95 - ($issueCount * 5));

        return $confidence;
    }

    /**
     * Calculate risk level
     */
    private function calculateRiskLevel($score, $flags) {
        // Check for critical flags
        $criticalFlags = ['violence', 'illegal', 'abusive'];
        foreach ($flags as $flag) {
            if (in_array($flag, $criticalFlags)) {
                return 'critical';
            }
        }

        if ($score >= 85) return 'low';
        if ($score >= 70) return 'medium';
        if ($score >= 50) return 'high';
        return 'critical';
    }

    /**
     * ADVANCED IMAGE MODERATION with AI-like analysis
     */
    private function advancedImageModeration($imagePaths) {
        $issues = [];
        $warnings = [];
        $penalty = 0;

        foreach ($imagePaths as $imagePath) {
            if (!file_exists($imagePath)) {
                continue;
            }

            // Check image size and dimensions
            $imageInfo = getimagesize($imagePath);
            if (!$imageInfo) {
                $warnings[] = "Could not read image: " . basename($imagePath);
                continue;
            }

            $width = $imageInfo[0];
            $height = $imageInfo[1];
            $fileSize = filesize($imagePath);

            // 1. Quality checks
            if ($width < 200 || $height < 200) {
                $warnings[] = "Low resolution image: " . basename($imagePath);
            }

            // 2. Advanced content analysis
            $contentAnalysis = $this->advancedImageContentAnalysis($imagePath);

            if ($contentAnalysis['suspicious']) {
                $issues = array_merge($issues, $contentAnalysis['concerns']);
                $penalty += $contentAnalysis['penalty'];
            }

            if (!empty($contentAnalysis['warnings'])) {
                $warnings = array_merge($warnings, $contentAnalysis['warnings']);
            }

            // 3. Check for manipulated images
            if ($this->detectImageManipulation($imagePath)) {
                $warnings[] = "Possible image manipulation detected";
                $penalty += 5;
            }

            // 4. Aspect ratio analysis (detect stretched/distorted images)
            $aspectRatio = $width / $height;
            if ($aspectRatio > 4 || $aspectRatio < 0.25) {
                $warnings[] = "Unusual aspect ratio detected";
            }
        }

        return [
            'penalty' => min($penalty, 50),
            'issues' => $issues,
            'warnings' => $warnings
        ];
    }

    /**
     * ADVANCED IMAGE CONTENT ANALYSIS (AI-like)
     */
    private function advancedImageContentAnalysis($imagePath) {
        $concerns = [];
        $warnings = [];
        $penalty = 0;
        $suspicious = false;

        // 1. Color analysis (detect skin tones - NSFW indicator)
        $colorAnalysis = $this->analyzeImageColors($imagePath);
        if ($colorAnalysis['skin_tone_ratio'] > 0.6) {
            $concerns[] = "High skin tone ratio detected - manual review recommended";
            $penalty += 30;
            $suspicious = true;
        }

        // 2. Histogram analysis (enhanced)
        $histogram = $this->advancedHistogramAnalysis($imagePath);
        if ($histogram['is_suspicious']) {
            $warnings[] = "Unusual image characteristics: " . $histogram['reason'];
            $penalty += 5;
        }

        // 3. Edge detection (blur/low quality indicator)
        $edgeScore = $this->calculateEdgeScore($imagePath);
        if ($edgeScore < 0.1) {
            $warnings[] = "Image may be blurred or low quality";
        }

        // 4. Text in image detection (might contain inappropriate text)
        if ($this->hasTextInImage($imagePath)) {
            $warnings[] = "Text detected in image - ensure it follows policy";
        }

        // 5. Check EXIF for copyright
        $exif = @exif_read_data($imagePath);
        if ($exif && isset($exif['Copyright'])) {
            $warnings[] = "Copyright metadata found: " . $exif['Copyright'];
        }

        return [
            'suspicious' => $suspicious,
            'concerns' => $concerns,
            'warnings' => $warnings,
            'penalty' => $penalty
        ];
    }

    /**
     * Analyze image colors (detect skin tones)
     */
    private function analyzeImageColors($imagePath) {
        $imageInfo = getimagesize($imagePath);
        $mimeType = $imageInfo['mime'];

        switch ($mimeType) {
            case 'image/jpeg':
                $image = imagecreatefromjpeg($imagePath);
                break;
            case 'image/png':
                $image = imagecreatefrompng($imagePath);
                break;
            case 'image/gif':
                $image = imagecreatefromgif($imagePath);
                break;
            default:
                return ['skin_tone_ratio' => 0];
        }

        if (!$image) {
            return ['skin_tone_ratio' => 0];
        }

        $width = imagesx($image);
        $height = imagesy($image);

        $sampleSize = min($width * $height, 1000);
        $skinTonePixels = 0;

        for ($i = 0; $i < $sampleSize; $i++) {
            $x = rand(0, $width - 1);
            $y = rand(0, $height - 1);
            $rgb = imagecolorat($image, $x, $y);
            $colors = imagecolorsforindex($image, $rgb);

            // Skin tone detection (simplified)
            if ($this->isSkinTone($colors['red'], $colors['green'], $colors['blue'])) {
                $skinTonePixels++;
            }
        }

        imagedestroy($image);

        return [
            'skin_tone_ratio' => $skinTonePixels / $sampleSize
        ];
    }

    /**
     * Check if color is skin tone
     */
    private function isSkinTone($r, $g, $b) {
        // Simplified skin tone detection
        // Real implementation would use more sophisticated algorithms
        return ($r > 95 && $g > 40 && $b > 20 &&
                $r > $g && $r > $b &&
                abs($r - $g) > 15 &&
                $r - $b > 15);
    }

    /**
     * Advanced histogram analysis
     */
    private function advancedHistogramAnalysis($imagePath) {
        $imageInfo = getimagesize($imagePath);
        $mimeType = $imageInfo['mime'];

        switch ($mimeType) {
            case 'image/jpeg':
                $image = imagecreatefromjpeg($imagePath);
                break;
            case 'image/png':
                $image = imagecreatefrompng($imagePath);
                break;
            case 'image/gif':
                $image = imagecreatefromgif($imagePath);
                break;
            default:
                return ['is_suspicious' => false, 'reason' => ''];
        }

        if (!$image) {
            return ['is_suspicious' => false, 'reason' => ''];
        }

        $width = imagesx($image);
        $height = imagesy($image);
        $sampleSize = min($width * $height, 1000);

        $darkPixels = 0;
        $lightPixels = 0;
        $midPixels = 0;
        $colorVariance = 0;

        for ($i = 0; $i < $sampleSize; $i++) {
            $x = rand(0, $width - 1);
            $y = rand(0, $height - 1);
            $rgb = imagecolorat($image, $x, $y);
            $colors = imagecolorsforindex($image, $rgb);

            $brightness = ($colors['red'] + $colors['green'] + $colors['blue']) / 3;

            if ($brightness < 50) {
                $darkPixels++;
            } elseif ($brightness > 200) {
                $lightPixels++;
            } else {
                $midPixels++;
            }

            $colorVariance += abs($colors['red'] - $colors['green']) +
                            abs($colors['green'] - $colors['blue']) +
                            abs($colors['blue'] - $colors['red']);
        }

        imagedestroy($image);

        $darkRatio = $darkPixels / $sampleSize;
        $lightRatio = $lightPixels / $sampleSize;
        $avgVariance = $colorVariance / $sampleSize;

        // Analysis
        if ($darkRatio > 0.9) {
            return ['is_suspicious' => true, 'reason' => 'mostly black/dark'];
        }
        if ($lightRatio > 0.9) {
            return ['is_suspicious' => true, 'reason' => 'mostly white/light'];
        }
        if ($avgVariance < 5) {
            return ['is_suspicious' => true, 'reason' => 'very low color variation'];
        }

        return ['is_suspicious' => false, 'reason' => ''];
    }

    /**
     * Calculate edge score (sharpness indicator)
     */
    private function calculateEdgeScore($imagePath) {
        // Simplified edge detection
        // Real implementation would use Sobel or Canny edge detection
        $imageInfo = getimagesize($imagePath);

        if (!$imageInfo) return 0.5;

        // For now, return a placeholder
        // In production, integrate with actual edge detection algorithms
        return 0.5;
    }

    /**
     * Detect if image contains text
     */
    private function hasTextInImage($imagePath) {
        // Placeholder for OCR integration
        // In production, integrate with Tesseract OCR or Google Vision API

        // Basic heuristic: check for high contrast edges that might be text
        return false;
    }

    /**
     * Detect image manipulation/photoshop
     */
    private function detectImageManipulation($imagePath) {
        // Check for common manipulation indicators
        $exif = @exif_read_data($imagePath);

        if ($exif) {
            // Check if software tag indicates editing
            if (isset($exif['Software'])) {
                $software = strtolower($exif['Software']);
                $editors = ['photoshop', 'gimp', 'paint.net', 'pixlr'];

                foreach ($editors as $editor) {
                    if (strpos($software, $editor) !== false) {
                        return true;
                    }
                }
            }
        }

        return false;
    }

    /**
     * Calculate capital letters ratio
     */
    private function calculateCapsRatio($text) {
        $text = preg_replace('/[^a-zA-Z]/', '', $text);
        if (strlen($text) === 0) return 0;

        $uppercase = preg_replace('/[^A-Z]/', '', $text);
        return strlen($uppercase) / strlen($text);
    }

    /**
     * Detect spam patterns
     */
    private function detectSpamPatterns($text) {
        // Check for excessive repetition
        if (preg_match('/(.)\1{4,}/', $text)) {
            return true;
        }

        // Check for excessive exclamation marks
        if (substr_count($text, '!') > 5) {
            return true;
        }

        // Check for excessive question marks
        if (substr_count($text, '?') > 5) {
            return true;
        }

        // Check for common spam phrases
        $spamPhrases = ['click here', 'buy now', 'limited time', 'act now', 'free money'];
        $spamCount = 0;
        foreach ($spamPhrases as $phrase) {
            if (stripos($text, $phrase) !== false) {
                $spamCount++;
            }
        }

        return $spamCount >= 3;
    }

    /**
     * Check potential copyright issues (basic)
     */
    public function checkCopyrightRisk($title, $description) {
        $text = strtolower($title . ' ' . $description);
        $risk = 'low';
        $concerns = [];

        // Check for brand names (this is basic - real implementation needs comprehensive list)
        $knownBrands = ['nike', 'adidas', 'apple', 'samsung', 'coca-cola', 'pepsi',
                        'disney', 'marvel', 'mcdonalds', 'starbucks'];

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

        return [
            'risk' => $risk,
            'concerns' => $concerns
        ];
    }

    /**
     * Generate safety report
     */
    public function generateReport($moderationResult, $copyrightResult) {
        $report = [
            'timestamp' => date('Y-m-d H:i:s'),
            'overall_status' => $moderationResult['safe'] ? 'APPROVED' : 'REJECTED',
            'safety_score' => $moderationResult['score'],
            'processing_time' => $moderationResult['processing_time'] . 'ms',
            'issues_found' => count($moderationResult['issues']),
            'warnings_found' => count($moderationResult['warnings']),
            'flags' => $moderationResult['flags'],
            'copyright_risk' => $copyrightResult['risk'],
            'details' => [
                'content_issues' => $moderationResult['issues'],
                'warnings' => $moderationResult['warnings'],
                'copyright_concerns' => $copyrightResult['concerns']
            ]
        ];

        return $report;
    }
}

