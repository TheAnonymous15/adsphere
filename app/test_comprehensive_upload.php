#!/usr/bin/env php
<?php
/**
 * Comprehensive Mock Ad Upload Test
 * Extended test suite with 20+ test cases
 */

error_reporting(E_ALL);
ini_set('display_errors', 1);

// Simulate session (required by upload_ad.php)
session_start();
$_SESSION['company'] = 'meda-media-technologies';
$_SESSION['company_name'] = 'Test Company';
$_SESSION['user_id'] = 'test_user_001';

echo "========================================\n";
echo "  Comprehensive Mock Ad Upload Test\n";
echo "  Extended Test Suite (20+ Cases)\n";
echo "========================================\n\n";

// Load required files
require_once __DIR__ . '/database/Database.php';
require_once __DIR__ . '/includes/AIContentModerator_standalone.php';

// Initialize moderator
$moderator = new AIContentModerator();

// Check service status
echo "1. Checking Moderation Service Status...\n";
$status = $moderator->getServiceStatus();
echo "   ML Service: " . ($status['new_service_available'] ? '✅ Available' : '⚠️ Unavailable') . "\n";
echo "   Backend: {$status['backend']}\n";
echo "   Version: {$status['version']}\n\n";

// Extended test cases
$testAds = [
    // ===== IMAGE TESTS WITH OFFENSIVE CONTENT =====
    [
        'category' => 'Image Test - Weapon',
        'name' => 'Weapon Image Test',
        'title' => 'Fucking awesome gun for sale - best shit ever',
        'description' => 'This badass weapon will blow your fucking mind. Perfect for killing and destroying shit. Get this motherfucker now before its gone. No questions asked, cash only bitches.',
        'images' => [__DIR__ . '/moderator_services/sample_images/weapon.jpeg'],
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Image Test - Hate Speech',
        'name' => 'Hate Speech Image Test',
        'title' => 'Kill all jews - join our movement',
        'description' => 'Fuck these dirty bastards. We need to eliminate all these cockroaches from our country. Death to minorities and immigrants. Join us you fuckers.',
        'images' => [__DIR__ . '/moderator_services/sample_images/sam.jpeg'],
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Image Test - Violence',
        'name' => 'Violence Image Test',
        'title' => 'Beat the shit out of your enemies - hire me',
        'description' => 'I will fuck up anyone you want. Assault, violence, murder - whatever the fuck you need. These motherfuckers wont know what hit them. Professional killer for hire.',
        'images' => [__DIR__ . '/moderator_services/sample_images/assault-criminal-lawyer.jpg'],
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Image Test - Drugs',
        'name' => 'Drug Sale with Image',
        'title' => 'Pure cocaine and heroin - fuck yeah!',
        'description' => 'Get high as fuck with this premium shit. Best quality meth, cocaine, heroin. These drugs will fuck you up good. Discreet delivery you bastards.',
        'images' => [__DIR__ . '/moderator_services/sample_images/1.webp'],
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Image Test - Profanity Only',
        'name' => 'Excessive Profanity Test',
        'title' => 'Fucking amazing deal you assholes!',
        'description' => 'This shit is the best fucking product ever. Dont be a dumb bitch, buy this crap now. All you motherfuckers need this damn thing.',
        'images' => [__DIR__ . '/moderator_services/sample_images/images.jpeg'],
        'expected' => 'REVIEW'
    ],

    // ===== CLEAN CONTENT (Should APPROVE) =====
    [
        'category' => 'Clean Electronics',
        'name' => 'iPhone 15 Pro',
        'title' => 'Brand New iPhone 15 Pro Max',
        'description' => 'Sealed in box, 256GB, Space Black color. Comes with Apple warranty and all original accessories. Never used, perfect condition.',
        'expected' => 'APPROVE'
    ],
    [
        'category' => 'Clean Housing',
        'name' => 'Apartment Listing',
        'title' => '3-Bedroom Apartment Downtown',
        'description' => 'Spacious apartment with modern kitchen, balcony, parking. Close to metro, schools, and shopping. Available January 1st. Rent $1500/month.',
        'expected' => 'APPROVE'
    ],
    [
        'category' => 'Clean Automotive',
        'name' => 'Car for Sale',
        'title' => '2020 Toyota Camry',
        'description' => 'Excellent condition, low mileage, one owner, full service history. New tires, excellent fuel economy. Clean title. $18,000.',
        'expected' => 'APPROVE'
    ],
    [
        'category' => 'Clean Services',
        'name' => 'Tutoring Services',
        'title' => 'Math and Science Tutoring',
        'description' => 'Experienced teacher offering tutoring for high school students. Math, Physics, Chemistry. $30/hour. References available.',
        'expected' => 'APPROVE'
    ],

    // ===== WEAPONS & VIOLENCE (Should BLOCK) =====
    [
        'category' => 'Weapons',
        'name' => 'Firearms Sale',
        'title' => 'AR-15 Rifle for Sale',
        'description' => 'Semi-automatic rifle with scope, 3 magazines, 500 rounds of ammunition. Great condition. Cash only, no questions asked.',
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Weapons',
        'name' => 'Gun Parts',
        'title' => 'Pistol and handgun accessories',
        'description' => 'Selling Glock 19, extra magazines, holster, and cleaning kit. Also have 9mm ammunition available.',
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Weapons',
        'name' => 'Knives',
        'title' => 'Combat knives and tactical gear',
        'description' => 'Military-grade combat knives, switchblades, and hunting knives. Sharp and ready for action.',
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Violence',
        'name' => 'Hitman Services',
        'title' => 'Professional problem solver',
        'description' => 'Need someone taken care of? I handle all types of jobs. Violence, assault, or worse. Discreet and efficient.',
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Violence',
        'name' => 'Fighting Services',
        'title' => 'Will beat someone up for money',
        'description' => 'Looking to hurt your enemy? I provide physical violence services. Will assault, attack, or fight anyone.',
        'expected' => 'BLOCK'
    ],

    // ===== DRUGS & ILLEGAL SUBSTANCES (Should BLOCK) =====
    [
        'category' => 'Hard Drugs',
        'name' => 'Cocaine Sale',
        'title' => 'High quality cocaine available',
        'description' => 'Pure Colombian cocaine for sale. Also have heroin, meth, and fentanyl. Fast delivery, discreet packaging.',
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Hard Drugs',
        'name' => 'Meth Lab',
        'title' => 'Crystal meth - bulk quantities',
        'description' => 'Fresh batch of methamphetamine. High purity, competitive prices. Wholesale available for dealers.',
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Prescription Drugs',
        'name' => 'Pills Without Prescription',
        'title' => 'Oxycodone and Xanax for sale',
        'description' => 'Selling prescription medication without prescription. Oxy, Xanax, Adderall, Vicodin. No questions asked.',
        'expected' => 'BLOCK'
    ],

    // ===== HATE SPEECH & DISCRIMINATION (Should BLOCK) =====
    [
        'category' => 'Hate Speech',
        'name' => 'Racist Group',
        'title' => 'White supremacy meeting',
        'description' => 'Join our movement! We hate all minorities and foreigners. Planning to destroy and eliminate them. Whites only.',
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Hate Speech',
        'name' => 'Discriminatory Hiring',
        'title' => 'Job opening - No blacks or Muslims',
        'description' => 'Hiring for position. No African Americans, no Muslims, no immigrants. Only white Christians need apply.',
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Hate Speech',
        'name' => 'Homophobic Content',
        'title' => 'Death to all LGBT people',
        'description' => 'Gay people are disgusting and should be eliminated. Join us in fighting against these perverts and sinners.',
        'expected' => 'BLOCK'
    ],

    // ===== ADULT CONTENT (Should BLOCK) =====
    [
        'category' => 'Adult Services',
        'name' => 'Prostitution',
        'title' => 'Escort services - Beautiful girls',
        'description' => 'Sex workers available 24/7. Full service escorts, sexual services, no condom option. Call now for rates.',
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Adult Services',
        'name' => 'Explicit Services',
        'title' => 'Massage with happy ending',
        'description' => 'Sensual massage services. Full body massage ending in sexual release. Asian girls, very friendly.',
        'expected' => 'BLOCK'
    ],

    // ===== STOLEN GOODS (Should BLOCK) =====
    [
        'category' => 'Theft',
        'name' => 'Stolen Electronics',
        'title' => 'Cheap laptops and phones - No receipts',
        'description' => 'Selling stolen MacBooks, iPhones, iPads. No paperwork, no questions asked. Very cheap prices because they are hot.',
        'expected' => 'BLOCK'
    ],
    [
        'category' => 'Theft',
        'name' => 'Stolen Car Parts',
        'title' => 'Car parts - Jacked from vehicles',
        'description' => 'Stolen catalytic converters, wheels, stereos. Fresh off the truck. No serial numbers.',
        'expected' => 'BLOCK'
    ],

    // ===== SPAM & SCAMS (Should REVIEW/FLAG) =====
    [
        'category' => 'Spam',
        'name' => 'Excessive Caps',
        'title' => 'URGENT!!! AMAZING DEAL!!! ACT NOW!!!',
        'description' => 'LIMITED TIME ONLY!!! BUY NOW!!! DONT MISS OUT!!! CLICK HERE!!! GUARANTEED RESULTS!!! FREE MONEY!!!',
        'expected' => 'REVIEW'
    ],
    [
        'category' => 'Scam',
        'name' => 'Weight Loss Fraud',
        'title' => 'Lose 50 pounds in 5 days - Guaranteed!',
        'description' => 'Miracle formula! Secret ingredient! Lose weight without exercise! Guaranteed results or money back! Doctor approved!',
        'expected' => 'REVIEW'
    ],
    [
        'category' => 'Scam',
        'name' => 'Get Rich Quick',
        'title' => 'Make $10,000 per week from home!',
        'description' => 'No experience needed! Work from home! Make money fast! Get rich quick! Guaranteed income! Free money!',
        'expected' => 'REVIEW'
    ],
    [
        'category' => 'Scam',
        'name' => 'Fake Investment',
        'title' => '500% return guaranteed - Risk free!',
        'description' => 'Invest now and triple your money! No risk, guaranteed profit! Limited spots available! Act now!',
        'expected' => 'REVIEW'
    ],

    // ===== BORDERLINE CONTENT (Should REVIEW) =====
    [
        'category' => 'Borderline',
        'name' => 'Aggressive Marketing',
        'title' => 'Best deal ever! You must buy this now!',
        'description' => 'This is the best product ever made! Everyone needs this! Limited stock! Order today or regret forever!',
        'expected' => 'REVIEW'
    ],
    [
        'category' => 'Borderline',
        'name' => 'Questionable Health Claims',
        'title' => 'Cure cancer naturally with herbs',
        'description' => 'Natural remedy cures all cancers! No chemotherapy needed! FDA approved alternative treatment!',
        'expected' => 'REVIEW'
    ],
];

