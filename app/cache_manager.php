<?php
/********************************************
 * Cache Manager - AdSphere
 * Manage full-page cache and other caches
 ********************************************/

class CacheManager {

    private $pageCachePath;
    private $routesCachePath;

    public function __construct() {
        $this->pageCachePath = __DIR__ . '/../cache/pages/';
        $this->routesCachePath = __DIR__ . '/../cache/';

        // Ensure cache directories exist
        if (!is_dir($this->pageCachePath)) {
            mkdir($this->pageCachePath, 0755, true);
        }
    }

    /**
     * Clear all page caches
     */
    public function clearPageCache(): int {
        $count = 0;
        $files = glob($this->pageCachePath . '*.html');

        foreach ($files as $file) {
            if (@unlink($file)) {
                $count++;
            }
        }

        return $count;
    }

    /**
     * Clear routes cache
     */
    public function clearRoutesCache(): bool {
        $routesFile = $this->routesCachePath . 'routes_cache.php';

        if (file_exists($routesFile)) {
            return @unlink($routesFile);
        }

        return true;
    }

    /**
     * Clear all caches
     */
    public function clearAll(): array {
        return [
            'page_cache' => $this->clearPageCache(),
            'routes_cache' => $this->clearRoutesCache()
        ];
    }

    /**
     * Get cache statistics
     */
    public function getStats(): array {
        $pageFiles = glob($this->pageCachePath . '*.html');
        $totalSize = 0;
        $oldestFile = null;
        $newestFile = null;

        foreach ($pageFiles as $file) {
            $size = filesize($file);
            $time = filemtime($file);

            $totalSize += $size;

            if ($oldestFile === null || $time < filemtime($oldestFile)) {
                $oldestFile = $file;
            }

            if ($newestFile === null || $time > filemtime($newestFile)) {
                $newestFile = $file;
            }
        }

        return [
            'total_files' => count($pageFiles),
            'total_size' => $totalSize,
            'total_size_mb' => round($totalSize / 1024 / 1024, 2),
            'oldest_cache' => $oldestFile ? date('Y-m-d H:i:s', filemtime($oldestFile)) : null,
            'newest_cache' => $newestFile ? date('Y-m-d H:i:s', filemtime($newestFile)) : null
        ];
    }

    /**
     * Warm cache by visiting pages
     */
    public function warmCache(array $urls): array {
        $results = [];

        foreach ($urls as $url) {
            $ch = curl_init($url);
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);
            curl_setopt($ch, CURLOPT_TIMEOUT, 10);

            $result = curl_exec($ch);
            $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);

            curl_close($ch);

            $results[$url] = [
                'success' => $httpCode === 200,
                'http_code' => $httpCode
            ];
        }

        return $results;
    }

    /**
     * Clean expired cache files
     */
    public function cleanExpired(int $maxAge = 3600): int {
        $count = 0;
        $files = glob($this->pageCachePath . '*.html');
        $now = time();

        foreach ($files as $file) {
            if (($now - filemtime($file)) > $maxAge) {
                if (@unlink($file)) {
                    $count++;
                }
            }
        }

        return $count;
    }
}

// CLI usage
if (php_sapi_name() === 'cli') {
    $manager = new CacheManager();

    $command = $argv[1] ?? 'help';

    switch ($command) {
        case 'clear':
            $result = $manager->clearAll();
            echo "✅ Cleared {$result['page_cache']} page cache files\n";
            echo "✅ Routes cache cleared\n";
            break;

        case 'stats':
            $stats = $manager->getStats();
            echo "📊 Cache Statistics:\n";
            echo "  Total Files: {$stats['total_files']}\n";
            echo "  Total Size: {$stats['total_size_mb']} MB\n";
            echo "  Oldest: {$stats['oldest_cache']}\n";
            echo "  Newest: {$stats['newest_cache']}\n";
            break;

        case 'clean':
            $maxAge = (int)($argv[2] ?? 3600);
            $count = $manager->cleanExpired($maxAge);
            echo "✅ Cleaned $count expired cache files (older than $maxAge seconds)\n";
            break;

        case 'warm':
            echo "🔥 Warming cache...\n";
            $baseUrl = $argv[2] ?? 'http://localhost';
            $urls = [
                "$baseUrl/",
                "$baseUrl/about",
                "$baseUrl/contact"
            ];
            $results = $manager->warmCache($urls);
            foreach ($results as $url => $result) {
                $status = $result['success'] ? '✅' : '❌';
                echo "$status $url (HTTP {$result['http_code']})\n";
            }
            break;

        default:
            echo "AdSphere Cache Manager\n\n";
            echo "Usage: php cache_manager.php <command>\n\n";
            echo "Commands:\n";
            echo "  clear       - Clear all caches\n";
            echo "  stats       - Show cache statistics\n";
            echo "  clean [age] - Clean expired cache (default: 3600s)\n";
            echo "  warm [url]  - Warm cache by visiting pages\n";
            echo "  help        - Show this help\n";
            break;
    }
}

