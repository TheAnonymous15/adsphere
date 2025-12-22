# 🚀 Quick Reference Guide - AdSphere Moderation Service

## 📋 Table of Contents
1. [Installation](#installation)
2. [Quick Start](#quick-start)
3. [API Usage](#api-usage)
4. [Management](#management)
5. [Monitoring](#monitoring)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Installation

```bash
# Run complete setup
./setup_complete.sh

# Follow interactive prompts
```

---

## ⚡ Quick Start

### Start Services

```bash
# Terminal 1: Redis
redis-server --port 6379

# Terminal 2: Worker Supervisor
python app/workers/worker_supervisor.py --workers 4

# Terminal 3: API Service
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

### Test It Works

```bash
# Health check
curl http://localhost:8002/health

# Moderate text
curl -X POST http://localhost:8002/moderate/realtime \
  -H "Content-Type: application/json" \
  -d '{"title": "Laptop for sale", "description": "MacBook Pro"}'
```

---

## 🔌 API Usage

### Text Moderation (Realtime)

```bash
curl -X POST http://localhost:8002/moderate/realtime \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "title": "Ad title",
    "description": "Ad description",
    "category": "electronics"
  }'
```

**Response:**
```json
{
  "success": true,
  "decision": "approve",
  "risk_level": "safe",
  "confidence": 0.95,
  "category_scores": {
    "nudity": 0.01,
    "violence": 0.02,
    "hate_speech": 0.01
  },
  "flags": [],
  "processing_time": 0.15
}
```

### Image Moderation

```bash
curl -X POST http://localhost:8002/moderate/image \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "image=@/path/to/image.jpg"
```

### Video Moderation (Async)

```bash
# Submit video job
curl -X POST http://localhost:8002/moderate/video \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "video=@/path/to/video.mp4"

# Response includes job_id
{
  "success": true,
  "job_id": "job-abc123",
  "status": "queued"
}

# Check status
curl http://localhost:8002/status/job-abc123

# Get result when complete
curl http://localhost:8002/result/job-abc123
```

---

## 🔑 API Key Management

### Generate API Key

```bash
# Admin key (all permissions)
python app/core/auth.py generate admin@example.com admin 365

# User key (moderate only)
python app/core/auth.py generate user@example.com user 30

# Save the key - it won't be shown again!
```

### List Keys

```bash
python app/core/auth.py list
```

### Revoke Key

```bash
python app/core/auth.py revoke adsphere_xxxxx
```

### View Stats

```bash
python app/core/auth.py stats
```

---

## 👁️ Monitoring

### Metrics Endpoints

```bash
# Prometheus format
curl http://localhost:8002/metrics

# JSON format
curl http://localhost:8002/metrics/json | jq
```

### Key Metrics

- `moderation_requests_total` - Total requests processed
- `moderation_processing_time_p95` - 95th percentile latency
- `moderation_queue_depth` - Current queue size
- `moderation_workers_active` - Active workers
- `moderation_errors_total` - Error count

### Worker Status

```bash
# In worker supervisor terminal
> status

# Shows:
# - Worker health
# - Uptime
# - Crash count
# - Restart count
```

---

## 🗄️ Database Queries

```bash
# Open database
sqlite3 app/database/moderation.db

# View recent jobs
SELECT job_id, job_type, decision, risk_level, submitted_at 
FROM moderation_jobs 
ORDER BY submitted_at DESC 
LIMIT 10;

# View statistics
SELECT * FROM daily_moderation_summary;

# View worker performance
SELECT * FROM worker_performance;

# View top violations
SELECT * FROM top_violations;
```

---

## 🛠️ Management Tasks

### Restart Worker

```bash
# In supervisor terminal
> restart worker-1
```

### Clean Old Logs

```bash
# Remove logs older than 30 days
find logs/ -name "*.log.*" -mtime +30 -delete
```

### Clean Fingerprint Cache

```python
from app.services.fp_hash import get_fingerprint_service

fp = get_fingerprint_service()
fp.cleanup_old_entries(max_age_days=30)
```

### Reset Rate Limits

```python
from app.core.rate_limiter import get_rate_limiter

limiter = get_rate_limiter()
limiter.reset_ip('192.168.1.1')
limiter.reset_api_key('adsphere_xxxxx')
```

### Backup Database

```bash
# Manual backup
cp app/database/moderation.db \
   app/database/backups/moderation_$(date +%Y%m%d).db

# Automated daily backup (add to cron)
0 2 * * * /path/to/backup_script.sh
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Test Specific Fixtures

```bash
pytest tests/test_text.py -v
pytest tests/test_pipeline.py -v
```

### Load Testing

```bash
python loadtest/load_test.py --workers 100 --requests 1000
```

---

## 🐛 Troubleshooting

### Workers Keep Crashing

**Check logs:**
```bash
tail -f logs/moderation.log
```

**Common causes:**
- Out of memory → Reduce batch size
- Model not found → Download missing models
- Redis connection → Check Redis is running

**Solution:**
```bash
# Reduce workers
python app/workers/worker_supervisor.py --workers 2

# Check memory
free -h
```

### High Queue Depth

**Check queue:**
```bash
redis-cli XLEN moderation_queue:jobs
```

**Solutions:**
- Add more workers
- Increase worker resources
- Check for stuck jobs

### Rate Limit Errors

**Check rate limits:**
```python
from app.core.rate_limiter import get_rate_limiter
stats = get_rate_limiter().get_stats()
print(stats)
```

**Reset if needed:**
```python
limiter.reset_ip('problem_ip')
```

### Database Locked

**Check connections:**
```bash
lsof app/database/moderation.db
```

**Fix:**
- Close other SQLite connections
- Use WAL mode for better concurrency

### Missing Models

**Download models:**
```bash
# YOLOv8 Violence
wget https://example.com/yolov8n-violence.pt \
  -O models_weights/yolov8n-violence.pt

# Verify
ls -lh models_weights/
```

---

## 📊 Performance Tuning

### Optimize for Throughput

```python
# config/policy.yaml
performance:
  batch_size: 32          # Process 32 frames at once
  num_workers: 8          # More workers
  frame_sample_rate: 3    # Every 3rd frame (faster)
  skip_audio: true        # Skip audio processing
```

### Optimize for Accuracy

```python
# config/policy.yaml
performance:
  batch_size: 8           # Smaller batches
  num_workers: 2          # Fewer workers
  frame_sample_rate: 1    # Every frame
  skip_audio: false       # Process audio
```

### Optimize for Cost

```python
# Enable fingerprint caching
USE_FINGERPRINTING = true

# Aggressive caching
CACHE_RESULTS_TTL = 86400  # 24 hours

# Reduce FPS
VIDEO_SAMPLE_FPS = 1  # 1 frame per second
```

---

## 🔐 Security Best Practices

1. **Keep API keys secret**
   - Never commit to git
   - Use environment variables
   - Rotate regularly

2. **Rate limiting**
   - Monitor for abuse
   - Adjust limits as needed
   - Block malicious IPs

3. **Audit logs**
   - Review regularly
   - Monitor for anomalies
   - Archive securely

4. **Database**
   - Regular backups
   - Encrypt at rest
   - Secure file permissions

5. **Updates**
   - Keep dependencies updated
   - Monitor CVEs
   - Test before deploying

---

## 📞 Support

### Get Help

```bash
# View all docs
ls -la *.md

# Key documents
cat ALL_17_COMPONENTS_COMPLETE.md
cat ALL_10_GAPS_COMPLETE.md
```

### Report Issues

Include:
1. Error message
2. Log output
3. Steps to reproduce
4. System info (OS, Python version)

---

## 🎯 Common Commands Reference

```bash
# Start everything
redis-server & \
python app/workers/worker_supervisor.py --workers 4 & \
uvicorn app.main:app --port 8002

# Check health
curl http://localhost:8002/health

# View metrics
curl http://localhost:8002/metrics/json | jq

# Generate API key
python app/core/auth.py generate user@test.com user

# View logs
tail -f logs/moderation.log

# Database shell
sqlite3 app/database/moderation.db

# Stop all
pkill -f "worker_supervisor"
pkill -f "uvicorn"
pkill -f "redis-server"
```

---

**📚 For complete documentation, see:** `ALL_17_COMPONENTS_COMPLETE.md`