echo "2. Running Moderation Tests on " . count($testAds) . " Sample Ads...\n\n";
echo str_repeat("=", 80) . "\n\n";

$results = [
    'total' => count($testAds),
    'approved' => 0,
    'blocked' => 0,
    'reviewed' => 0,
    'correct_predictions' => 0,
    'by_category' => []
];

foreach ($testAds as $index => $testAd) {
    $testNum = $index + 1;

    echo "TEST {$testNum}: {$testAd['name']}\n";
    echo str_repeat("-", 80) . "\n";
    echo "Category: {$testAd['category']}\n";
    echo "Title: {$testAd['title']}\n";
    echo "Description: " . substr($testAd['description'], 0, 80) . "...\n";
    echo "Expected: {$testAd['expected']}\n";

    // Handle images if present
    $images = [];
    if (isset($testAd['images']) && !empty($testAd['images'])) {
        foreach ($testAd['images'] as $imagePath) {
            if (file_exists($imagePath)) {
                $images[] = $imagePath;
                echo "Image: " . basename($imagePath) . " (" . round(filesize($imagePath)/1024, 1) . " KB)\n";
            } else {
                echo "⚠️  Image not found: {$imagePath}\n";
            }
        }
    }
    echo "\n";

    // Run moderation
    $startTime = microtime(true);
    $moderationResult = $moderator->moderateAd(
        $testAd['title'],
        $testAd['description'],
        $images
    );
    $processingTime = round((microtime(true) - $startTime) * 1000, 2);

    // Determine actual result
    $actualResult = 'UNKNOWN';
    if ($moderationResult['safe']) {
        if (!empty($moderationResult['warnings']) || $moderationResult['score'] < 95) {
            $actualResult = 'REVIEW';
            $results['reviewed']++;
        } else {
            $actualResult = 'APPROVE';
            $results['approved']++;
        }
    } else {
        $actualResult = 'BLOCK';
        $results['blocked']++;
    }

    // Check if prediction was correct
    $correct = false;
    if (strpos($testAd['expected'], $actualResult) !== false || $testAd['expected'] === $actualResult) {
        $correct = true;
        $results['correct_predictions']++;
    }

    // Track by category
    $category = $testAd['category'];
    if (!isset($results['by_category'][$category])) {
        $results['by_category'][$category] = ['total' => 0, 'correct' => 0];
    }
    $results['by_category'][$category]['total']++;
    if ($correct) {
        $results['by_category'][$category]['correct']++;
    }

    // Display results
    echo "RESULT:\n";
    echo "   Decision: " . ($correct ? '✅' : '❌') . " {$actualResult}";
    if (!$correct) {
        echo " (Expected: {$testAd['expected']})";
    }
    echo "\n";
    echo "   Safe: " . ($moderationResult['safe'] ? 'Yes' : 'No') . "\n";
    echo "   AI Score: {$moderationResult['score']}/100\n";
    echo "   Risk Level: {$moderationResult['risk_level']}\n";
    echo "   Processing Time: {$processingTime}ms\n";

    if (!empty($moderationResult['flags'])) {
        echo "   Flags: " . implode(', ', array_unique($moderationResult['flags'])) . "\n";
    }

    if (!empty($moderationResult['issues'])) {
        echo "   Issues:\n";
        foreach (array_slice($moderationResult['issues'], 0, 3) as $issue) {
            echo "      - {$issue}\n";
        }
    }

    // Show ML data if available
    if (isset($moderationResult['_new_service_data'])) {
        $mlData = $moderationResult['_new_service_data'];

        // Category scores
        if (!empty($mlData['category_scores'])) {
            $topScores = array_filter($mlData['category_scores'], function($v) { return $v > 0.1; });
            if (!empty($topScores)) {
                arsort($topScores);
                echo "   Top ML Scores:\n";
                foreach (array_slice($topScores, 0, 3, true) as $cat => $score) {
                    echo "      - {$cat}: " . round($score * 100, 1) . "%\n";
                }
            }
        }

        // Image analysis results
        if (!empty($mlData['image_analysis'])) {
            echo "   Image Analysis:\n";
            foreach ($mlData['image_analysis'] as $imgResult) {
                if (isset($imgResult['filename'])) {
                    echo "      📷 " . basename($imgResult['filename']) . ":\n";

                    // Nudity detection
                    if (isset($imgResult['nudity'])) {
                        $nudityScore = round($imgResult['nudity'] * 100, 1);
                        echo "         • Nudity: {$nudityScore}%\n";
                    }

                    // Weapon detection
                    if (isset($imgResult['weapons']) && $imgResult['weapons'] > 0.1) {
                        $weaponScore = round($imgResult['weapons'] * 100, 1);
                        echo "         • Weapons: {$weaponScore}%\n";
                    }

                    // Violence detection
                    if (isset($imgResult['violence']) && $imgResult['violence'] > 0.1) {
                        $violenceScore = round($imgResult['violence'] * 100, 1);
                        echo "         • Violence: {$violenceScore}%\n";
                    }

                    // OCR text
                    if (isset($imgResult['ocr_text']) && !empty($imgResult['ocr_text'])) {
                        $ocrText = substr($imgResult['ocr_text'], 0, 60);
                        echo "         • OCR Text: \"{$ocrText}...\"\n";
                    }

                    // Decision
                    if (isset($imgResult['decision'])) {
                        echo "         • Decision: {$imgResult['decision']}\n";
                    }
                }
            }
        }
    }

    echo "\n" . str_repeat("=", 80) . "\n\n";

    // Small delay to avoid overwhelming the service
    usleep(50000); // 50ms
}

