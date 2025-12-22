<?php
declare(strict_types=1);

// Only allow POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['status' => 'error', 'message' => 'Method not allowed']);
    exit;
}

// Get the message from POST data
$data = json_decode(file_get_contents('php://input'), true);
$message = $data['message'] ?? '';

if (empty($message)) {
    http_response_code(400);
    echo json_encode(['status' => 'error', 'message' => 'Message cannot be empty']);
    exit;
}

// Example using Twilio (install twilio/sdk via Composer)
// require_once 'vendor/autoload.php';
// use Twilio\Rest\Client;
// $sid = 'YOUR_TWILIO_SID';
// $token = 'YOUR_TWILIO_TOKEN';
// $twilio = new Client($sid, $token);
// $twilio->messages->create('+254726781724', ['from' => '+YOUR_TWILIO_NUMBER', 'body' => $message]);

// For demo: just return success
echo json_encode(['status' => 'success', 'message' => 'SMS sent!']);
