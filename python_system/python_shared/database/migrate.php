<?php
/********************************************
 * migrate.php
 * Migrate existing file-based ads to SQLite database
 * Run once to populate database from existing files
 ********************************************/

require_once __DIR__ . '/Database.php';

class AdMigration {

    private $db;
    private $adsBase;
    private $metaBase;
    private $stats = [
        'companies' => 0,
        'categories' => 0,
        'ads' => 0,
        'errors' => []
    ];

    public function __construct() {
        $this->db = Database::getInstance();
        $this->adsBase = __DIR__ . '/../companies/data/';
        $this->metaBase = __DIR__ . '/../companies/metadata/';
    }

    /**
     * Run full migration
     */
    public function migrate() {
        echo "=== AdSphere Migration Started ===\n\n";

        $this->db->beginTransaction();

        try {
            $this->migrateCompanies();
            $this->migrateCategories();
            $this->migrateAds();

            $this->db->commit();

            echo "\n=== Migration Completed Successfully ===\n";
            $this->printStats();

        } catch (Exception $e) {
            $this->db->rollback();
            echo "\n❌ Migration failed: " . $e->getMessage() . "\n";
            $this->printStats();
        }
    }

    /**
     * Migrate companies from metadata files
     */
    private function migrateCompanies() {
        echo "Migrating companies...\n";

        if (!is_dir($this->metaBase)) {
            echo "  No metadata directory found\n";
            return;
        }

        $files = glob($this->metaBase . '*.json');

        foreach ($files as $file) {
            $companySlug = basename($file, '.json');
            $data = json_decode(file_get_contents($file), true);

            if (!$data) continue;

            $contact = $data['contact'] ?? [];

            $sql = "INSERT OR REPLACE INTO companies
                    (company_slug, company_name, email, phone, sms, whatsapp, created_at, updated_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)";

            $params = [
                $companySlug,
                $data['company_name'] ?? ucfirst($companySlug),
                $contact['email'] ?? null,
                $contact['phone'] ?? null,
                $contact['sms'] ?? null,
                $contact['whatsapp'] ?? null,
                $data['created_at'] ?? time(),
                time(),
                'active'
            ];

            if ($this->db->execute($sql, $params)) {
                $this->stats['companies']++;
                echo "  ✓ Migrated company: $companySlug\n";
            }
        }
    }

    /**
     * Migrate categories from directory structure
     */
    private function migrateCategories() {
        echo "\nMigrating categories...\n";

        if (!is_dir($this->adsBase)) {
            echo "  No ads directory found\n";
            return;
        }

        $categories = scandir($this->adsBase);

        foreach ($categories as $cat) {
            if ($cat === '.' || $cat === '..') continue;

            $catPath = $this->adsBase . $cat;
            if (!is_dir($catPath)) continue;

            // Check if category has any company folders
            $hasContent = false;
            $companies = scandir($catPath);
            foreach ($companies as $company) {
                if ($company !== '.' && $company !== '..' && is_dir("$catPath/$company")) {
                    $hasContent = true;

                    // Record company-category assignment
                    $assignSql = "INSERT OR IGNORE INTO company_categories
                                  (company_slug, category_slug, assigned_at)
                                  VALUES (?, ?, ?)";
                    $this->db->execute($assignSql, [$company, $cat, time()]);
                }
            }

            if ($hasContent) {
                $sql = "INSERT OR IGNORE INTO categories
                        (category_slug, category_name, created_at)
                        VALUES (?, ?, ?)";

                if ($this->db->execute($sql, [$cat, ucfirst($cat), time()])) {
                    $this->stats['categories']++;
                    echo "  ✓ Migrated category: $cat\n";
                }
            }
        }
    }