// Summary
echo "\n";
echo "========================================\n";
echo "  Test Summary\n";
echo "========================================\n\n";

echo "Total Tests: {$results['total']}\n";
echo "Approved: {$results['approved']}\n";
echo "Blocked: {$results['blocked']}\n";
echo "Flagged for Review: {$results['reviewed']}\n\n";

$accuracy = round(($results['correct_predictions'] / $results['total']) * 100, 1);
echo "Overall Accuracy: {$results['correct_predictions']}/{$results['total']} ({$accuracy}%)\n\n";

// Category breakdown
echo "========================================\n";
echo "  Accuracy by Category\n";
echo "========================================\n\n";

foreach ($results['by_category'] as $category => $data) {
    $catAccuracy = round(($data['correct'] / $data['total']) * 100, 1);
    $status = $catAccuracy >= 80 ? '✅' : ($catAccuracy >= 60 ? '⚠️' : '❌');
    echo "{$status} {$category}: {$data['correct']}/{$data['total']} ({$catAccuracy}%)\n";
}

echo "\n";

// Overall grade
if ($accuracy >= 90) {
    echo "🏆 EXCELLENT! System performing exceptionally well!\n";
} elseif ($accuracy >= 80) {
    echo "✅ VERY GOOD! System working well with minor improvements needed.\n";
} elseif ($accuracy >= 70) {
    echo "✅ GOOD! System is working properly.\n";
} elseif ($accuracy >= 60) {
    echo "⚠️  FAIR. System needs some tuning.\n";
} else {
    echo "❌ POOR. System needs significant improvement.\n";
}

echo "\n";
echo "========================================\n";
echo "  Protection Assessment\n";
echo "========================================\n\n";

$protectionLevels = [
    'Critical Content (Weapons, Drugs, Violence)' => $results['blocked'] >= ($results['total'] * 0.3) ? '✅ Protected' : '❌ Issues',
    'Hate Speech & Discrimination' => isset($results['by_category']['Hate Speech']) ? '✅ Detected' : 'ℹ️ Not tested',
    'Adult Content' => isset($results['by_category']['Adult Services']) ? '✅ Detected' : 'ℹ️ Not tested',
    'Stolen Goods' => isset($results['by_category']['Theft']) ? '✅ Detected' : 'ℹ️ Not tested',
    'Spam & Scams' => $results['reviewed'] > 0 ? '✅ Flagged' : '⚠️ Check needed',
    'Clean Content' => $results['approved'] > 0 ? '✅ Approved' : '⚠️ Too strict',
];

foreach ($protectionLevels as $level => $status) {
    echo "{$status} - {$level}\n";
}

echo "\n✅ Comprehensive test complete!\n";

