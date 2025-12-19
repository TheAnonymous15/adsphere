<?php
/********************************************
 * Email Notification System
 * Sends notifications to ad owners about moderation actions
 ********************************************/

class ModerationNotifier {

    private $db;

    public function __construct() {
        require_once __DIR__ . '/../database/Database.php';
        $this->db = Database::getInstance();
    }

    /**
     * Send notification email to ad owner
     */
    public function notifyAdOwner($violation, $actionType, $adminUser = 'Admin') {
        // Get full ad and company details
        $adDetails = $this->db->queryOne("
            SELECT
                a.*,
                c.company_name,
                c.email as company_email,
                c.phone as company_phone,
                cat.category_name
            FROM ads a
            LEFT JOIN companies c ON a.company_slug = c.company_slug
            LEFT JOIN categories cat ON a.category_slug = cat.category_slug
            WHERE a.ad_id = ?
        ", [$violation['ad_id']]);

        if (!$adDetails || !$adDetails['company_email']) {
            error_log("Cannot send notification: No email for ad " . $violation['ad_id']);
            return false;
        }

        // Parse violations
        $violationsData = json_decode($violation['violations'], true);

        // Generate email content
        $emailData = $this->generateEmailContent(
            $adDetails,
            $violation,
            $violationsData,
            $actionType,
            $adminUser
        );

        // Send email (using PHP mail function - can be replaced with SMTP)
        $sent = $this->sendEmail(
            $adDetails['company_email'],
            $emailData['subject'],
            $emailData['body'],
            $emailData['html']
        );

        // Log notification
        $this->logNotification(
            $violation['ad_id'],
            $adDetails['company_slug'],
            $actionType,
            $adDetails['company_email'],
            $sent
        );

        return $sent;
    }

    /**
     * Generate email content based on action type
     */
    private function generateEmailContent($ad, $violation, $violationsData, $actionType, $adminUser) {
        $companyName = $ad['company_name'];
        $adTitle = $ad['title'];
        $violationsList = implode("\n• ", $violationsData['content_issues'] ?? []);
        $patternFlags = implode("\n• ", $violationsData['pattern_flags'] ?? []);

        // Action-specific messages
        $messages = [
            'delete' => [
                'subject' => '⚠️ Ad Removed - Policy Violation',
                'action' => 'REMOVED',
                'reason' => 'Your advertisement has been removed due to policy violations.',
                'consequence' => 'The ad is no longer visible on the platform.',
                'next_steps' => 'Please review our advertising policies before posting new content. Future violations may result in account suspension.'
            ],
            'ban' => [
                'subject' => '🚫 Account Suspended - Serious Policy Violations',
                'action' => 'ACCOUNT SUSPENDED',
                'reason' => 'Your account has been suspended due to serious or repeated policy violations.',
                'consequence' => 'All your advertisements have been removed and your account is now inactive.',
                'next_steps' => 'This is a permanent suspension. If you believe this is an error, please contact our appeals team at appeals@adsphere.com with your account details.'
            ],
            'pause' => [
                'subject' => '⏸️ Ad Under Review - Action Required',
                'action' => 'PAUSED FOR REVIEW',
                'reason' => 'Your advertisement has been paused pending review of potential policy concerns.',
                'consequence' => 'The ad is temporarily not visible on the platform.',
                'next_steps' => 'Our moderation team will review the ad. You may be contacted for clarification. If approved, the ad will be reactivated. You can also edit the ad to address the concerns.'
            ],
            'approve' => [
                'subject' => '✅ Ad Approved - No Action Needed',
                'action' => 'APPROVED',
                'reason' => 'After review, your advertisement has been approved.',
                'consequence' => 'Your ad remains active and visible on the platform.',
                'next_steps' => 'No action is needed. Thank you for following our advertising policies.'
            ]
        ];

        $msg = $messages[$actionType] ?? $messages['delete'];

        // Plain text email
        $textBody = "Dear {$companyName},\n\n";
        $textBody .= "ADVERTISEMENT STATUS UPDATE\n";
        $textBody .= "===========================\n\n";
        $textBody .= "Ad Title: {$adTitle}\n";
        $textBody .= "Ad ID: {$ad['ad_id']}\n";
        $textBody .= "Action Taken: {$msg['action']}\n";
        $textBody .= "Date: " . date('Y-m-d H:i:s') . "\n\n";

        $textBody .= "REASON:\n{$msg['reason']}\n\n";

        if (!empty($violationsList)) {
            $textBody .= "POLICY VIOLATIONS DETECTED:\n";
            $textBody .= "• {$violationsList}\n\n";
        }

        if (!empty($patternFlags)) {
            $textBody .= "ADDITIONAL CONCERNS:\n";
            $textBody .= "• {$patternFlags}\n\n";
        }

        $textBody .= "CONSEQUENCE:\n{$msg['consequence']}\n\n";
        $textBody .= "NEXT STEPS:\n{$msg['next_steps']}\n\n";

        $textBody .= "If you have questions, please contact our support team at support@adsphere.com\n\n";
        $textBody .= "Best regards,\n";
        $textBody .= "AdSphere Moderation Team\n";
        $textBody .= "Actioned by: {$adminUser}\n";

        // HTML email
        $htmlBody = $this->generateHTMLEmail($companyName, $adTitle, $ad['ad_id'], $msg, $violationsList, $patternFlags, $adminUser, $actionType);

        return [
            'subject' => $msg['subject'],
            'body' => $textBody,
            'html' => $htmlBody
        ];
    }

    /**
     * Generate beautiful HTML email
     */
    private function generateHTMLEmail($companyName, $adTitle, $adId, $msg, $violations, $flags, $adminUser, $actionType) {
        $actionColors = [
            'delete' => '#dc2626',
            'ban' => '#991b1b',
            'pause' => '#f59e0b',
            'approve' => '#16a34a'
        ];

        $actionIcons = [
            'delete' => '🗑️',
            'ban' => '🚫',
            'pause' => '⏸️',
            'approve' => '✅'
        ];

        $color = $actionColors[$actionType] ?? '#dc2626';
        $icon = $actionIcons[$actionType] ?? '⚠️';

        return "
<!DOCTYPE html>
<html>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f3f4f6; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, {$color} 0%, " . $this->darkenColor($color) . " 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { margin: 0; font-size: 24px; }
        .header .icon { font-size: 48px; margin-bottom: 10px; }
        .content { padding: 30px; }
        .info-box { background: #f9fafb; border-left: 4px solid {$color}; padding: 15px; margin: 20px 0; border-radius: 4px; }
        .info-row { display: flex; padding: 8px 0; border-bottom: 1px solid #e5e7eb; }
        .info-label { font-weight: bold; color: #6b7280; width: 120px; }
        .info-value { color: #1f2937; flex: 1; }
        .violations { background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 15px; margin: 20px 0; }
        .violations h3 { color: #dc2626; margin-top: 0; font-size: 16px; }
        .violations ul { margin: 10px 0; padding-left: 20px; color: #991b1b; }
        .violations li { margin: 5px 0; }
        .consequence { background: #fffbeb; border: 1px solid #fcd34d; border-radius: 8px; padding: 15px; margin: 20px 0; }
        .consequence h3 { color: #f59e0b; margin-top: 0; font-size: 16px; }
        .next-steps { background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 15px; margin: 20px 0; }
        .next-steps h3 { color: #16a34a; margin-top: 0; font-size: 16px; }
        .footer { background: #f9fafb; padding: 20px; text-align: center; color: #6b7280; font-size: 12px; }
        .button { display: inline-block; background: {$color}; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; margin: 10px 0; }
        .button:hover { opacity: 0.9; }
    </style>
</head>
<body>
    <div class='container'>
        <div class='header'>
            <div class='icon'>{$icon}</div>
            <h1>Advertisement Status Update</h1>
            <p style='margin: 10px 0 0 0; opacity: 0.9;'>Action: {$msg['action']}</p>
        </div>

        <div class='content'>
            <p>Dear <strong>{$companyName}</strong>,</p>

            <p>{$msg['reason']}</p>

            <div class='info-box'>
                <div class='info-row'>
                    <div class='info-label'>Ad Title:</div>
                    <div class='info-value'>{$adTitle}</div>
                </div>
                <div class='info-row'>
                    <div class='info-label'>Ad ID:</div>
                    <div class='info-value'>{$adId}</div>
                </div>
                <div class='info-row'>
                    <div class='info-label'>Date:</div>
                    <div class='info-value'>" . date('F j, Y \a\t g:i A') . "</div>
                </div>
                <div class='info-row' style='border: none;'>
                    <div class='info-label'>Actioned By:</div>
                    <div class='info-value'>{$adminUser}</div>
                </div>
            </div>

            " . (!empty($violations) ? "
            <div class='violations'>
                <h3>⚠️ Policy Violations Detected</h3>
                <ul>
                    <li>{$violations}</li>
                </ul>
            </div>
            " : "") . "

            " . (!empty($flags) ? "
            <div class='violations'>
                <h3>🚩 Additional Concerns</h3>
                <ul>
                    <li>{$flags}</li>
                </ul>
            </div>
            " : "") . "

            <div class='consequence'>
                <h3>📋 Consequence</h3>
                <p style='margin: 0;'>{$msg['consequence']}</p>
            </div>

            <div class='next-steps'>
                <h3>👉 Next Steps</h3>
                <p style='margin: 0;'>{$msg['next_steps']}</p>
            </div>

            <div style='text-align: center; margin: 30px 0;'>
                <a href='https://adsphere.com/support' class='button'>Contact Support</a>
                <a href='https://adsphere.com/policies' class='button' style='background: #6366f1;'>View Policies</a>
            </div>

            <p style='color: #6b7280; font-size: 14px; margin-top: 30px;'>
                If you have questions or believe this action was taken in error, please contact our support team at
                <a href='mailto:support@adsphere.com' style='color: {$color};'>support@adsphere.com</a>
            </p>
        </div>

        <div class='footer'>
            <p><strong>AdSphere Moderation Team</strong></p>
            <p>This is an automated notification. Please do not reply to this email.</p>
            <p>&copy; " . date('Y') . " AdSphere. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
        ";
    }

    /**
     * Darken a hex color
     */
    private function darkenColor($hex, $percent = 20) {
        $hex = str_replace('#', '', $hex);
        $r = hexdec(substr($hex, 0, 2));
        $g = hexdec(substr($hex, 2, 2));
        $b = hexdec(substr($hex, 4, 2));

        $r = max(0, $r - ($r * $percent / 100));
        $g = max(0, $g - ($g * $percent / 100));
        $b = max(0, $b - ($b * $percent / 100));

        return '#' . str_pad(dechex($r), 2, '0', STR_PAD_LEFT)
                   . str_pad(dechex($g), 2, '0', STR_PAD_LEFT)
                   . str_pad(dechex($b), 2, '0', STR_PAD_LEFT);
    }

    /**
     * Send email using PHP mail function
     * Replace this with SMTP for production (PHPMailer, SendGrid, etc.)
     */
    private function sendEmail($to, $subject, $textBody, $htmlBody) {
        $from = "noreply@adsphere.com";
        $fromName = "AdSphere Moderation";

        $headers = "From: {$fromName} <{$from}>\r\n";
        $headers .= "Reply-To: support@adsphere.com\r\n";
        $headers .= "MIME-Version: 1.0\r\n";
        $headers .= "Content-Type: multipart/alternative; boundary=\"boundary-" . md5(time()) . "\"\r\n";

        $boundary = "boundary-" . md5(time());

        $message = "--{$boundary}\r\n";
        $message .= "Content-Type: text/plain; charset=UTF-8\r\n";
        $message .= "Content-Transfer-Encoding: 7bit\r\n\r\n";
        $message .= $textBody . "\r\n\r\n";

        $message .= "--{$boundary}\r\n";
        $message .= "Content-Type: text/html; charset=UTF-8\r\n";
        $message .= "Content-Transfer-Encoding: 7bit\r\n\r\n";
        $message .= $htmlBody . "\r\n\r\n";

        $message .= "--{$boundary}--";

        // For development, log instead of sending
        if (getenv('APP_ENV') === 'development' || !function_exists('mail')) {
            $logFile = __DIR__ . '/../logs/email_notifications_' . date('Y-m-d') . '.log';
            $logEntry = sprintf(
                "[%s] TO: %s | SUBJECT: %s | BODY: %s\n\n",
                date('Y-m-d H:i:s'),
                $to,
                $subject,
                substr($textBody, 0, 200) . '...'
            );
            file_put_contents($logFile, $logEntry, FILE_APPEND | LOCK_EX);
            return true; // Simulate success
        }

        // Send actual email
        return mail($to, $subject, $message, $headers);
    }

    /**
     * Log notification attempt
     */
    private function logNotification($adId, $companySlug, $actionType, $email, $sent) {
        try {
            $this->db->execute("
                CREATE TABLE IF NOT EXISTS notification_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad_id TEXT NOT NULL,
                    company_slug TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    recipient_email TEXT NOT NULL,
                    sent_successfully INTEGER NOT NULL,
                    created_at INTEGER NOT NULL
                )
            ");

            $this->db->execute("
                INSERT INTO notification_log
                (ad_id, company_slug, action_type, recipient_email, sent_successfully, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ", [
                $adId,
                $companySlug,
                $actionType,
                $email,
                $sent ? 1 : 0,
                time()
            ]);
        } catch (Exception $e) {
            error_log("Failed to log notification: " . $e->getMessage());
        }
    }
}

