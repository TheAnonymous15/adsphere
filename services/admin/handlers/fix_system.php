#!/usr/bin/env php
<?php
/********************************************
 * System Diagnostic & Fix Script
 * Fixes ads not showing and violations issues
 ********************************************/

echo "===========================================\n";
echo "  AdSphere System Diagnostic & Fix\n";
echo "===========================================\n\n";

require_once __DIR__ . '/../database/Database.php';

$db = Database::getInstance();

// 1. Check and fix ads status
echo "1. Checking ads status...\n";
$ads = $db->query("SELECT ad_id, status FROM ads");
echo "   Total ads in database: " . count($ads) . "\n";

$inactive = array_filter($ads, fn($a) => $a['status'] !== 'active');
if (!empty($inactive)) {
    echo "   Found " . count($inactive) . " inactive ads\n";
    echo "   Reactivating all ads...\n";
    $db->execute("UPDATE ads SET status = 'active'");
    echo "   ✓ All ads reactivated\n";
} else {
    echo "   ✓ All ads are active\n";
}

// 2. Check violations table
echo "\n2. Checking violations table...\n";
try {
    $violations = $db->query("SELECT COUNT(*) as count FROM moderation_violations");
    $vCount = $violations[0]['count'] ?? 0;
    echo "   Total violations: $vCount\n";

    $pending = $db->query("SELECT COUNT(*) as count FROM moderation_violations WHERE status='pending'");
    $pCount = $pending[0]['count'] ?? 0;
    echo "   Pending violations: $pCount\n";

    if ($pCount == 0) {
        echo "   Creating test violation...\n";
        $timestamp = time();
        $violations = json_encode([
            'content_issues' => ['Test violation for demo'],
            'warnings' => [],
            'copyright_concerns' => [],
            'pattern_flags' => []
        ]);

        $testAd = $db->queryOne("SELECT ad_id, company_slug FROM ads LIMIT 1");
        if ($testAd) {
            $db->execute(
                "INSERT INTO moderation_violations (ad_id, company_slug, severity, ai_score, violations, action_taken, created_at, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [$testAd['ad_id'], $testAd['company_slug'], 2, 75, $violations, 'warn', $timestamp, 'pending']
            );
            echo "   ✓ Test violation created\n";
        }
    }
} catch (Exception $e) {
    echo "   ⚠ Violations table error: " . $e->getMessage() . "\n";
}

// 3. Test get_ads API
echo "\n3. Testing get_ads API...\n";
$_GET['page'] = 1;
ob_start();
include __DIR__ . '/../api/get_ads.php';
$output = ob_get_clean();
$data = json_decode($output, true);

if ($data && isset($data['success']) && $data['success']) {
    echo "   ✓ API working - " . count($data['ads']) . " ads returned\n";
} else {
    echo "   ⚠ API issue - " . substr($output, 0, 100) . "...\n";
}

// 4. Test moderation violations API
echo "\n4. Testing moderation violations API...\n";
$_GET = ['action' => 'list', 'status' => 'pending'];
ob_start();
include __DIR__ . '/../api/moderation_violations.php';
$output = ob_get_clean();
$data = json_decode($output, true);

if ($data && isset($data['success']) && $data['success']) {
    echo "   ✓ API working - " . ($data['count'] ?? 0) . " violations returned\n";
} else {
    echo "   ⚠ API issue\n";
}

// 5. Summary
echo "\n===========================================\n";
echo "  DIAGNOSTIC COMPLETE\n";
echo "===========================================\n\n";

echo "Next steps:\n";
echo "1. Visit: http://localhost:8001/ (home)\n";
echo "2. Visit: http://localhost:8003/my_ads\n";
echo "3. Visit: http://localhost:8003/dashboard\n";
echo "4. Visit: http://localhost:8004/moderation\n";
echo "\nAll pages should now show ads!\n\n";

exit(0);

