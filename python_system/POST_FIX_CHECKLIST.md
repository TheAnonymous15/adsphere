# Post-Fix Deployment Checklist
**Complete these steps to finalize the external references fix**

## ✅ Immediate Actions (Required)

### 1. Verify Path Configuration
```bash
cd python_system
php -r "require 'python_shared/config/paths.php'; echo 'Paths OK: ' . SHARED_PATH;"
```
**Expected:** Should print paths without errors

### 2. Check Directory Structure
```bash
ls -la python_shared/{database,logs,data}
```
**Expected:** All directories should exist

### 3. Validate PHP Files
```bash
php -l python_shared/bootstrap.php
php -l python_company/index.php
php -l python_admin/api/router.php
```
**Expected:** "No syntax errors detected" for all files

---

## 📦 Optional Data Migration

### If You Have Existing Data

#### Option A: Copy Company Data
```bash
# If you have data in the old location
cp -r ../app/data/companies/* python_shared/data/companies/
```

#### Option B: Symbolic Link
```bash
# If you want to keep data in original location
ln -s ../app/data/companies python_shared/data/companies
```

#### Option C: Move Data
```bash
# To fully migrate
mv ../app/data/companies/* python_shared/data/companies/
```

### If You Have Existing Database
```bash
# Copy database to new location
cp ../app/database/adsphere.db python_shared/database/

# Or create symbolic link
ln -s ../app/database/adsphere.db python_shared/database/adsphere.db
```

---

## 🧪 Testing

### 1. Test Startup
```bash
cd python_system
./startup.sh
```
**Expected:** System starts without path errors

### 2. Test Admin Login
```bash
# Start admin service (if separate)
# Access: http://localhost:8001/login
```
**Expected:** Login page loads, can access dashboard

### 3. Test Company Portal
```bash
# Start company service (if separate)
# Access: http://localhost:8000/login
```
**Expected:** Company login works, upload page accessible

### 4. Test Moderation Service
```bash
cd moderator_services/moderation_service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```
**Expected:** Service starts, docs at http://localhost:8002/docs

---

## 🔍 Verification

### Check for Remaining External References
```bash
# Search for old patterns (should return no results in python_system)
grep -r "dirname(dirname(dirname(__DIR__)))" python_system/ --include="*.php" | grep -v ".md"
grep -r "/Users/danielkinyua/" python_system/ --include="*.py" | grep -v ".md"
```
**Expected:** No results (or only in markdown documentation)

### Verify Python Imports
```bash
cd python_system
python -c "from moderation_service.app.services.video_moderation_pipeline import VideoModerationPipeline; print('✅ Imports OK')"
```
**Expected:** "✅ Imports OK"

---

## 📋 Review Changes

### New Files Created:
- [x] `python_shared/config/paths.php` - Core path configuration
- [x] `EXTERNAL_REFERENCES_FIX_COMPLETE.md` - Detailed report
- [x] `PATH_CONFIGURATION_GUIDE.md` - Developer guide
- [x] `TASK_SUMMARY.md` - Quick summary
- [x] `POST_FIX_CHECKLIST.md` - This file

### Modified Files (30):
Review the following key files:
- [x] `python_shared/bootstrap.php`
- [x] `python_shared/functions.php`
- [x] `python_company/index.php`
- [x] `python_company/pages/upload_ad.php`
- [x] `python_admin/api/router.php`
- [x] All admin pages (9 files)
- [x] All Python files (6 files)
- [x] Shell scripts (2 files)

---

## 🚀 Deployment

### Development Environment
1. ✅ All changes are in place
2. ✅ Test locally with `./startup.sh`
3. ✅ Verify all services work

### Production Environment
```bash
# 1. Pull latest changes
git pull origin main

# 2. Ensure directories exist
mkdir -p python_shared/{database,logs,data/companies}

# 3. Copy/migrate data if needed
# (See "Optional Data Migration" above)

# 4. Set permissions
chmod 755 python_shared/{database,logs,data}
chmod 644 python_shared/database/*.db

# 5. Start services
./startup.sh
```

---

## 🐛 Troubleshooting

### Problem: "paths.php not found"
**Solution:**
```bash
# Verify file exists
ls -la python_shared/config/paths.php

# Check require path in your PHP file
# Should be: require_once dirname(dirname(__DIR__)) . '/python_shared/config/paths.php';
```

### Problem: Database not found
**Solution:**
```bash
# Check if database exists
ls -la python_shared/database/adsphere.db

# If not, initialize it
python database.py
```

### Problem: Permission denied
**Solution:**
```bash
# Fix permissions
chmod -R 755 python_shared/
chmod 644 python_shared/database/*.db
```

### Problem: Module not found (Python)
**Solution:**
```bash
# Make sure you're in python_system directory
cd python_system

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Use full module path in imports
# from moderation_service.app.services.* (not from app.services.*)
```

---

## 📊 Success Criteria

Your deployment is successful when:

- [x] All PHP files have no syntax errors
- [x] All path constants resolve correctly
- [x] Python imports work without errors
- [x] Services start without path-related errors
- [x] No hardcoded absolute paths remain
- [x] System is fully self-contained
- [x] Can move python_system folder without breaking

---

## 📚 Documentation

Refer to these documents for details:

1. **EXTERNAL_REFERENCES_FIX_COMPLETE.md** - Complete change log
2. **PATH_CONFIGURATION_GUIDE.md** - How to use paths in code
3. **TASK_SUMMARY.md** - Quick overview

---

## 🎯 Next Development Tasks (Optional)

### Enhancement Ideas:
1. Add `.env` support for environment-specific paths
2. Create unified config file for all settings
3. Add path validation tests
4. Create automated migration script
5. Add health check endpoints

---

## ✅ Sign-off

When all items above are complete, mark this task as done:

- [ ] Path configuration verified
- [ ] All syntax checks passed
- [ ] Data migrated (if applicable)
- [ ] All services tested
- [ ] No external references found
- [ ] Documentation reviewed
- [ ] Deployment successful

**Completed By:** ________________  
**Date:** ________________  
**Notes:** ________________

---

**Last Updated:** December 24, 2025  
**Status:** Ready for deployment