    /**
     * Migrate ads from file structure
     */
    private function migrateAds() {
        echo "\nMigrating ads...\n";

        $categories = scandir($this->adsBase);

        foreach ($categories as $cat) {
            if ($cat === '.' || $cat === '..') continue;

            $catPath = $this->adsBase . $cat;
            if (!is_dir($catPath)) continue;

            $companies = scandir($catPath);

            foreach ($companies as $company) {
                if ($company === '.' || $company === '..') continue;

                $companyPath = "$catPath/$company";
                if (!is_dir($companyPath)) continue;

                $ads = scandir($companyPath);

                foreach ($ads as $adId) {
                    if ($adId === '.' || $adId === '..') continue;

                    $adPath = "$companyPath/$adId";
                    if (!is_dir($adPath)) continue;

                    $metaFile = "$adPath/meta.json";
                    if (!file_exists($metaFile)) continue;

                    $meta = json_decode(file_get_contents($metaFile), true);
                    if (!$meta) continue;

                    // Find media file
                    $mediaFile = null;
                    $mediaType = null;
                    $files = scandir($adPath);
                    foreach ($files as $file) {
                        if ($file === 'meta.json' || $file === '.' || $file === '..') continue;
                        $ext = strtolower(pathinfo($file, PATHINFO_EXTENSION));
                        if (in_array($ext, ['jpg', 'jpeg', 'png', 'gif', 'webp'])) {
                            $mediaFile = $file;
                            $mediaType = 'image';
                            break;
                        } elseif (in_array($ext, ['mp4', 'webm', 'mov', 'avi'])) {
                            $mediaFile = $file;
                            $mediaType = 'video';
                            break;
                        } elseif (in_array($ext, ['mp3', 'wav', 'ogg'])) {
                            $mediaFile = $file;
                            $mediaType = 'audio';
                            break;
                        }
                    }

                    if (!$mediaFile) {
                        $this->stats['errors'][] = "No media file found for ad: $adId";
                        continue;
                    }

                    $contact = $meta['contact'] ?? [];

                    $sql = "INSERT OR REPLACE INTO ads
                            (ad_id, company_slug, category_slug, title, description,
                             media_filename, media_type, media_path,
                             contact_phone, contact_sms, contact_email, contact_whatsapp,
                             created_at, updated_at, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

                    $params = [
                        $adId,
                        $company,
                        $cat,
                        $meta['title'] ?? 'Untitled',
                        $meta['description'] ?? '',
                        $mediaFile,
                        $mediaType,
                        "$cat/$company/$adId/$mediaFile",
                        $contact['phone'] ?? null,
                        $contact['sms'] ?? null,
                        $contact['email'] ?? null,
                        $contact['whatsapp'] ?? null,
                        $meta['timestamp'] ?? time(),
                        time(),
                        'active'
                    ];

                    if ($this->db->execute($sql, $params)) {
                        $this->stats['ads']++;
                        if ($this->stats['ads'] % 10 === 0) {
                            echo "  Migrated {$this->stats['ads']} ads...\n";
                        }
                    } else {
                        $this->stats['errors'][] = "Failed to migrate ad: $adId";
                    }
                }
            }
        }

        echo "  ✓ Total ads migrated: {$this->stats['ads']}\n";
    }

    /**
     * Print migration statistics
     */
    private function printStats() {
        echo "\n=== Migration Statistics ===\n";
        echo "Companies: {$this->stats['companies']}\n";
        echo "Categories: {$this->stats['categories']}\n";
        echo "Ads: {$this->stats['ads']}\n";

        if (!empty($this->stats['errors'])) {
            echo "\nErrors (" . count($this->stats['errors']) . "):\n";
            foreach (array_slice($this->stats['errors'], 0, 10) as $error) {
                echo "  - $error\n";
            }
            if (count($this->stats['errors']) > 10) {
                echo "  ... and " . (count($this->stats['errors']) - 10) . " more\n";
            }
        }
    }

    /**
     * Dry run - preview what would be migrated
     */
    public function dryRun() {
        echo "=== Dry Run Mode ===\n\n";

        // Count metadata files
        $metaFiles = glob($this->metaBase . '*.json');
        echo "Companies to migrate: " . count($metaFiles) . "\n";

        // Count categories
        $categories = array_filter(scandir($this->adsBase), function($cat) {
            return $cat !== '.' && $cat !== '..' && is_dir($this->adsBase . $cat);
        });
        echo "Categories to migrate: " . count($categories) . "\n";

        // Count ads
        $adsCount = 0;
        foreach ($categories as $cat) {
            $companies = scandir($this->adsBase . $cat);
            foreach ($companies as $company) {
                if ($company === '.' || $company === '..') continue;
                $companyPath = $this->adsBase . "$cat/$company";
                if (!is_dir($companyPath)) continue;
                $ads = array_filter(scandir($companyPath), function($ad) use ($companyPath) {
                    return $ad !== '.' && $ad !== '..' && is_dir("$companyPath/$ad");
                });
                $adsCount += count($ads);
            }
        }
        echo "Ads to migrate: $adsCount\n";

        echo "\nRun without --dry-run to perform actual migration.\n";
    }
}

// Run migration
$migration = new AdMigration();

if (isset($argv[1]) && $argv[1] === '--dry-run') {
    $migration->dryRun();
} else {
    $confirm = readline("\n⚠️  This will migrate all existing ads to the database. Continue? (yes/no): ");
    if (strtolower(trim($confirm)) === 'yes') {
        $migration->migrate();
    } else {
        echo "Migration cancelled.\n";
    }
}

