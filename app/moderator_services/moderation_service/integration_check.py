#!/usr/bin/env python3
"""Final integration check for the moderation service"""

import sys
sys.path.insert(0, '.')

print('=== FINAL INTEGRATION CHECK ===')
print()

# 1. Check imports
print('1. Checking FastAPI app...')
try:
    from app.main import app
    print('   ✅ FastAPI app imports correctly')
except Exception as e:
    print(f'   ❌ FastAPI import error: {e}')

# 2. Check routes
print('2. Checking routes...')
try:
    from app.api.routes_moderation import router, get_pipeline
    print('   ✅ Moderation routes import correctly')
except Exception as e:
    print(f'   ❌ Routes import error: {e}')

# 3. Check master pipeline
print('3. Checking master pipeline...')
try:
    from app.services.master_pipeline import MasterModerationPipeline
    pipeline = MasterModerationPipeline()
    print('   ✅ Master pipeline initializes correctly')
except Exception as e:
    print(f'   ❌ Pipeline error: {e}')

# 4. Check schemas
print('4. Checking schemas...')
try:
    from app.models.schemas import ModerationRequest, ModerationResponse, CategoryScores
    print('   ✅ Pydantic schemas import correctly')
except Exception as e:
    print(f'   ❌ Schema error: {e}')

# 5. Check configuration
print('5. Checking configuration...')
try:
    from app.core.config import settings
    print(f'   ✅ Config loaded (version={settings.VERSION})')
except Exception as e:
    print(f'   ❌ Config error: {e}')

# 6. Test moderation
print('6. Testing moderation...')
try:
    result = pipeline.moderate_text(
        title='Test Product',
        description='This is a safe test description'
    )
    if result['decision'] == 'approve':
        print('   ✅ Text moderation working correctly')
    else:
        print(f'   ⚠ Unexpected decision: {result["decision"]}')
except Exception as e:
    print(f'   ❌ Moderation error: {e}')

print()
print('=== INTEGRATION CHECK COMPLETE ===')

