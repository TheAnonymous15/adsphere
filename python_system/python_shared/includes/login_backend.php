<?php
require '../config.php';
require '../csrf.php';

$data = json_decode(file_get_contents('php://input'), true);
$email = $data['email'] ?? '';
$password = $data['password'] ?? '';
$remember = $data['remember'] ?? false;
$csrf = $data['csrf_token'] ?? '';

if (!verify_csrf($csrf)) {
    echo json_encode(['status'=>0, 'message'=>'CSRF validation failed']);
    exit;
}

// Throttling
$stmt = $pdo->prepare("SELECT COUNT(*) FROM login_attempts WHERE ip_address = ? AND attempt_time > NOW() - INTERVAL 15 MINUTE");
$stmt->execute([ $_SERVER['REMOTE_ADDR'] ]);
if ($stmt->fetchColumn() >= 5) {
    echo json_encode(['status'=>0, 'message'=>'Too many attempts. Try again later.']);
    exit;
}

$stmt = $pdo->prepare("SELECT * FROM users WHERE email = ?");
$stmt->execute([$email]);
$user = $stmt->fetch(PDO::FETCH_ASSOC);

if ($user && password_verify($password, $user['password'])) {
    $_SESSION['user_id'] = $user['id'];
    $_SESSION['role'] = $user['role'];

    if ($remember) {
        $token = bin2hex(random_bytes(32));
        setcookie("remember_me", $token, time() + (86400*30), "/", "", false, true);
        $pdo->prepare("UPDATE users SET remember_token = ? WHERE id = ?")->execute([$token, $user['id']]);
    }

    echo json_encode(['status'=>1, 'message'=>'Login successful', 'role'=>$user['role']]);
} else {
    $pdo->prepare("INSERT INTO login_attempts (username, ip_address) VALUES (?, ?)")->execute([$email, $_SERVER['REMOTE_ADDR']]);
    echo json_encode(['status'=>0, 'message'=>'Invalid credentials']);
}
?>
