<?php
/********************************************
 * Database.php
 * SQLite Database Wrapper for AdSphere
 * Handles connections, queries, caching, and locking
 ********************************************/

class Database {

    private static $instance = null;
    private $db = null;
    private $dbPath;
    private $cacheEnabled = true;
    private $cachePrefix = 'adsphere_';

    /**
     * Private constructor for singleton
     */
    private function __construct() {
        $this->dbPath = __DIR__ . '/adsphere.db';
        $this->connect();
        $this->initializeSchema();
    }

    /**
     * Get singleton instance
     */
    public static function getInstance() {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /**
     * Connect to SQLite database
     */
    private function connect() {
        try {
            $this->db = new PDO('sqlite:' . $this->dbPath);
            $this->db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
            $this->db->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

            // Enable foreign keys
            $this->db->exec('PRAGMA foreign_keys = ON');

            // Performance optimizations
            $this->db->exec('PRAGMA synchronous = NORMAL');
            $this->db->exec('PRAGMA journal_mode = WAL');
            $this->db->exec('PRAGMA temp_store = MEMORY');
            $this->db->exec('PRAGMA cache_size = -64000'); // 64MB cache

        } catch (PDOException $e) {
            error_log("Database connection failed: " . $e->getMessage());
            throw $e;
        }
    }

    /**
     * Initialize schema if not exists
     */
    private function initializeSchema() {
        // Check if schema is initialized
        $tables = $this->query("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'");

        if (empty($tables)) {
            $schemaFile = __DIR__ . '/schema.sql';
            if (file_exists($schemaFile)) {
                $sql = file_get_contents($schemaFile);
                $this->db->exec($sql);
            }
        }
    }

    /**
     * Execute a query and return results
     */
    public function query($sql, $params = []) {
        try {
            $stmt = $this->db->prepare($sql);
            $stmt->execute($params);
            return $stmt->fetchAll();
        } catch (PDOException $e) {
            error_log("Query failed: " . $e->getMessage() . " | SQL: " . $sql);
            return false;
        }
    }

    /**
     * Execute a query and return single row
     */
    public function queryOne($sql, $params = []) {
        try {
            $stmt = $this->db->prepare($sql);
            $stmt->execute($params);
            return $stmt->fetch();
        } catch (PDOException $e) {
            error_log("QueryOne failed: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Execute an INSERT/UPDATE/DELETE and return affected rows
     */
    public function execute($sql, $params = []) {
        try {
            $stmt = $this->db->prepare($sql);
            $stmt->execute($params);
            return $stmt->rowCount();
        } catch (PDOException $e) {
            error_log("Execute failed: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Insert and return last insert ID
     */
    public function insert($sql, $params = []) {
        try {
            $stmt = $this->db->prepare($sql);
            $stmt->execute($params);
            return $this->db->lastInsertId();
        } catch (PDOException $e) {
            error_log("Insert failed: " . $e->getMessage());
            return false;
        }
    }

    /**
     * Begin transaction
     */
    public function beginTransaction() {
        return $this->db->beginTransaction();
    }

    /**
     * Commit transaction
     */
    public function commit() {
        return $this->db->commit();
    }

    /**
     * Rollback transaction
     */
    public function rollback() {
        return $this->db->rollBack();
    }

    /**
     * Cache get with automatic expiration
     */
    public function cacheGet($key) {
        if (!$this->cacheEnabled) return null;

        $fullKey = $this->cachePrefix . $key;
        $now = time();

        $result = $this->queryOne(
            "SELECT cache_value FROM cache WHERE cache_key = ? AND expires_at > ?",
            [$fullKey, $now]
        );

        if ($result) {
            return json_decode($result['cache_value'], true);
        }

        return null;
    }

    /**
     * Cache set with TTL
     */
    public function cacheSet($key, $value, $ttl = 3600) {
        if (!$this->cacheEnabled) return false;

        $fullKey = $this->cachePrefix . $key;
        $expiresAt = time() + $ttl;
        $jsonValue = json_encode($value);

        return $this->execute(
            "INSERT OR REPLACE INTO cache (cache_key, cache_value, expires_at) VALUES (?, ?, ?)",
            [$fullKey, $jsonValue, $expiresAt]
        );
    }

    /**
     * Cache delete
     */
    public function cacheDelete($key) {
        $fullKey = $this->cachePrefix . $key;
        return $this->execute("DELETE FROM cache WHERE cache_key = ?", [$fullKey]);
    }

    /**
     * Cache clear (all or by pattern)
     */
    public function cacheClear($pattern = null) {
        if ($pattern) {
            $fullPattern = $this->cachePrefix . $pattern . '%';
            return $this->execute("DELETE FROM cache WHERE cache_key LIKE ?", [$fullPattern]);
        } else {
            return $this->execute("DELETE FROM cache");
        }
    }

    /**
     * File locking mechanism
     */
    public function acquireLock($lockName, $timeout = 30) {
        $lockFile = __DIR__ . "/locks/{$lockName}.lock";
        $lockDir = dirname($lockFile);

        if (!is_dir($lockDir)) {
            mkdir($lockDir, 0755, true);
        }

        $fp = fopen($lockFile, 'c');
        $start = time();

        while (true) {
            if (flock($fp, LOCK_EX | LOCK_NB)) {
                return $fp;
            }

            if (time() - $start >= $timeout) {
                fclose($fp);
                return false;
            }

            usleep(100000); // 100ms
        }
    }

    /**
     * Release file lock
     */
    public function releaseLock($fp) {
        if ($fp && is_resource($fp)) {
            flock($fp, LOCK_UN);
            fclose($fp);
            return true;
        }
        return false;
    }

    /**
     * Get database statistics
     */
    public function getStats() {
        return [
            'database_size' => filesize($this->dbPath),
            'total_ads' => $this->queryOne("SELECT COUNT(*) as count FROM ads")['count'],
            'total_companies' => $this->queryOne("SELECT COUNT(*) as count FROM companies")['count'],
            'total_views' => $this->queryOne("SELECT COUNT(*) as count FROM ad_views")['count'],
            'total_contacts' => $this->queryOne("SELECT COUNT(*) as count FROM ad_contacts")['count'],
            'cache_entries' => $this->queryOne("SELECT COUNT(*) as count FROM cache")['count']
        ];
    }

    /**
     * Optimize database
     */
    public function optimize() {
        $this->db->exec('VACUUM');
        $this->db->exec('ANALYZE');
        return true;
    }

    /**
     * Backup database
     */
    public function backup($destination = null) {
        if (!$destination) {
            $destination = __DIR__ . '/backups/adsphere_' . date('Y-m-d_His') . '.db';
        }

        $backupDir = dirname($destination);
        if (!is_dir($backupDir)) {
            mkdir($backupDir, 0755, true);
        }

        return copy($this->dbPath, $destination);
    }

    /**
     * Full-text search
     */
    public function searchAds($query, $limit = 50) {
        $sql = "
            SELECT a.* FROM ads a
            JOIN ads_fts ON ads_fts.ad_id = a.ad_id
            WHERE ads_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        ";

        return $this->query($sql, [$query, $limit]);
    }

    /**
     * Prevent cloning
     */
    private function __clone() {}

    /**
     * Prevent unserialization
     */
    public function __wakeup() {
        throw new Exception("Cannot unserialize singleton");
    }
}

