# 🎯 USAGE GUIDE - How to Use AdSphere Python System

## Overview

The AdSphere Python system has **3 independent services** that you can run and interact with:

```
┌────────────────────────────────────────────────────────┐
│          AdSphere Python Services                      │
├────────────────────────────────────────────────────────┤
│                                                        │
│  🌐 PUBLIC (8001)     👥 COMPANY (8003)  ⚙️ ADMIN (8004)
│  Users browse ads     Ad management       Moderation  │
│  Search & view        Upload & edit       Statistics  │
│  Track interactions   Analytics           Approve ads │
│                                                        │
└────────────────────────────────────────────────────────┘
```

---

## 🚀 USAGE #1: Testing the APIs Interactively

### The Easiest Way - Use Swagger UI

1. **Start all 3 services** (see QUICK_START.md)

2. **Open in your browser:**
   - Public: http://localhost:8001/docs
   - Company: http://localhost:8003/docs
   - Admin: http://localhost:8004/docs

3. **You'll see:**
   - List of all endpoints
   - Request/response schemas
   - "Try it out" button for each endpoint

4. **Click "Try it out":**
   - Fill in parameters
   - Click "Execute"
   - See the response

**This is the best way for beginners!**

---

## 🛠️ USAGE #2: Testing with cURL (Command Line)

### Example 1: Get all ads
```bash
curl http://localhost:8001/api/ads
```

**Response:**
```json
{
  "status": "success",
  "total": 5,
  "page": 1,
  "limit": 20,
  "ads": [
    {
      "id": "AD-202512-123456",
      "title": "iPhone 13 Pro",
      "category": "Electronics",
      "view_count": 42,
      ...
    }
  ]
}
```

### Example 2: Register a user
```bash
curl -X POST http://localhost:8001/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "MyPassword123",
    "full_name": "John Doe"
  }'
```

**Response:**
```json
{
  "status": "success",
  "message": "User registered successfully",
  "user_id": 1,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Example 3: Search for ads
```bash
curl "http://localhost:8001/api/ads?search=iPhone&category=Electronics"
```

### Example 4: Track a view
```bash
curl -X POST http://localhost:8001/api/track_interaction \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "ad_id": "AD-202512-123456",
    "event_type": "view",
    "duration_seconds": 45
  }'
```

---

## 📱 USAGE #3: Using with Postman

### Step 1: Import OpenAPI Schema
1. Open Postman
2. Click "Import"
3. Paste this URL: `http://localhost:8001/openapi.json`
4. Postman will create all requests for you

### Step 2: Use Collections
- Requests are organized by endpoint
- Fill in required fields
- Click "Send"
- View response

### Step 3: Set Environment Variables
```
BASE_URL: http://localhost:8001
USER_TOKEN: <token from login>
AD_ID: <ad id>
```

---

## 🔑 USAGE #4: Working with Authentication

### Step 1: Login and get token
```bash
curl -X POST http://localhost:8001/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "MyPassword123"
  }'
```

**Response includes "token":**
```json
{
  "status": "success",
  "user_id": 1,
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Step 2: Use token in requests
```bash
curl http://localhost:8001/api/ads \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**Note:** Replace with your actual token!

---

## 📊 USAGE #5: Company Workflow

### 1. Company Login
```bash
curl -X POST http://localhost:8003/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "my-company",
    "password": "company_password"
  }'
```

### 2. Upload an Ad
```bash
curl -X POST http://localhost:8003/api/upload-ad \
  -H "Authorization: Bearer COMPANY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "iPhone 13 Pro",
    "description": "Excellent condition, minimal use",
    "category": "Electronics",
    "images": ["image1.jpg", "image2.jpg"],
    "price": 800
  }'
```

### 3. Get My Ads
```bash
curl http://localhost:8003/api/my-ads \
  -H "Authorization: Bearer COMPANY_TOKEN"
```

### 4. Get Analytics for an Ad
```bash
curl http://localhost:8003/api/analytics/AD-202512-123456 \
  -H "Authorization: Bearer COMPANY_TOKEN"
```

---

## ⚖️ USAGE #6: Admin Workflow

### 1. Admin Login
```bash
curl -X POST http://localhost:8004/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin_password"
  }'
```

### 2. Get Moderation Queue
```bash
curl http://localhost:8004/api/moderation-queue \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### 3. Moderate an Ad (Approve)
```bash
curl -X POST http://localhost:8004/api/ads/AD-202512-123456/moderate \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "approve",
    "reason": "Content looks good"
  }'
```

### 4. Block an Ad
```bash
curl -X POST http://localhost:8004/api/ads/AD-202512-123456/moderate \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "block",
    "reason": "Violates community guidelines"
  }'
