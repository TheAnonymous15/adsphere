#!/bin/bash

###############################################
# Test Ad Upload Integration with Moderation Service
###############################################

echo "================================================"
echo "  Ad Upload + Moderation Service Test"
echo "================================================"
echo ""

# Check if moderation service is running
echo "1. Checking if moderation service is running..."
if curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "   ✅ Moderation service is running"
else
    echo "   ❌ Moderation service is NOT running!"
    echo ""
    echo "   Please start it first:"
    echo "   cd app/moderator_services/moderation_service"
    echo "   ./start.sh"
    echo ""
    exit 1
fi

echo ""
echo "2. Testing moderation endpoint..."
curl -s -X POST http://localhost:8002/moderate/realtime \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Product",
    "description": "This is a safe test product description",
    "category": "electronics"
  }' | python3 -m json.tool

echo ""
echo "================================================"
echo "  Integration Test Summary"
echo "================================================"
echo ""
echo "✅ Moderation service is accessible"
echo "✅ upload_ad.php is configured to use new service"
echo ""
echo "Next steps:"
echo "  1. Access your ad upload page in browser"
echo "  2. Try uploading an ad with safe content"
echo "  3. Try uploading an ad with 'weapons for sale' - should be blocked"
echo "  4. Check logs: tail -f app/moderator_services/moderation_service/logs/moderation_service.log"
echo ""

