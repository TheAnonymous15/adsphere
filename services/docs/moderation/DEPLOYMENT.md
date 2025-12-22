# AdSphere Moderation Service - Deployment Guide

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose installed
- Python 3.11+ (for local development)
- 4GB+ RAM recommended
- Optional: NVIDIA GPU with CUDA support

### Step 1: Clone/Navigate to Service

```bash
cd app/moderator_services/moderation_service
```

### Step 2: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit as needed
nano .env
```

### Step 3: Build and Run

```bash
# Build Docker images
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f moderation
```

### Step 4: Verify

```bash
# Health check
curl http://localhost:8002/health

# Test moderation
curl -X POST http://localhost:8002/moderate/realtime \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Ad",
    "description": "This is a test advertisement",
    "category": "electronics"
  }'
```

Expected response:
```json
{
  "success": true,
  "decision": "approve",
  "global_score": 0.95,
  "risk_level": "low",
  "category_scores": {...},
  "flags": [],
  "reasons": ["All categories below safety thresholds"],
  "audit_id": "mod-20251220-abc123",
  "processing_time": 234.56
}
```

---

## 📦 Service Architecture

```
moderation_service/
├── app/
│   ├── main.py              # FastAPI application
│   ├── api/
│   │   └── routes_moderation.py  # API endpoints
│   ├── core/
│   │   ├── config.py        # Configuration
│   │   ├── decision_engine.py    # Risk scoring
│   │   └── hashing.py       # Content fingerprinting
│   ├── services/
│   │   ├── text_detoxify.py      # Hate/toxicity detection
│   │   ├── nsfw_detector.py      # NSFW detection
│   │   ├── ocr_paddle.py    # (TODO) OCR
│   │   ├── asr_whisper.py   # (TODO) Speech-to-text
│   │   ├── yolo_violence.py # (TODO) Violence detection
│   │   ├── yolo_weapons.py  # (TODO) Weapon detection
│   │   └── blood_cnn.py     # (TODO) Gore detection
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   └── workers/
│       └── video_worker.py  # (TODO) Async video processing
├── models_weights/          # Pre-trained model files
├── logs/                    # Application logs
├── cache/                   # Content fingerprint cache
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

---

## 🔧 Configuration

### Environment Variables

Key settings in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `GPU_ENABLED` | Enable GPU acceleration | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `THRESHOLD_*` | Category thresholds | See `.env.example` |

### Thresholds

Each category has 3 thresholds:
- **APPROVE**: Below this = safe
- **REVIEW**: Between approve & reject = needs human review
- **REJECT**: Above this = block content

Example for nudity:
```bash
THRESHOLD_NUDITY_APPROVE=0.2
THRESHOLD_NUDITY_REVIEW=0.4
THRESHOLD_NUDITY_REJECT=0.6
```

Adjust based on your risk tolerance.

---

## 🎯 API Endpoints

### POST /moderate/realtime

Synchronous moderation for text + images.

**Request:**
```json
{
  "title": "Ad title",
  "description": "Ad description",
  "category": "electronics",
  "language": "en",
  "media": [
    {"type": "image", "url": "https://..."}
  ],
  "user": {"id": "user123", "company": "acme"},
  "context": {"ad_id": "AD-001", "source": "php"}
}
```

**Response:**
```json
{
  "success": true,
  "decision": "approve|review|block",
  "global_score": 0.85,
  "risk_level": "low|medium|high|critical",
  "category_scores": {
    "nudity": 0.05,
    "violence": 0.02,
    "hate": 0.01,
    ...
  },
  "flags": [],
  "reasons": [...],
  "audit_id": "mod-...",
  "processing_time": 123.45
}
```

### POST /moderate/video

Async video moderation (returns job_id).

### GET /status/{job_id}

Check job status.

### GET /result/{job_id}

Get final moderation result.

---

## 🧪 Testing

### Unit Tests

```bash
# Install dev dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Load Testing

```bash
# Install Apache Bench
apt-get install apache2-utils

# Test throughput
ab -n 1000 -c 10 -p test_payload.json \
   -T application/json \
   http://localhost:8002/moderate/realtime
