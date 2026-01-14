<?php
/**
 * AI Search API
 * Communicates with the moderation service's search assistant via WebSocket
 * Falls back to REST API if WebSocket unavailable
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Configuration
define('SEARCH_SERVICE_HOST', getenv('SEARCH_SERVICE_HOST') ?: 'localhost');
define('SEARCH_SERVICE_PORT', getenv('SEARCH_SERVICE_PORT') ?: '8002');
define('SEARCH_SERVICE_URL', 'http://' . SEARCH_SERVICE_HOST . ':' . SEARCH_SERVICE_PORT);
define('SEARCH_WS_URL', 'ws://' . SEARCH_SERVICE_HOST . ':' . SEARCH_SERVICE_PORT . '/ws/search');
define('SEARCH_TIMEOUT', 5); // seconds

/**
 * WebSocket client for search service
 */
class WebSocketSearchClient {
    private $socket = null;
    private $host;
    private $port;
    private $path;
    private $connected = false;

    public function __construct(string $url) {
        $parsed = parse_url($url);
        $this->host = $parsed['host'] ?? 'localhost';
        $this->port = $parsed['port'] ?? 8002;
        $this->path = $parsed['path'] ?? '/ws/search';
    }

    public function connect(): bool {
        try {
            $this->socket = @fsockopen($this->host, $this->port, $errno, $errstr, 3);

            if (!$this->socket) {
                return false;
            }

            // Perform WebSocket handshake
            $key = base64_encode(random_bytes(16));
            $headers = [
                "GET {$this->path} HTTP/1.1",
                "Host: {$this->host}:{$this->port}",
                "Upgrade: websocket",
                "Connection: Upgrade",
                "Sec-WebSocket-Key: {$key}",
                "Sec-WebSocket-Version: 13",
                "",
                ""
            ];

            fwrite($this->socket, implode("\r\n", $headers));

            // Read response
            $response = '';
            while (($line = fgets($this->socket)) !== false) {
                $response .= $line;
                if ($line === "\r\n") break;
            }

            // Check for successful upgrade
            if (strpos($response, '101') !== false && stripos($response, 'upgrade') !== false) {
                $this->connected = true;
                stream_set_timeout($this->socket, SEARCH_TIMEOUT);
                return true;
            }

            fclose($this->socket);
            return false;

        } catch (Exception $e) {
            return false;
        }
    }

    public function send(array $data): bool {
        if (!$this->connected || !$this->socket) {
            return false;
        }

        $json = json_encode($data);
        $frame = $this->createFrame($json);

        return fwrite($this->socket, $frame) !== false;
    }

    public function receive(): ?array {
        if (!$this->connected || !$this->socket) {
            return null;
        }

        try {
            // Read frame header
            $header = fread($this->socket, 2);
            if (strlen($header) < 2) return null;

            $opcode = ord($header[0]) & 0x0F;
            $masked = (ord($header[1]) & 0x80) !== 0;
            $length = ord($header[1]) & 0x7F;

            // Extended payload length
            if ($length === 126) {
                $ext = fread($this->socket, 2);
                $length = unpack('n', $ext)[1];
            } elseif ($length === 127) {
                $ext = fread($this->socket, 8);
                $length = unpack('J', $ext)[1];
            }

            // Read mask if present
            $mask = '';
            if ($masked) {
                $mask = fread($this->socket, 4);
            }

            // Read payload
            $payload = '';
            while (strlen($payload) < $length) {
                $chunk = fread($this->socket, $length - strlen($payload));
                if ($chunk === false) break;
                $payload .= $chunk;
            }

            // Unmask if needed
            if ($masked && $mask) {
                for ($i = 0; $i < strlen($payload); $i++) {
                    $payload[$i] = $payload[$i] ^ $mask[$i % 4];
                }
            }

            // Handle different opcodes
            if ($opcode === 0x08) { // Close
                $this->close();
                return null;
            }

            if ($opcode === 0x01) { // Text frame
                return json_decode($payload, true);
            }

            return null;

        } catch (Exception $e) {
            return null;
        }
    }

    public function close(): void {
        if ($this->socket) {
            // Send close frame
            $frame = chr(0x88) . chr(0x80) . random_bytes(4);
            @fwrite($this->socket, $frame);
            @fclose($this->socket);
            $this->socket = null;
            $this->connected = false;
        }
    }

    private function createFrame(string $data): string {
        $length = strlen($data);
        $frame = chr(0x81); // Text frame, FIN bit set

        // Mask key (required for client->server)
        $mask = random_bytes(4);

        if ($length <= 125) {
            $frame .= chr(0x80 | $length);
        } elseif ($length <= 65535) {
            $frame .= chr(0x80 | 126) . pack('n', $length);
        } else {
            $frame .= chr(0x80 | 127) . pack('J', $length);
        }

        $frame .= $mask;

        // Mask the data
        for ($i = 0; $i < $length; $i++) {
            $frame .= $data[$i] ^ $mask[$i % 4];
        }

        return $frame;
    }

