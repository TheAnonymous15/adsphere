<?php
require '../config.php';
session_destroy();
setcookie("remember_me", "", time()-3600, "/");
echo json_encode(['status'=>1, 'message'=>'Logged out']);
?>