```

### Integration Test

```bash
# Test from PHP client
cd /path/to/adsphere
php -r "
require 'app/moderator_services/ModerationServiceClient.php';
\$client = new ModerationServiceClient('http://localhost:8002');
\$result = \$client->moderateRealtime('Test', 'Description', [], [], []);
var_dump(\$result);
"
```

---

## 📊 Monitoring

### Logs

```bash
# Application logs
docker-compose logs -f moderation

# Audit logs
tail -f logs/audit/*.log

# Redis logs
docker-compose logs -f redis
```

### Metrics

Access Redis Commander UI:
```
http://localhost:8081
```

View queued jobs, cache entries, etc.

### Performance

Monitor with:
```bash
# Container stats
docker stats adsphere_moderation

# API response times (check processing_time in responses)
```

---

## 🔒 Security

### API Authentication

To enable API key auth, set in `.env`:
```bash
API_KEY=your-secret-key-here
```

Then clients must send:
```bash
curl -H "X-API-Key: your-secret-key-here" ...
```

### Network Security

In production:
- Use internal Docker network (no public ports for Redis)
- Enable TLS/SSL for API
- Rate limiting via nginx/API gateway

### Audit Logging

All moderation decisions are logged to `logs/audit/` with:
- Timestamp
- Request details
- Decision + scores
- User context

---

## 🚀 Scaling

### Horizontal Scaling

Run multiple workers:

```bash
docker-compose up --scale moderation=4
```

Use load balancer (nginx/HAProxy) in front.

### GPU Acceleration

Edit `docker-compose.yml`:

```yaml
moderation:
  deploy:
    resources:
      reservations:
        devices:
          - capabilities: ["gpu"]
  environment:
    - GPU_ENABLED=true
```

Update `Dockerfile` to use CUDA base image.

### Redis Cluster

For high availability, use Redis Sentinel or Cluster mode.

---

## 🐛 Troubleshooting

### Service won't start

```bash
# Check logs
docker-compose logs moderation

# Common issues:
# - Port 8002 already in use → change port mapping
# - Out of memory → increase Docker memory limit
# - Missing models → download model weights
```

### Models not loading

```bash
# Check models directory
ls -la models_weights/

# Download missing models (example):
wget https://example.com/yolov8-violence.pt -O models_weights/yolov8n-violence.pt
```

### High latency

- Enable GPU if available
- Reduce `FRAME_SAMPLE_FPS` for videos
- Scale horizontally
- Use Redis for caching

### False positives/negatives

Adjust thresholds in `.env`:
- **Too many blocks?** → Increase `THRESHOLD_*_REJECT`
- **Too permissive?** → Decrease `THRESHOLD_*_REVIEW`

---

## 📝 TODOs (Implementation Roadmap)

### Phase 1 (MVP) - ✅ Complete
- [x] FastAPI service structure
- [x] Text moderation (Detoxify)
- [x] Basic NSFW detection
- [x] Decision engine
- [x] Docker deployment
- [x] PHP client integration

### Phase 2 - Video Pipeline
- [ ] ffmpeg frame extraction
- [ ] YOLOv8 violence detection
- [ ] YOLOv8 weapon detection
- [ ] Blood detection CNN
- [ ] OCR (PaddleOCR)
- [ ] ASR (Whisper/Vosk)
- [ ] Redis Streams job queue

### Phase 3 - Advanced Features
- [ ] Content fingerprinting
- [ ] Perceptual hashing
- [ ] Cache layer
- [ ] Live stream support
- [ ] Adaptive frame sampling

### Phase 4 - Production Hardening
- [ ] Database audit logging
- [ ] API authentication
- [ ] Rate limiting
- [ ] Distributed tracing
- [ ] Prometheus metrics
- [ ] Grafana dashboards

---

## 📚 Resources

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Detoxify](https://github.com/unitaryai/detoxify)
- [YOLOv8](https://docs.ultralytics.com/)
- [OpenNSFW](https://github.com/mdietrichstein/open-nsfw-python)
- [NudeNet](https://github.com/notAI-tech/NudeNet)

---

## 📞 Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review audit logs: `logs/audit/`
- Test API: `curl http://localhost:8002/health`

---

**Status:** ✅ MVP Ready  
**Version:** 1.0.0  
**Last Updated:** December 20, 2025

