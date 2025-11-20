<?php

class ProfileController
{
    public function handle()
    {
        session_start();

        if (empty($_SESSION['user_id'])) {
            header("Location: /login");
            exit;
        }

        return [];
    }
}
