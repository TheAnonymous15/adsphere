<?php

class DashboardController
{
    public function handle()
    {
        session_start();

        // --- Require login ---
        if (empty($_SESSION['user_id'])) {
            header("Location: /login");
            exit;
        }

        // Page logic here
        return [
            "username" => $_SESSION['username'] ?? null,
        ];
    }
}
