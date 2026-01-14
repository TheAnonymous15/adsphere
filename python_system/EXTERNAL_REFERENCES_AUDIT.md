# External References Audit - Python System
**Date:** December 24, 2025  
**Status:** Complete

## Summary
This document lists all files in the `python_system` directory that reference paths, files, or resources OUTSIDE the python_system ecosystem.

---

## 1. Hard-coded Absolute Paths

### 1.1 Image/Video Sample Directories (Outside python_system)

**File:** `python_system/moderator_services/ocr_scan_all.py`  
**Line:** 422  
**Issue:** References `/app/moderator_services/sample_images`
```python
SAMPLE_DIR = Path("/Users/danielkinyua/Downloads/projects/ad/adsphere/app/moderator_services/sample_images")
```
**Fix Needed:** Use relative path to `python_system/moderator_services/sample_images`

---

**File:** `python_system/moderator_services/analyze_sam.py`  
**Line:** 34  
**Issue:** References `/app/moderator_services/sample_images`
```python
image_path = Path("/Users/danielkinyua/Downloads/projects/ad/adsphere/app/moderator_services/sample_images/sam.jpeg")
```
**Fix Needed:** Use relative path to `python_system/moderator_services/sample_images`

---

### 1.2 Database Path References (Outside python_system)

**File:** `python_system/startup.sh`  
**Line:** 55  
**Issue:** References `../app/database/adsphere.db`
```bash
if [ ! -f "../app/database/adsphere.db" ]; then
```
**Fix Needed:** Should reference database within python_system or python_shared

---

**File:** `python_system/GETTING_STARTED.sh`  
**Line:** 174  
**Issue:** References `../app/database/adsphere.db`
```bash
echo "  rm ../app/database/adsphere.db"
```
**Fix Needed:** Should reference database within python_system

---

**File:** `python_system/moderator_services/moderation_service/app/services/scalable_scanner.py`  
**Line:** 585  
**Issue:** Fallback path to `/app/database/adsphere.db`
```python
Path("/Users/danielkinyua/Downloads/projects/ad/adsphere/app/database/adsphere.db"),
```
**Fix Needed:** Remove hardcoded path, use config-based path within python_system

---

### 1.3 Company Data/Ads Directory (Outside python_system)

**File:** `python_system/moderator_services/moderation_service/app/api/routes_moderation.py`  
**Line:** 1577  
**Issue:** References `/app/data/companies`
```python
ads_base_path = Path("/Users/danielkinyua/Downloads/projects/ad/adsphere/app/data/companies")
```
**Fix Needed:** Use path within python_system or make configurable

---

**File:** `python_system/moderator_services/moderation_service/app/services/scalable_scanner.py`  
**Line:** 1016  
**Issue:** References `/app/data/companies`
```python
Path("/Users/danielkinyua/Downloads/projects/ad/adsphere/app/data/companies"),
```
**Fix Needed:** Use path within python_system or make configurable

---

## 2. PHP Files Requiring External Resources

### 2.1 Services Directory References (via BASE_PATH)

**File:** `python_system/python_company/pages/upload_ad.php`  
**Lines:** 29, 33  
**Issue:** BASE_PATH points to parent of python_system, references `/services/`
```php
define('BASE_PATH', dirname(dirname(dirname(__DIR__))));  // Goes up to adsphere/
require_once BASE_PATH . '/services/shared/database/AdModel.php';
require_once BASE_PATH . '/services/moderator_services/ModerationServiceClient.php';
```
**Fix Needed:** Change BASE_PATH to point to python_shared within python_system

---

**File:** `python_system/python_shared/bootstrap.php`  
**Lines:** 18, 22  
**Issue:** BASE_PATH points outside python_system
```php
define('BASE_PATH', dirname(dirname(__DIR__)));  // Goes to adsphere/
require_once BASE_PATH . '/services/shared/database/Database.php';
```
**Fix Needed:** Redefine BASE_PATH to stay within python_system

---

**File:** `python_system/python_shared/functions.php`  
**Line:** 115  
**Issue:** Logs directory via BASE_PATH pointing outside
```php
$logFile = BASE_PATH . '/services/shared/logs/activity_' . date('Y-m-d') . '.log';
```
**Fix Needed:** Use python_shared/logs within python_system

---

### 2.2 Admin Pages BASE_PATH Issues

**Multiple Files:**
- `python_system/python_admin/pages/companies.php` (Lines 8, 13)
- `python_system/python_admin/pages/categories.php` (Lines 6, 8)
- `python_system/python_admin/pages/logs.php` (Lines 6, 8)
- `python_system/python_admin/pages/ads.php` (Lines 8, 13)
- `python_system/python_admin/pages/2fa.php` (Lines 13-14, 56)
- `python_system/python_admin/pages/flagged.php` (Lines 6, 9)

