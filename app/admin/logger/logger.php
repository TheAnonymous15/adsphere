<?php
/*****************************************************
 * Logger library
 * Logs events inside admin/logger/logs/
 *****************************************************/

class Logger {

    private static function getLogPath($type) {
        $dir = __DIR__ . "/logs/";

        if (!is_dir($dir)) {
            mkdir($dir, 0750, true);
        }

        return $dir . $type . ".log";
    }

    // Main method called by login, yubikey verification, etc
    public static function write($type, $username, $event, $yubiID = null) {

        $ip = $_SERVER['REMOTE_ADDR'] ?? "UNKNOWN";

        $location = self::getApproxLocation($ip); // returns city,country if implemented

        $time = date("Y-m-d H:i:s");

        $entry = json_encode([
            "timestamp" => $time,
            "username"  => $username,
            "ip"        => $ip,
            "location"  => $location,
            "yubi_uid"  => $yubiID,
            "event"     => $event,
        ], JSON_UNESCAPED_SLASHES);

        $path = self::getLogPath($type);

        file_put_contents($path, $entry . PHP_EOL, FILE_APPEND | LOCK_EX);
    }

    /*****************************************************
     * Stub for location lookup
     * Plug in MaxMind or ip-api.com later
     *****************************************************/
    private static function getApproxLocation($ip) {
        // ❗ Do NOT call external APIs in here yet
        // return "Unknown Location";

        // Example future integration:
        // $json = file_get_contents("http://ip-api.com/json/$ip");
        // $data = json_decode($json,true);
        // return $data['city'] . "," . $data['country'];

        return null;
    }
}
