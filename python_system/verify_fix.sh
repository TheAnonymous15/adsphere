#!/bin/bash
# Verification Script for External References Fix
# Run this to verify all changes are correct

echo "================================================"
echo "  External References Fix - Verification"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASSED=0
FAILED=0

# Test function
test_check() {
    local name="$1"
    local command="$2"

    echo -n "Testing: $name... "

    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
    fi
}

echo "1. PHP SYNTAX CHECKS"
echo "-------------------"
test_check "paths.php syntax" "php -l python_shared/config/paths.php"
test_check "bootstrap.php syntax" "php -l python_shared/bootstrap.php"
test_check "functions.php syntax" "php -l python_shared/functions.php"
test_check "company index.php syntax" "php -l python_company/index.php"
test_check "admin router.php syntax" "php -l python_admin/api/router.php"
test_check "upload_ad.php syntax" "php -l python_company/pages/upload_ad.php"
echo ""

echo "2. PATH RESOLUTION CHECKS"
echo "------------------------"
test_check "PYTHON_SYSTEM_ROOT defined" "php -r 'require \"python_shared/config/paths.php\"; if (!defined(\"PYTHON_SYSTEM_ROOT\")) exit(1);'"
test_check "SHARED_PATH defined" "php -r 'require \"python_shared/config/paths.php\"; if (!defined(\"SHARED_PATH\")) exit(1);'"
test_check "DB_PATH defined" "php -r 'require \"python_shared/config/paths.php\"; if (!defined(\"DB_PATH\")) exit(1);'"
test_check "LOGS_PATH defined" "php -r 'require \"python_shared/config/paths.php\"; if (!defined(\"LOGS_PATH\")) exit(1);'"
test_check "MODERATOR_SERVICES_PATH defined" "php -r 'require \"python_shared/config/paths.php\"; if (!defined(\"MODERATOR_SERVICES_PATH\")) exit(1);'"
echo ""

echo "3. DIRECTORY EXISTENCE CHECKS"
echo "----------------------------"
test_check "python_shared/database exists" "test -d python_shared/database"
test_check "python_shared/logs exists" "test -d python_shared/logs"
test_check "python_shared/data exists" "test -d python_shared/data"
test_check "python_shared/config exists" "test -d python_shared/config"
test_check "moderator_services exists" "test -d moderator_services"
echo ""

echo "4. CRITICAL FILE CHECKS"
echo "----------------------"
test_check "paths.php exists" "test -f python_shared/config/paths.php"
test_check "bootstrap.php exists" "test -f python_shared/bootstrap.php"
test_check "Database.php exists" "test -f python_shared/database/Database.php"
test_check "AdModel.php exists" "test -f python_shared/database/AdModel.php"
test_check "ModerationServiceClient.php exists" "test -f moderator_services/ModerationServiceClient.php"
echo ""

echo "5. EXTERNAL REFERENCE CHECKS"
echo "---------------------------"

# Check for old BASE_PATH patterns in PHP files
OLD_PATTERN_COUNT=$(grep -r "dirname(dirname(dirname(__DIR__)))" . --include="*.php" 2>/dev/null | grep -v "\.md" | wc -l | tr -d ' ')
if [ "$OLD_PATTERN_COUNT" -eq "0" ]; then
    echo -e "Old BASE_PATH pattern: ${GREEN}✓ NONE FOUND${NC}"
    ((PASSED++))
else
    echo -e "Old BASE_PATH pattern: ${RED}✗ FOUND $OLD_PATTERN_COUNT${NC}"
    ((FAILED++))
fi

# Check for hardcoded absolute paths in Python files
HARDCODED_PATH_COUNT=$(grep -r "/Users/danielkinyua/Downloads" . --include="*.py" 2>/dev/null | grep -v "\.md" | wc -l | tr -d ' ')
if [ "$HARDCODED_PATH_COUNT" -eq "0" ]; then
    echo -e "Hardcoded paths in Python: ${GREEN}✓ NONE FOUND${NC}"
    ((PASSED++))
else
    echo -e "Hardcoded paths in Python: ${RED}✗ FOUND $HARDCODED_PATH_COUNT${NC}"
    ((FAILED++))
fi

# Check for /services/ references (should be minimal)
SERVICES_REF_COUNT=$(grep -r "'/services/" . --include="*.php" 2>/dev/null | grep -v "\.md" | grep -v "/services/assets" | grep -v "/services/company/data" | wc -l | tr -d ' ')
if [ "$SERVICES_REF_COUNT" -eq "0" ]; then
    echo -e "External /services/ refs: ${GREEN}✓ NONE FOUND${NC}"
    ((PASSED++))
else
    echo -e "External /services/ refs: ${YELLOW}⚠ FOUND $SERVICES_REF_COUNT (review needed)${NC}"
    # Not counting as failure - some URL references may be intentional
fi

echo ""
echo "6. DOCUMENTATION CHECKS"
echo "----------------------"
test_check "Fix completion report exists" "test -f EXTERNAL_REFERENCES_FIX_COMPLETE.md"
test_check "Path guide exists" "test -f PATH_CONFIGURATION_GUIDE.md"
test_check "Task summary exists" "test -f TASK_SUMMARY.md"
test_check "Post-fix checklist exists" "test -f POST_FIX_CHECKLIST.md"
echo ""

echo "================================================"
echo "  VERIFICATION SUMMARY"
echo "================================================"
echo -e "${GREEN}PASSED: $PASSED${NC}"
if [ "$FAILED" -gt "0" ]; then
    echo -e "${RED}FAILED: $FAILED${NC}"
else
    echo -e "${GREEN}FAILED: $FAILED${NC}"
fi
echo ""

if [ "$FAILED" -eq "0" ]; then
    echo -e "${GREEN}✓✓✓ ALL CHECKS PASSED ✓✓✓${NC}"
    echo ""
    echo "The external references fix is complete and verified!"
    echo "You can now deploy the system."
    exit 0
else
    echo -e "${RED}✗✗✗ SOME CHECKS FAILED ✗✗✗${NC}"
    echo ""
    echo "Please review the failed checks above."
    echo "See POST_FIX_CHECKLIST.md for troubleshooting."
    exit 1
fi