    public function isConnected(): bool {
        return $this->connected;
    }
}

/**
 * Search via WebSocket
 */
function searchViaWebSocket(string $query, int $topK = 5, float $threshold = 0.25, ?array $categories = null): ?array {
    $ws = new WebSocketSearchClient(SEARCH_WS_URL);

    if (!$ws->connect()) {
        return null; // WebSocket not available
    }

    try {
        // Send search request
        $request = [
            'action' => 'search',
            'query' => $query,
            'top_k' => $topK,
            'threshold' => $threshold
        ];

        if ($categories) {
            $request['categories'] = $categories;
        }

        if (!$ws->send($request)) {
            $ws->close();
            return null;
        }

        // Receive response
        $response = $ws->receive();
        $ws->close();

        return $response;

    } catch (Exception $e) {
        $ws->close();
        return null;
    }
}

/**
 * Quick search via WebSocket (just slugs)
 */
function quickSearchViaWebSocket(string $query, int $topK = 3): ?array {
    $ws = new WebSocketSearchClient(SEARCH_WS_URL);

    if (!$ws->connect()) {
        return null;
    }

    try {
        $ws->send([
            'action' => 'quick',
            'query' => $query,
            'top_k' => $topK
        ]);

        $response = $ws->receive();
        $ws->close();

        return $response;

    } catch (Exception $e) {
        $ws->close();
        return null;
    }
}

/**
 * Make REST API request (fallback)
 */
function callSearchServiceREST(string $endpoint, array $data = [], string $method = 'GET'): array {
    $url = SEARCH_SERVICE_URL . '/moderate/search/' . ltrim($endpoint, '/');

    $ch = curl_init();

    if ($method === 'POST') {
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, ['Content-Type: application/json']);
    } elseif ($method === 'GET' && !empty($data)) {
        $url .= '?' . http_build_query($data);
    }

    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => SEARCH_TIMEOUT,
        CURLOPT_CONNECTTIMEOUT => 3,
    ]);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $error = curl_error($ch);
    curl_close($ch);

    if ($error) {
        return ['success' => false, 'error' => 'Service unavailable: ' . $error];
    }

    if ($httpCode !== 200) {
        return ['success' => false, 'error' => 'Service error: HTTP ' . $httpCode];
    }

    $decoded = json_decode($response, true);
    return $decoded ?: ['success' => false, 'error' => 'Invalid response'];
}

/**
 * Fallback keyword matching when service is unavailable
 */