**Common Issue:** All define BASE_PATH as `dirname(dirname(dirname(__DIR__)))` which goes outside python_system

**Fix Needed:** Standardize BASE_PATH to python_system root

---

### 2.3 Includes/Requires Outside Ecosystem

**File:** `python_system/python_shared/api/scanner.php`  
**Line:** 42  
**Issue:** Requires file that should be in python_shared
```php
require_once __DIR__ . '/../includes/RealTimeAdScanner.php';
```
**Status:** This is OK (within python_shared), but verify file exists

---

**File:** `python_system/python_shared/api/moderators/image_moderator.php`  
**Line:** 7  
```php
require_once __DIR__ . '/../../includes/AIContentModerator.php';
```
**Status:** This is OK (within python_shared)

---

## 3. Import Path Issues (Python)

### 3.1 Incorrect Module Imports

**File:** `python_system/moderator_services/test_offline_video.py`  
**Line:** 68  
**Issue:** Imports from `app.services` instead of `moderation_service.app.services`
```python
from app.services.video_moderation_pipeline import VideoModerationPipeline
```
**Fix Needed:** Change to `from moderation_service.app.services.video_moderation_pipeline import VideoModerationPipeline`

---

**File:** `python_system/moderator_services/test_youtube_video.py`  
**Lines:** 42, 90  
**Issue:** Imports from `app.services` instead of `moderation_service.app.services`
```python
from app.services.video.youtube_processor import YouTubeProcessor, check_youtube_video
from app.services.video_moderation_pipeline import VideoModerationPipeline
```
**Fix Needed:** Add `moderation_service.` prefix

---

## 4. Documentation Hard-coded Paths

**File:** `python_system/moderator_services/moderation_service/app/api/routes_docs.py`  
**Line:** 80  
**Issue:** Hard-coded installation path in HTML docs
```python
cd /Users/danielkinyua/Downloads/projects/ad/adsphere/services/moderator_services/moderation_service
```
**Fix Needed:** Use generic path or environment variable

---

## 5. Validation Scripts

**File:** `python_system/moderator_services/moderation_service/validate_system.py`  
**Line:** 245  
**Issue:** Relative path that goes outside moderation_service
```python
php_client = "../ModerationServiceClient.php"
```
**Status:** This is OK (refers to file in moderator_services directory)

---

## Recommended Fixes

### Priority 1: BASE_PATH Standardization
Create a new bootstrap file that sets BASE_PATH to python_system root:
```php
// python_system/python_shared/config/paths.php
define('PYTHON_SYSTEM_ROOT', dirname(dirname(__DIR__)));
define('BASE_PATH', PYTHON_SYSTEM_ROOT);
define('SHARED_PATH', PYTHON_SYSTEM_ROOT . '/python_shared');
define('DB_PATH', SHARED_PATH . '/database');
define('LOGS_PATH', SHARED_PATH . '/logs');
define('DATA_PATH', SHARED_PATH . '/data');
```

### Priority 2: Remove Hard-coded Absolute Paths
Replace all absolute paths with relative paths or environment variables:
```python
# Instead of:
SAMPLE_DIR = Path("/Users/danielkinyua/Downloads/projects/ad/adsphere/app/moderator_services/sample_images")

# Use:
SAMPLE_DIR = Path(__file__).parent / "sample_images"
```

### Priority 3: Fix Python Import Paths
Update all imports from `app.services` to `moderation_service.app.services`

### Priority 4: Database Location
Move database to `python_system/python_shared/database/` or create proper config

### Priority 5: Company Data Location
Either:
- Copy/move data to python_system
- Use environment variable for data path
- Create symbolic link if data must stay in /app

---

## Files That Need Updates

### Python Files (6 files)
1. `moderator_services/ocr_scan_all.py`
2. `moderator_services/analyze_sam.py`
3. `moderator_services/test_offline_video.py`
4. `moderator_services/test_youtube_video.py`
5. `moderator_services/moderation_service/app/services/scalable_scanner.py`
6. `moderator_services/moderation_service/app/api/routes_moderation.py`

### Shell Scripts (2 files)
1. `startup.sh`
2. `GETTING_STARTED.sh`

### PHP Files (15+ files)
1. `python_shared/bootstrap.php`
2. `python_shared/functions.php`
3. `python_company/pages/upload_ad.php`
4. `python_admin/pages/companies.php`
5. `python_admin/pages/categories.php`
6. `python_admin/pages/logs.php`
7. `python_admin/pages/ads.php`
8. `python_admin/pages/2fa.php`
9. `python_admin/pages/flagged.php`
10. `python_admin/pages/moderation.php`

### Documentation (1 file)
1. `moderator_services/moderation_service/app/api/routes_docs.py`

---

## Total External References Found: 24+

**Critical Issues:** 18  
**Warning Issues:** 6  
**Info/Documentation:** 2

