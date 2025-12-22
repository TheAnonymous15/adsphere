# AdSphere Content Moderation Microservice

Enterprise-grade distributed multimodal AI content moderation platform.

## Overview

This microservice processes video advertisements (≤1 min) with:
- **Frame-based computer vision** (nudity, violence, weapons, blood, minors)
- **ASR speech transcription + NLP** (hate, extremism, illegal content)
- **OCR text extraction** (phishing, scams, illegal offers)
- **Metadata scanning**
- **Decision engine** with risk scoring

## Architecture

- **FastAPI** REST API
- **Redis Streams** for job queuing
- **Async workers** for distributed processing
- **Docker-native** deployment
- **CPU/GPU** support

## Models Used (Free/Open-Source)

- **OpenNSFW2** - Nudity detection
- **NudeNet** - Explicit content classification
- **YOLOv8-violence** - Fight/violence detection
- **YOLOv8-weapons** - Gun/knife detection
- **Blood CNN** - Gore detection
- **Detoxify** - Hate speech/toxicity
- **PaddleOCR** - Text extraction from frames
- **Whisper/Vosk** - Speech-to-text

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /moderate/video` | Upload video for moderation |
| `POST /moderate/realtime` | Realtime text+media moderation |
| `GET /status/{job_id}` | Get job status |
| `GET /result/{job_id}` | Get moderation results |
| `POST /stream/start` | Start live stream session |
| `POST /stream/frame` | Submit stream frame |
| `POST /stream/end` | End stream session |

## Decision Outcomes

- **allow** - Safe content, auto-approve
- **review** - Uncertain, needs human review
- **block** - Violation detected, reject

## Quick Start

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Check logs
docker-compose logs -f moderation

# Stop
docker-compose down
```

## Configuration

Set environment variables in `docker-compose.yml` or `.env`:

```bash
REDIS_URL=redis://redis:6379/0
LOG_LEVEL=INFO
GPU_ENABLED=false
MODERATION_SERVICE_URL=http://moderation:8000
```

## Performance

- **Throughput**: ≥100 videos/min
- **Latency**: ≤2s median for uploads
- **Scaling**: Horizontal via worker replication

## Security

- API authentication via tokens
- Model sandboxing
- Audit logging
- Forensic retention

## Compliance

- CSAM resistance
- GDPR/CCPA aligned
- Tamper-resistant logs

## Development

```bash
# Install deps
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload --port 8000

# Test
curl -X POST http://localhost:8000/moderate/realtime \
  -H "Content-Type: application/json" \
  -d '{"title": "Test ad", "description": "Testing moderation"}'
```

## License

Internal use only - AdSphere platform

