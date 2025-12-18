<?php
header("Content-Type: application/json");

$ads = require __DIR__ . "/../includes/ads.php";

$page     = intval($_GET["page"] ?? 1);
$q        = strtolower($_GET["q"] ?? "");
$category = strtolower($_GET["category"] ?? "");
$sort     = $_GET["sort"] ?? "date";

$pageSize = 12;

$filtered = array_filter($ads, function($ad) use ($q,$category){

    if ($category && strtolower($ad["category"]) !== $category)
        return false;

    if ($q && !str_contains(strtolower($ad["title"].$ad["description"]), $q))
        return false;

    return true;
});

if ($sort === "date") {
    usort($filtered,function($a,$b){
        return $b["timestamp"] <=> $a["timestamp"];
    });
}

$offset  = ($page - 1) * $pageSize;
$pageAds = array_slice($filtered, $offset, $pageSize);

echo json_encode([
    "ads"   => $pageAds,
    "page"  => $page,
    "total" => count($filtered)
], JSON_PRETTY_PRINT);
exit;
