<?php
/********************************************
 * Moderation Violations API
 * Get pending violations and take actions
 ********************************************/

header('Content-Type: application/json');

require_once __DIR__ . '/../database/Database.php';
require_once __DIR__ . '/../includes/ModerationNotifier.php';

$db = Database::getInstance();
$notifier = new ModerationNotifier();

try {
    $action = $_GET['action'] ?? $_POST['action'] ?? 'list';

    switch ($action) {
        case 'list':
            // Get all pending violations
            $status = $_GET['status'] ?? 'pending';

            $violations = $db->query("
                SELECT
                    v.*,
                    a.title as ad_title,
                    a.description as ad_description,
                    a.category_slug,
                    c.company_name,
                    c.email as company_email,
                    cat.category_name
                FROM moderation_violations v
                LEFT JOIN ads a ON v.ad_id = a.ad_id
                LEFT JOIN companies c ON v.company_slug = c.company_slug
                LEFT JOIN categories cat ON a.category_slug = cat.category_slug
                WHERE v.status = ?
                ORDER BY v.severity DESC, v.created_at DESC
                LIMIT 50
            ", [$status]);

            // Parse violations JSON
            foreach ($violations as &$v) {
                $v['violations_data'] = json_decode($v['violations'], true);
            }

            echo json_encode([
                'success' => true,
                'violations' => $violations,
                'count' => count($violations)
            ], JSON_PRETTY_PRINT);
            break;

        case 'stats':
            // Get violation statistics
            $stats = $db->queryOne("
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved,
                    SUM(CASE WHEN severity = 4 THEN 1 ELSE 0 END) as critical,
                    SUM(CASE WHEN severity = 3 THEN 1 ELSE 0 END) as high,
                    SUM(CASE WHEN severity = 2 THEN 1 ELSE 0 END) as medium,
                    SUM(CASE WHEN severity = 1 THEN 1 ELSE 0 END) as low
                FROM moderation_violations
                WHERE created_at > ?
            ", [time() - (7 * 86400)]); // Last 7 days

            echo json_encode([
                'success' => true,
                'stats' => $stats
            ], JSON_PRETTY_PRINT);
            break;

        case 'take_action':
            // Take action on a violation
            $violationId = $_POST['violation_id'] ?? null;
            $actionType = $_POST['action_type'] ?? null;
            $adminUser = $_POST['admin_user'] ?? 'admin';

            if (!$violationId || !$actionType) {
                throw new Exception('Missing required parameters');
            }

            // Get violation details
            $violation = $db->queryOne(
                "SELECT * FROM moderation_violations WHERE id = ?",
                [$violationId]
            );

            if (!$violation) {
                throw new Exception('Violation not found');
            }

            // Perform action
            switch ($actionType) {
                case 'delete':
                    $db->execute(
                        "UPDATE ads SET status = 'inactive' WHERE ad_id = ?",
                        [$violation['ad_id']]
                    );
                    break;

                case 'ban':
                    $db->execute(
                        "UPDATE companies SET status = 'inactive' WHERE company_slug = ?",
                        [$violation['company_slug']]
                    );
                    $db->execute(
                        "UPDATE ads SET status = 'inactive' WHERE company_slug = ?",
                        [$violation['company_slug']]
                    );
                    break;

                case 'approve':
                    // Mark as resolved without action
                    break;

                case 'pause':
                    $db->execute(
                        "UPDATE ads SET status = 'inactive' WHERE ad_id = ?",
                        [$violation['ad_id']]
                    );
                    break;
            }

            // Update violation status
            $db->execute("
                UPDATE moderation_violations
                SET status = 'resolved',
                    resolved_at = ?,
                    resolved_by = ?,
                    action_taken = ?
                WHERE id = ?
            ", [time(), $adminUser, $actionType, $violationId]);

            // Log action
            $db->execute("
                INSERT INTO moderation_actions
                (violation_id, ad_id, action_type, admin_user, reason, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ", [
                $violationId,
                $violation['ad_id'],
                $actionType,
                $adminUser,
                $_POST['reason'] ?? 'Admin action',
                time()
            ]);

            // Send notification email to ad owner
            try {
                $notificationSent = $notifier->notifyAdOwner($violation, $actionType, $adminUser);
                $notificationStatus = $notificationSent ? 'sent' : 'failed';
            } catch (Exception $e) {
                error_log("Notification error: " . $e->getMessage());
                $notificationStatus = 'error';
            }

            echo json_encode([
                'success' => true,
                'message' => "Action '$actionType' executed successfully",
                'notification' => $notificationStatus
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

