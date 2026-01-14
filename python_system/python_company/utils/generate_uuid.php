<?php

function generate_ad_id() {

    // timestamp + milliseconds
    $micro = microtime(true);
    $date = new DateTime();
    $date->setTimestamp((int)$micro);

    $Y  = $date->format("Y");
    $m  = $date->format("m");

    // HHMMSS + 4 extra digits from micros
    $timePart = $date->format("His") . substr((string)$micro, -5);

    // generate 5 random chars
    $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    
    $rand = "";
    for ($i = 0; $i < 6; $i++) {
        $rand .= $chars[random_int(0, strlen($chars)-1)];
    }

    return "AD-$Y$m-$timePart-$rand";
}
