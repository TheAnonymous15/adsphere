<?php
session_start();
if(!isset($_SESSION['company'])) exit();

$company = $_SESSION['company'];
$profile = [
    "email"=>$_POST['email'] ?? "",
    "phone"=>$_POST['phone'] ?? "",
    "website"=>$_POST['website'] ?? "",
];

file_put_contents(
    __DIR__."/companies/$company/profile.json",
    json_encode($profile)
);

header("Location: profile.php?updated=1");
