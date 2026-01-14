# Path Configuration Quick Reference
**For Python System Developers**

## Overview
All paths in the python_system now use a centralized configuration system. This makes the codebase portable and maintainable.

---

## Using Paths in PHP Files

### Step 1: Load the Configuration
At the top of any PHP file that needs paths:

```php
// Load path configuration
require_once dirname(dirname(__DIR__)) . '/python_shared/config/paths.php';
```

**Note:** Adjust the `dirname()` calls based on your file's location relative to `python_shared`.

### Step 2: Use Path Constants

```php
// Database access
require_once SHARED_PATH . '/database/Database.php';
$db = Database::getInstance();

// Load AdModel
require_once SHARED_PATH . '/database/AdModel.php';

// Moderation service client
require_once MODERATOR_SERVICES_PATH . '/ModerationServiceClient.php';

// Logging
$logFile = LOGS_PATH . '/activity_' . date('Y-m-d') . '.log';

// Company data
$companyPath = COMPANIES_PATH . '/' . $companySlug;
```

---

## Available Path Constants

| Constant | Value | Purpose |
|----------|-------|---------|
| `PYTHON_SYSTEM_ROOT` | `/path/to/python_system` | Root of python_system |
| `BASE_PATH` | Same as PYTHON_SYSTEM_ROOT | Backward compatibility |
| `SHARED_PATH` | `python_system/python_shared` | Shared resources |
| `DB_PATH` | `python_shared/database` | SQLite database files |
| `LOGS_PATH` | `python_shared/logs` | Log files |
| `DATA_PATH` | `python_shared/data` | Data storage |
| `COMPANIES_PATH` | `python_shared/data/companies` | Company ads data |
| `MODERATOR_SERVICES_PATH` | `python_system/moderator_services` | Moderation services |
| `TEMPLATES_PATH` | `python_system/templates` | Template files |
| `STATIC_PATH` | `python_system/static` | Static assets |
| `PUBLIC_COMPANY_PATH` | `python_system/python_company` | Company portal |
| `ADMIN_PATH` | `python_system/python_admin` | Admin panel |

---

## Using Paths in Python Files

### For File Paths
Use relative paths with `Path(__file__)`:

```python
from pathlib import Path

# Get current file's directory
current_dir = Path(__file__).parent

# Sample images in same directory
sample_images = current_dir / "sample_images"

# Navigate up to python_system root
python_system_root = Path(__file__).parent.parent.parent
database_path = python_system_root / "python_shared" / "database" / "adsphere.db"
```

### For Module Imports
Always use full module paths:

```python
# ✅ CORRECT
from moderation_service.app.services.video_moderation_pipeline import VideoModerationPipeline
from moderation_service.app.services.video.youtube_processor import YouTubeProcessor

# ❌ INCORRECT
from app.services.video_moderation_pipeline import VideoModerationPipeline
from app.services.video.youtube_processor import YouTubeProcessor
```

---

## Common Patterns

### Pattern 1: Admin Page
```php
<?php
/**
 * Admin Page Example
 */
if (session_status() === PHP_SESSION_NONE) session_start();

// Load path configuration
require_once dirname(dirname(__DIR__)) . '/python_shared/config/paths.php';

// Load database
require_once SHARED_PATH . '/database/Database.php';
$db = Database::getInstance();

// Your code here...
?>
```

### Pattern 2: Company Page
```php
<?php
if (session_status() === PHP_SESSION_NONE) session_start();

// Load path configuration
require_once dirname(dirname(__DIR__)) . '/python_shared/config/paths.php';

if (!isset($_SESSION['company_logged_in'])) {
    header("Location: /login");
    exit;
}

// Load services
require_once SHARED_PATH . '/database/AdModel.php';
require_once MODERATOR_SERVICES_PATH . '/ModerationServiceClient.php';

// Your code here...
?>
```

### Pattern 3: API Endpoint
```php
<?php
// Load path configuration
require_once dirname(dirname(__DIR__)) . '/python_shared/config/paths.php';

header('Content-Type: application/json');

// Load database
require_once SHARED_PATH . '/database/Database.php';
$db = Database::getInstance();

// Your API logic...
echo json_encode($response);
?>
```

