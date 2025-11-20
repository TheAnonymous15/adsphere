<?php
declare(strict_types=1);

class LoginController
{
    public function handle(): array
    {
        session_start();

        // If already logged in → redirect to dashboard
        if (!empty($_SESSION['user_id'])) {
            header("Location: /dashboard");
            exit;
        }

        // Only process POST form
        if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
            return [];
        }

        $email = trim($_POST['email'] ?? '');
        $password = trim($_POST['password'] ?? '');

        // Basic validation
        if ($email === '' || $password === '') {
            return ['error' => 'Please fill in all fields'];
        }

        // TODO: Replace with database user lookup
        $demoEmail = "admin@example.com";
        $demoPass  = "password123"; // (Hash this in the future)

        if ($email !== $demoEmail || $password !== $demoPass) {
            return ['error' => 'Invalid email or password'];
        }

        // Create login session
        $_SESSION['user_id'] = 1;
        $_SESSION['user_email'] = $email;

        // Redirect to dashboard or home
        header("Location: /dashboard");
        exit;
    }
}
