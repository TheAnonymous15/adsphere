<?php
header("Content-Type: application/json");

$ads = json_decode(file_get_contents(__DIR__."/ads.json"),true);
$likes = json_decode(file_get_contents(__DIR__."/likes.json"),true);

$totalAds = count($ads);
$totalLikes = array_sum($likes);

echo json_encode([
    "total_ads"=>$totalAds,
    "total_likes"=>$totalLikes
]);
