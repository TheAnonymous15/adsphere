<?php
header("Content-Type: application/json");

$adsBase = __DIR__ . "/../companies/data/";

$categories = array_filter(scandir($adsBase), function($i) use ($adsBase){
    return $i !== "." && $i !== ".." && is_dir($adsBase . $i);
});

echo json_encode([
    "categories" => array_values($categories)
]);
exit;