function fallbackKeywordMatch(string $query, array $categories): array {
    $query = strtolower(trim($query));
    if (empty($query)) {
        return [];
    }

    // Keyword mappings
    $keywordMap = [
        'food' => ['eat', 'eating', 'hungry', 'meal', 'restaurant', 'cook', 'cooking',
                   'breakfast', 'lunch', 'dinner', 'snack', 'drink', 'grocery', 'kitchen',
                   'chef', 'delicious', 'tasty', 'cuisine', 'dining', 'cafe', 'pizza',
                   'burger', 'coffee', 'tea', 'bakery'],
        'electronics' => ['tv', 'television', 'radio', 'phone', 'smartphone', 'laptop',
                         'computer', 'pc', 'tablet', 'gadget', 'device', 'tech', 'technology',
                         'gaming', 'console', 'headphone', 'speaker', 'camera', 'printer',
                         'monitor', 'keyboard', 'wifi', 'bluetooth', 'smart', 'digital'],
        'housing' => ['house', 'home', 'apartment', 'flat', 'rent', 'rental', 'lease',
                     'buy', 'sell', 'property', 'real estate', 'room', 'bedroom',
                     'land', 'plot', 'building', 'condo', 'villa', 'mortgage', 'tenant'],
        'vehicles' => ['car', 'vehicle', 'auto', 'automobile', 'truck', 'van', 'suv',
                      'motorcycle', 'bike', 'bicycle', 'scooter', 'drive', 'driving',
                      'fuel', 'petrol', 'diesel', 'engine', 'tire', 'wheel', 'transport'],
        'fashion' => ['clothes', 'clothing', 'dress', 'shirt', 'pants', 'jeans', 'shoes',
                     'jacket', 'coat', 'sweater', 'bag', 'handbag', 'watch', 'jewelry',
                     'accessory', 'fashion', 'style', 'outfit', 'wear', 'designer'],
        'health' => ['health', 'healthy', 'medical', 'medicine', 'doctor', 'hospital',
                    'clinic', 'pharmacy', 'fitness', 'gym', 'workout', 'exercise',
                    'wellness', 'beauty', 'skincare', 'makeup', 'spa', 'diet', 'nutrition'],
        'jobs' => ['job', 'jobs', 'work', 'working', 'career', 'employment', 'hire',
                  'hiring', 'recruit', 'resume', 'cv', 'interview', 'salary', 'wage',
                  'office', 'remote', 'freelance', 'part-time', 'full-time', 'vacancy'],
        'services' => ['service', 'repair', 'fix', 'install', 'maintenance', 'cleaning',
                      'plumber', 'electrician', 'carpenter', 'painting', 'delivery',
                      'catering', 'event', 'photography', 'consulting', 'legal', 'insurance'],
        'education' => ['school', 'college', 'university', 'study', 'learn', 'learning',
                       'course', 'class', 'lesson', 'tutor', 'teacher', 'student', 'degree',
                       'training', 'workshop', 'online', 'book', 'exam', 'scholarship'],
        'travel' => ['travel', 'trip', 'vacation', 'holiday', 'tour', 'tourism',
                    'flight', 'airline', 'hotel', 'resort', 'booking', 'ticket',
                    'beach', 'mountain', 'safari', 'adventure', 'destination', 'cruise'],
        'sports' => ['sport', 'sports', 'football', 'soccer', 'basketball', 'tennis',
                    'swimming', 'running', 'gym', 'fitness', 'workout', 'athlete',
                    'team', 'match', 'game', 'league', 'tournament', 'cycling'],
        'entertainment' => ['movie', 'film', 'cinema', 'music', 'concert', 'show', 'tv',
                           'streaming', 'netflix', 'game', 'gaming', 'party', 'club',
                           'dance', 'art', 'museum', 'festival', 'comedy', 'fun'],
        'furniture' => ['furniture', 'sofa', 'couch', 'chair', 'table', 'desk', 'bed',
                       'mattress', 'wardrobe', 'cabinet', 'shelf', 'lamp', 'curtain',
                       'carpet', 'decor', 'decoration', 'interior', 'home'],
        'pets' => ['pet', 'pets', 'dog', 'cat', 'puppy', 'kitten', 'bird', 'fish',
                  'animal', 'vet', 'veterinary', 'pet food', 'adoption', 'grooming'],
        'books' => ['book', 'books', 'reading', 'read', 'novel', 'fiction', 'magazine',
                   'newspaper', 'library', 'ebook', 'audiobook', 'author', 'literature']
    ];

    $results = [];
    $queryWords = explode(' ', $query);

    foreach ($categories as $cat) {
        $slug = strtolower($cat['slug'] ?? $cat['category_slug'] ?? '');
        $name = strtolower($cat['name'] ?? $cat['category_name'] ?? $slug);
        $score = 0.0;

        // Direct match with category name
        if ($query === $slug || $query === $name) {
            $score = 1.0;
        } elseif (strpos($name, $query) !== false || strpos($slug, $query) !== false) {
            $score = 0.85;
        } elseif (strpos($query, $name) !== false || strpos($query, $slug) !== false) {
            $score = 0.8;
        }

        // Check keyword mappings
        if ($score < 0.7 && isset($keywordMap[$slug])) {
            foreach ($keywordMap[$slug] as $keyword) {
                if ($query === $keyword) {
                    $score = max($score, 0.95);
                    break;
                } elseif (strpos($keyword, $query) !== false || strpos($query, $keyword) !== false) {
                    $score = max($score, 0.75);
                }
                // Check individual query words
                foreach ($queryWords as $word) {
                    if (strlen($word) >= 3 && (strpos($keyword, $word) !== false || strpos($word, $keyword) !== false)) {
                        $score = max($score, 0.6);
                    }
                }
            }
        }

        if ($score >= 0.25) {
            $results[] = [
                'slug' => $slug,
                'name' => $cat['name'] ?? $cat['category_name'] ?? ucfirst($slug),
                'score' => round($score, 4),
                'match_type' => 'keyword_fallback'
            ];
        }
    }

    // Sort by score descending
    usort($results, fn($a, $b) => $b['score'] <=> $a['score']);

    return array_slice($results, 0, 5);
}

/**
 * Get categories from database
 */
function getCategoriesFromDB(): array {
    $dbPath = dirname(__DIR__) . '/shared/database/adsphere.db';

    if (!file_exists($dbPath)) {
        // Try alternate path
        $dbPath = dirname(dirname(__DIR__)) . '/shared/database/adsphere.db';
    }

    if (!file_exists($dbPath)) {
        return [];
    }

    try {
        $db = new PDO('sqlite:' . $dbPath);
        $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

        $stmt = $db->query("SELECT category_slug, category_name FROM categories ORDER BY category_name");
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    } catch (PDOException $e) {
        error_log('DB error: ' . $e->getMessage());
        return [];
    }
}