```

### 5. Get Dashboard Stats
```bash
curl http://localhost:8004/api/dashboard \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## 📝 USAGE #7: Working with the Code

### Looking at the Database Models
```python
# Open models.py to see:
- User (public users)
- Company (advertisers)
- Admin (platform admins)
- Ad (advertisements)
- Category (ad categories)
- AdView (view tracking)
- Interaction (contact tracking)
- Favorite (user favorites)
- ModerationLog (admin actions)
- AuditLog (system events)
```

### Looking at the API Routes
```python
# Open app.py to see three apps:
public_app   # Lines 150-300+
company_app  # Lines 350-500+
admin_app    # Lines 550-700+
```

### Adding Custom Endpoints
```python
@public_app.get("/api/custom")
async def custom_endpoint(db: Session = Depends(get_db)):
    # Your code here
    return {"result": "your_data"}
```

---

## 🔗 USAGE #8: Integration with Frontend

### From React/Vue/Angular
```javascript
// Login
const response = await fetch('http://localhost:8001/api/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});
const data = await response.json();
const token = data.token;

// Get ads
const ads = await fetch('http://localhost:8001/api/ads', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// Track interaction
await fetch('http://localhost:8001/api/track_interaction', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    ad_id: 'AD-123',
    event_type: 'view',
    duration_seconds: 45
  })
});
```

---

## 📚 USAGE #9: Testing Workflow

### Manual Testing Checklist
- [ ] Open http://localhost:8001/docs
- [ ] Click on "GET /api/ads"
- [ ] Click "Try it out"
- [ ] Click "Execute"
- [ ] See the response
- [ ] Try each endpoint one by one

### Automated Testing
```bash
# With pytest (when tests are added)
pytest tests/

# With curl (manual)
./test_api.sh
```

---

## 🐛 USAGE #10: Debugging

### View Logs
Check the terminal where you ran the service - all logs appear there

### Enable SQL Logging
Edit `database.py`:
```python
engine = create_engine(
    DATABASE_URL,
    echo=True  # Set to True to see SQL queries
)
```

### Check Database
```bash
sqlite3 ../app/database/adsphere.db
sqlite> SELECT * FROM ads;
sqlite> SELECT COUNT(*) FROM users;
sqlite> .quit
```

### Test Endpoint Directly
```bash
# View request/response with verbose output
curl -v http://localhost:8001/api/ads

# Pretty print JSON response
curl http://localhost:8001/api/ads | python -m json.tool
```

---

## 📖 QUICK REFERENCE

| Task | Command |
|------|---------|
| Start Public Service | `python app.py public` |
| Start Company Service | `python app.py company` |
| Start Admin Service | `python app.py admin` |
| View API Docs | http://localhost:8001/docs |
| Get Ads | `curl http://localhost:8001/api/ads` |
| Register User | See Example 2 above |
| Login | See Example 3 in Auth section |
| Stop Service | `Ctrl+C` |
| Reset Database | `rm ../app/database/adsphere.db && python database.py` |

---

## ✅ COMMON USE CASES

### Use Case 1: Test if system is working
```bash
curl http://localhost:8001/health
# Should return {"status":"healthy","service":"public","port":8001}
```

### Use Case 2: See all ads in system
```bash
curl http://localhost:8001/api/ads
```

### Use Case 3: Create a user account
```bash
# 1. Register
curl -X POST http://localhost:8001/api/register \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser@test.com","password":"pass123","full_name":"Test User"}'

# 2. Login (same credentials)
curl -X POST http://localhost:8001/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"newuser@test.com","password":"pass123"}'
```

### Use Case 4: Company uploads an ad
```bash
# Get company token first
curl -X POST http://localhost:8003/api/login ...

# Then upload ad
curl -X POST http://localhost:8003/api/upload-ad \
  -H "Authorization: Bearer TOKEN" ...
```

### Use Case 5: Admin approves an ad
```bash
# Get admin token
curl -X POST http://localhost:8004/api/login ...

# Get pending ads
curl http://localhost:8004/api/moderation-queue ...

# Approve one
curl -X POST http://localhost:8004/api/ads/AD-123/moderate \
  -H "Authorization: Bearer TOKEN" \
  -d '{"decision":"approve"}'
```

---

## 🎊 YOU'RE READY!

Now you know how to:
✅ Start the services
✅ Test APIs with Swagger UI
✅ Use cURL for testing
✅ Authenticate and get tokens
✅ Use all three services
✅ Debug problems
✅ Integrate with frontend

**Start exploring! Open http://localhost:8001/docs now!** 🚀