### Pattern 4: Python Script
```python
from pathlib import Path
import sys

# Add python_system to path if needed
python_system = Path(__file__).parent.parent.parent
sys.path.insert(0, str(python_system))

# Import from moderation service
from moderation_service.app.services.scanner import AdScanner

# Use relative paths for data
database_path = python_system / "python_shared" / "database" / "adsphere.db"
```

---

## Migration Checklist

When creating or updating files:

### For PHP Files:
- [ ] Load `python_shared/config/paths.php` at the top
- [ ] Use path constants (SHARED_PATH, DB_PATH, etc.)
- [ ] Remove any `dirname(dirname(dirname(__DIR__)))` patterns
- [ ] Remove any references to `/services/` or `/app/`
- [ ] Test with `php -l filename.php`

### For Python Files:
- [ ] Use `Path(__file__).parent` for relative paths
- [ ] Use full module paths in imports (e.g., `moderation_service.app.services.*`)
- [ ] Remove any hardcoded absolute paths
- [ ] Test imports work correctly

---

## Directory Structure

```
python_system/
├── python_shared/              # Shared resources (SHARED_PATH)
│   ├── config/
│   │   └── paths.php          # ⭐ Path configuration
│   ├── database/              # Database files (DB_PATH)
│   │   ├── Database.php
│   │   ├── AdModel.php
│   │   └── adsphere.db
│   ├── logs/                  # Log files (LOGS_PATH)
│   │   └── activity_*.log
│   ├── data/                  # Data storage (DATA_PATH)
│   │   ├── companies/         # Company data (COMPANIES_PATH)
│   │   ├── flagged_ads.json
│   │   └── ...
│   └── api/
├── python_admin/              # Admin panel (ADMIN_PATH)
│   ├── pages/
│   └── api/
├── python_company/            # Company portal (PUBLIC_COMPANY_PATH)
│   └── pages/
├── moderator_services/        # Moderation (MODERATOR_SERVICES_PATH)
│   └── moderation_service/
└── templates/                 # Templates (TEMPLATES_PATH)
```

---

## Troubleshooting

### Problem: "paths.php not found"
**Solution:** Check the relative path from your file to `python_shared/config/paths.php`

```php
// If your file is in python_admin/pages/
require_once dirname(dirname(__DIR__)) . '/python_shared/config/paths.php';

// If your file is in python_admin/api/
require_once dirname(dirname(__DIR__)) . '/python_shared/config/paths.php';

// If your file is in python_company/pages/
require_once dirname(dirname(__DIR__)) . '/python_shared/config/paths.php';
```

### Problem: "Module not found" in Python
**Solution:** Use full module path

```python
# ❌ Wrong
from app.services.scanner import AdScanner

# ✅ Correct
from moderation_service.app.services.scanner import AdScanner
```

### Problem: Database not found
**Solution:** Check database location

```bash
# Database should be at:
python_system/python_shared/database/adsphere.db

# If it's elsewhere, copy it:
cp path/to/adsphere.db python_system/python_shared/database/
```

---

## Best Practices

### ✅ DO:
- Always use path constants from paths.php
- Use relative paths in Python with `Path(__file__)`
- Use full module paths in imports
- Test your changes with `php -l` for PHP files
- Keep all data within python_system directory structure

### ❌ DON'T:
- Hardcode absolute paths like `/Users/...`
- Use `../app/` or `/services/` references
- Use `dirname(dirname(dirname(__DIR__)))` pattern
- Import with `from app.services.*` in Python
- Store data outside python_system

---

## Quick Reference Commands

```bash
# Validate PHP syntax
php -l path/to/file.php

# Test paths
php -r "require 'python_shared/config/paths.php'; echo DB_PATH;"

# Check directory structure
tree -L 3 python_shared/

# Test Python imports (from python_system directory)
python -c "from moderation_service.app.services.scanner import AdScanner; print('OK')"
```

---

**Last Updated:** December 24, 2025  
**Version:** 1.0  
**Maintainer:** Development Team

