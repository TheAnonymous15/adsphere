<?php
require '../config.php';

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['status'=>0, 'message'=>'Not authenticated']);
    exit;
}

if ($_SESSION['role'] === 'admin') {
    echo json_encode(['status'=>1, 'dashboard'=>'Admin dashboard content']);
} else {
    echo json_encode(['status'=>1, 'dashboard'=>'User dashboard content']);
}
?>
