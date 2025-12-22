<?php
/********************************************
 * includes/ads.php
 * Loads ads + merged contact details
 ********************************************/

error_reporting(E_ALL);
ini_set("display_errors", 1);

// ABSOLUTE folder path
$adsBase = __DIR__ . "/../companies/data/";

$ads = [];

// ensure base exists
if (!is_dir($adsBase)) {
    return []; // return empty array instead of echoing JSON
}

// loop categories
foreach (scandir($adsBase) as $cat) {

    if ($cat === "." || $cat === "..") continue;

    $catPath = "$adsBase/$cat";
    if (!is_dir($catPath)) continue;

    // loop company folders
    foreach (scandir($catPath) as $company) {

        if ($company === "." || $company === "..") continue;

        $compPath = "$catPath/$company";
        if (!is_dir($compPath)) continue;


        /****************************************
         * fallback contact from company metadata
         ****************************************/
        $fallbackContact = [];
        $companyMeta = "$compPath/metadata.json";

        if (file_exists($companyMeta)) {
            $json = json_decode(file_get_contents($companyMeta), true);
            if (isset($json["contact"])) {
                $fallbackContact = $json["contact"];
            }
        }

        // loop ads folders
        foreach (scandir($compPath) as $adFolder) {

            if ($adFolder === "." || $adFolder === "..") continue;

            $metaFile = "$compPath/$adFolder/meta.json";
            if (!file_exists($metaFile)) continue;

            $meta = json_decode(file_get_contents($metaFile), true);

            if (!is_array($meta)) continue;


            /****************************************
             * resolve final contact priority:
             * ad contact > company contact
             ****************************************/
            $finalContact = $fallbackContact;

            if (isset($meta["contact"]))
                $finalContact = array_merge($fallbackContact, $meta["contact"]);


            /****************************************
             * build media filename
             ****************************************/
            $mediaFilename = $meta["media"] ?? "";
            $mediaUrl = "/services/company/data/$cat/$company/$adFolder/$mediaFilename";


            /****************************************
             * push to output ads list
             ****************************************/

            // Use folder name as ad_id if not present in meta
            $adId = $meta["ad_id"] ?? $adFolder;

            // Use company from meta if present, otherwise use folder name
            $companyName = $meta["company"] ?? $company;

            $ads[] = [
                "ad_id"       => $adId,
                "title"       => $meta["title"] ?? "",
                "description" => $meta["description"] ?? "",
                "category"    => $cat,
                "company"     => $companyName,
                "media"       => $mediaUrl,
                "timestamp"   => $meta["timestamp"] ?? time(),
                "status"      => $meta["status"] ?? "active",
                "contact"     => [
                    "email"    => $finalContact["email"] ?? "",
                    "phone"    => $finalContact["phone"] ?? "",
                    "sms"      => $finalContact["sms"] ?? "",
                    "whatsapp" => $finalContact["whatsapp"] ?? ""
                ]
            ];
        }
    }
}

// RETURN ARRAY — not echo JSON
return $ads;
