<?php
header("Content-Type: application/json");
session_start();

$adId = $_POST['ad_id'] ?? null;

if(!$adId) {
    echo json_encode(["ok" => false, "msg" => "no id"]);
    exit();
}

$likesFile = __DIR__."/likes.json";

$likes = file_exists($likesFile)
    ? json_decode(file_get_contents($likesFile), true)
    : [];

if(!isset($likes[$adId])) $likes[$adId] = 0;

$likes[$adId]++;

file_put_contents($likesFile, json_encode($likes));

echo json_encode(["ok"=>true,"likes"=>$likes[$adId]]);
