# ⚡ QUICK START - 8 Minutes to Running

## 🚀 THE FASTEST WAY TO START

### Terminal 1 - Setup & Initialize
```bash
# Navigate to the directory
cd /Users/danielkinyua/Downloads/projects/ad/adsphere/python_system

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies (takes ~2 minutes)
pip install -r requirements.txt

# Initialize database (takes ~30 seconds)
python database.py

# You're ready! Now start the services...
```

### Terminal 2 - Start Public Service (Port 8001)
```bash
cd /Users/danielkinyua/Downloads/projects/ad/adsphere/python_system
source venv/bin/activate
python app.py public

# You'll see:
# ✅ Uvicorn running on http://0.0.0.0:8001
```

### Terminal 3 - Start Company Service (Port 8003)
```bash
cd /Users/danielkinyua/Downloads/projects/ad/adsphere/python_system
source venv/bin/activate
python app.py company

# You'll see:
# ✅ Uvicorn running on http://0.0.0.0:8003
```

### Terminal 4 - Start Admin Service (Port 8004)
```bash
cd /Users/danielkinyua/Downloads/projects/ad/adsphere/python_system
source venv/bin/activate
python app.py admin

# You'll see:
# ✅ Uvicorn running on http://0.0.0.0:8004
```

---

## ✅ VERIFY IT'S WORKING

Run these in a new terminal (with venv activated):

```bash
# Check each service is running
curl http://localhost:8001/health
curl http://localhost:8003/health
curl http://localhost:8004/health

# Each should return: {"status":"healthy","service":"...","port":...}
```

---

## 🌐 OPEN IN BROWSER

### API Documentation (Interactive)
- **Public**: http://localhost:8001/docs
- **Company**: http://localhost:8003/docs
- **Admin**: http://localhost:8004/docs

You can test API endpoints directly in your browser!

---

## 📝 TRY YOUR FIRST API CALLS

### Get All Ads
```bash
curl http://localhost:8001/api/ads
```

### Register a User
```bash
curl -X POST http://localhost:8001/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "email":"test@example.com",
    "password":"password123",
    "full_name":"Test User"
  }'
```

### Get Dashboard Stats
```bash
curl http://localhost:8001/api/dashboard_stats
```

### Get Categories
```bash
curl http://localhost:8001/api/categories
```

---

## 📚 WHAT TO READ NEXT

1. **README.md** - Complete setup and API documentation
2. **MIGRATION_GUIDE.md** - How to migrate from PHP
3. **SUMMARY.md** - Project overview and architecture

---

## ❓ COMMON QUESTIONS

### Q: How do I stop the services?
**A**: Press `Ctrl+C` in each terminal

### Q: How do I restart?
**A**: Just run `python app.py public` again

### Q: How do I reset the database?
**A**: 
```bash
rm ../app/database/adsphere.db
python database.py
```

### Q: Can I run all services in one terminal?
**A**: Not easily. Use the startup.sh script:
```bash
chmod +x startup.sh
./startup.sh
```

### Q: Where is the API documentation?
**A**: Open http://localhost:8001/docs in your browser

### Q: How do I test with Postman?
**A**: Import the OpenAPI spec from http://localhost:8001/openapi.json

### Q: Can I change the port?
**A**: Edit app.py and change the port number in uvicorn.run()

---

## 🎯 WHAT YOU CAN DO NOW

✅ Browse ads via API
✅ Register users
✅ Login
✅ Track interactions
✅ Upload ads (as company)
✅ View analytics
✅ Manage ads
✅ Moderate content (as admin)
✅ View dashboard stats

---

## 📊 NEXT STEPS

1. **Try the APIs** - Test each endpoint
2. **Read the docs** - Understand the system
3. **Test data migration** - Migrate from PHP (see MIGRATION_GUIDE.md)
4. **Load testing** - Compare performance with PHP
5. **Deploy** - When ready for production

---

## 🎊 YOU'RE ALL SET!

The system is running and ready to use. Start exploring the API at:

**http://localhost:8001/docs**

Enjoy! 🚀