// Main API handling
$action = $_GET['action'] ?? $_POST['action'] ?? 'search';
$query = trim($_GET['query'] ?? $_POST['query'] ?? '');

switch ($action) {
    case 'search':
    case 'match':
        if (empty($query)) {
            echo json_encode([
                'success' => false,
                'error' => 'Query is required',
                'results' => []
            ]);
            exit;
        }

        // Get categories from database
        $categories = getCategoriesFromDB();
        $topK = intval($_GET['limit'] ?? 5);
        $threshold = floatval($_GET['threshold'] ?? 0.25);

        // Prepare categories for API
        $apiCategories = array_map(function($cat) {
            return [
                'slug' => $cat['category_slug'],
                'name' => $cat['category_name']
            ];
        }, $categories);

        // Try WebSocket first
        $result = searchViaWebSocket($query, $topK, $threshold, $apiCategories);

        if ($result && ($result['success'] ?? false)) {
            echo json_encode([
                'success' => true,
                'query' => $query,
                'results' => $result['results'] ?? [],
                'count' => $result['count'] ?? 0,
                'processing_time_ms' => $result['processing_time_ms'] ?? 0,
                'model_type' => $result['model_type'] ?? 'semantic',
                'source' => 'websocket'
            ]);
            exit;
        }

        // Fallback to REST API
        $restResult = callSearchServiceREST('match', [
            'query' => $query,
            'top_k' => $topK,
            'threshold' => $threshold,
            'categories' => $apiCategories
        ], 'POST');

        if ($restResult['success'] ?? false) {
            echo json_encode([
                'success' => true,
                'query' => $query,
                'results' => $restResult['results'] ?? [],
                'count' => $restResult['count'] ?? 0,
                'processing_time_ms' => $restResult['processing_time_ms'] ?? 0,
                'model_type' => $restResult['model_type'] ?? 'semantic',
                'source' => 'rest_api'
            ]);
        } else {
            // Final fallback to keyword matching
            $results = fallbackKeywordMatch($query, $categories);

            echo json_encode([
                'success' => true,
                'query' => $query,
                'results' => $results,
                'count' => count($results),
                'model_type' => 'keyword_fallback',
                'source' => 'local_fallback',
                'service_error' => $restResult['error'] ?? null
            ]);
        }
        break;

    case 'quick':
        // Quick search - just return matching category slugs
        if (empty($query)) {
            echo json_encode(['success' => true, 'matches' => []]);
            exit;
        }

        $categories = getCategoriesFromDB();
        $topK = intval($_GET['top_k'] ?? 3);

        // Try WebSocket first
        $result = quickSearchViaWebSocket($query, $topK);

        if ($result && ($result['success'] ?? false)) {
            $matches = array_column($result['results'] ?? [], 'slug');
            echo json_encode([
                'success' => true,
                'matches' => $matches,
                'source' => 'websocket'
            ]);
            exit;
        }

        // Fallback to REST
        $restResult = callSearchServiceREST('quick/' . urlencode($query), ['top_k' => $topK], 'GET');

        if ($restResult['success'] ?? false) {
            echo json_encode([
                'success' => true,
                'matches' => $restResult['matches'] ?? [],
                'source' => 'rest_api'
            ]);
        } else {
            // Fallback to local
            $results = fallbackKeywordMatch($query, $categories);
            $matches = array_column($results, 'slug');
            echo json_encode([
                'success' => true,
                'matches' => $matches,
                'source' => 'local_fallback'
            ]);
        }
        break;

    case 'categories':
        // Return all categories
        $categories = getCategoriesFromDB();
        echo json_encode([
            'success' => true,
            'categories' => array_map(function($cat) {
                return [
                    'slug' => $cat['category_slug'],
                    'name' => $cat['category_name']
                ];
            }, $categories),
            'count' => count($categories)
        ]);
        break;

    case 'health':
        // Health check - try WebSocket first
        $ws = new WebSocketSearchClient(SEARCH_WS_URL);
        $wsConnected = $ws->connect();
        if ($wsConnected) {
            $ws->close();
        }

        $restResult = callSearchServiceREST('health', [], 'GET');

        echo json_encode([
            'success' => true,
            'api_status' => 'healthy',
            'websocket_available' => $wsConnected,
            'rest_available' => ($restResult['status'] ?? '') === 'healthy',
            'service_status' => $restResult['status'] ?? 'unknown',
            'model_loaded' => $restResult['model_loaded'] ?? false
        ]);
        break;

    default:
        echo json_encode([
            'success' => false,
            'error' => 'Unknown action: ' . $action
        ]);
}

