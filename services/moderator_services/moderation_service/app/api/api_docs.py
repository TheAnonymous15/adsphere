"""
AdSphere Moderation API - Comprehensive Documentation
======================================================

Enterprise-grade AI/ML content moderation service.
Auto-generated documentation available at /docs and /redoc.
"""

# =============================================================================
# API TAGS - Endpoint Organization
# =============================================================================
TAGS_METADATA = [
    {
        "name": "health",
        "description": """
## 🏥 Health & Monitoring

Service health and monitoring endpoints for system observability.

### Endpoints
| Endpoint | Method | Description |n
|----------|--------|-------------|
| `/health` | GET | Basic health check |
| `/metrics` | GET | Prometheus metrics |
| `/instance` | GET | Instance information |

### Health Response
```json
{
  "status": "healthy",
  "service": "AdSphere Moderation Service",
  "version": "1.0.0",
  "uptime_seconds": 3600
}
```
        """,
    },
    {
        "name": "moderation",
        "description": """
## 🛡️ Content Moderation

Core moderation APIs for analyzing advertisements and content.

### Endpoints Overview
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/moderate/text` | POST | Moderate text content |
| `/moderate/image` | POST | Moderate images |
| `/moderate/image/process` | POST | Full image processing pipeline |
| `/moderate/video` | POST | Moderate video content |
| `/moderate/realtime` | POST | Real-time ad moderation |

### Decision Outcomes
| Decision | Risk Level | Action |
|----------|------------|--------|
| `approve` | low | ✅ Content is safe, proceed |
| `review` | medium | ⚠️ Flagged for manual review |
| `block` | high/critical | ❌ Content rejected |

### Supported Content Types
- **Text**: Titles, descriptions, comments (50+ languages)
- **Images**: JPEG, PNG, WebP, GIF, AVIF (max 10MB)
- **Videos**: MP4, MOV, AVI, MKV (max 60 seconds, 500MB)

### Category Scores
All responses include category-specific scores (0.0 - 1.0):
- `nudity` - Adult/NSFW content
- `violence` - Violence and gore
- `weapons` - Weapons detection
- `hate` - Hate speech and discrimination
- `drugs` - Drug-related content
- `scam_fraud` - Scam patterns
- `spam` - Spam detection
        """,
    },
    {
        "name": "search",
        "description": """
## 🔍 AI Search Assistant

Semantic search powered by multilingual sentence transformers.
Match user queries to categories using AI-powered similarity matching.

### Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search/match` | POST | AI category matching |
| `/search/quick/{query}` | GET | Quick semantic search |
| `/search/categories` | GET | List all categories |
| `/search/health` | GET | Search service health |

### How It Works
1. User enters search query (e.g., "hungry", "car", "rent")
2. AI model encodes query into semantic vector
3. Compares against category embeddings
4. Returns best matching categories with confidence scores

### Supported Languages
50+ languages including:
- English, Spanish, French, German
- Swahili, Arabic, Chinese, Hindi
- Portuguese, Russian, Japanese, Korean

### Example Request
```bash
curl -X POST "http://localhost:8002/search/match" \\
  -H "Content-Type: application/json" \\
  -d '{"query": "I want to buy a car", "top_k": 3}'
```

### Example Response
```json
{
  "success": true,
  "query": "I want to buy a car",
  "results": [
    {"slug": "vehicles", "name": "Vehicles", "score": 0.92},
    {"slug": "automotive", "name": "Automotive", "score": 0.78}
  ],
  "processing_time_ms": 45.2,
  "model_type": "semantic"
}
```

### Cache Architecture
```
Query → Memory Cache → Redis → SQLite → Model
         (fastest)              (persistent)
```
        """,
    },
    {
        "name": "scanner",
        "description": """
## 🔄 Real-time Ad Scanner

Background scanning system for continuous moderation of existing ads.

### Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/moderate/realtimescanner/start` | POST | Start scanner |
| `/moderate/realtimescanner/stats` | GET | Scanner statistics |
| `/moderate/realtimescanner/enqueue` | POST | Queue ad for scanning |
| `/moderate/realtimescanner/status/{id}` | GET | Check scan status |

### Scan Modes
| Mode | Description | Use Case |
|------|-------------|----------|
| `incremental` | Last 24 hours | Daily maintenance |
| `priority` | High-risk first | Suspicious content |
| `full` | All ads | Complete audit |
| `single` | Specific ad | Manual trigger |

### Performance
- **Throughput**: 12-15 ads/second
- **1M ads projection**: ~22 hours (full scan)
- **Caching**: Skip recently scanned (24h default)

### Scanner Response
```json
{
  "scanner_id": "scan-abc123",
  "status": "running",
  "scanned": 1500,
  "flagged": 23,
  "clean": 1477,
  "speed": "13.2 ads/sec"
}
```
        """,
    },
    {
        "name": "image",
        "description": """
## 🖼️ Image Moderation Pipeline

Comprehensive 10-step image analysis pipeline.

### Pipeline Steps
```
┌──────────┐   ┌───────────┐   ┌────────────┐   ┌─────────┐
│ SECURITY │──▶│ SANITIZER │──▶│ COMPRESSOR │──▶│   OCR   │
│   SCAN   │   │  (clean)  │   │  (≤1MB)    │   │ (text)  │
└──────────┘   └───────────┘   └────────────┘   └─────────┘
                                                     │
     ┌───────────────────────────────────────────────┘
     ▼
┌──────────┐   ┌───────────┐   ┌────────────┐   ┌─────────┐
│   NSFW   │   │  WEAPONS  │   │  VIOLENCE  │   │  SCENE  │
│ DETECT   │   │  DETECT   │   │   DETECT   │   │ ANALYZE │
└──────────┘   └───────────┘   └────────────┘   └─────────┘
```

### Security Detectors (ML-powered)
- **Steganography**: Hidden data in pixel values
- **Forensics**: Image manipulation detection
- **Hidden Data**: Appended/embedded files
- **Malware**: Executable signatures

### Content Detectors
| Detector | Model | Accuracy |
|----------|-------|----------|
| NSFW | NudeNet | 95%+ |
| Weapons | YOLOv8 + Classifier | 90%+ |
| Violence | Custom CNN | 88%+ |
| OCR | PaddleOCR | 98%+ |

### Compression
- Output format: WebP
- Max size: 1MB
- Quality: Adaptive (preserve detail)
        """,
    },
    {
        "name": "video",
        "description": """
## 🎬 Video Moderation Pipeline

Complete video analysis with frame extraction and audio processing.

### Pipeline Flow
```
Video Upload
     │
     ▼
┌─────────────────────────────┐
│ Video/Audio Separator       │
└──────────────┬──────────────┘
        ┌──────┴──────┐
        ▼             ▼
   ┌─────────┐   ┌─────────┐
   │  VIDEO  │   │  AUDIO  │
   │ FRAMES  │   │ CHUNKS  │
   │ (2 FPS) │   │ (6s ea) │
   └────┬────┘   └────┬────┘
        │             │
        ▼             ▼
   ┌─────────┐   ┌─────────┐
   │  FRAME  │   │  SPEECH │
   │ANALYSIS │   │ TO TEXT │
   │(parallel)│   │(Whisper)│
   └────┬────┘   └────┬────┘
        │             │
        └──────┬──────┘
               ▼
        ┌─────────────┐
        │  AGGREGATE  │
        │   SCORES    │
        └─────────────┘
```

### Limits
| Parameter | Value |
|-----------|-------|
| Max Duration | 60 seconds |
| Max File Size | 500MB |
| Frame Rate | 2 FPS (120 frames max) |
| Audio Chunks | 10 × 6 seconds |

### Parallel Processing
- **Frame Workers**: 120 async workers
- **Audio Workers**: 10 parallel chunks
- **GPU Acceleration**: Supported (MPS/CUDA)
        """,
    },
    {
        "name": "websocket",
        "description": """
## ⚡ WebSocket Streaming

Real-time bidirectional communication for progress tracking.

### Connection
```
ws://localhost:8002/ws/moderate
ws://localhost:8002/ws/search
```

### Use Cases
- **Progress Updates**: Track moderation progress
- **Streaming Results**: Real-time decisions
- **Live Search**: Instant category matching

### Message Protocol
```json
{
  "type": "progress",
  "task_id": "mod-12345",
  "progress": 0.75,
  "stage": "analyzing_frames",
  "message": "Processed 90/120 frames"
}
```

### Events
| Event | Description |
|-------|-------------|
| `connected` | Connection established |
| `progress` | Processing update |
| `result` | Final decision |
| `error` | Error occurred |
        """,
    },
    {
        "name": "admin",
        "description": """
## ⚙️ Administration

System management and control endpoints.

### Service Control
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/status` | GET | System status |
| `/admin/restart` | POST | Restart service |
| `/admin/shutdown` | POST | Graceful shutdown |

### Cache Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/cache/stats` | GET | Cache statistics |
| `/admin/cache/clear` | POST | Clear all caches |

### Worker Management
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/worker/{type}/status` | GET | Worker status |
| `/admin/worker/{type}/start` | POST | Start worker |
| `/admin/worker/{type}/stop` | POST | Stop worker |

### Logs & Monitoring
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/logs` | GET | Recent logs |
| `/admin/system` | GET | System resources |
| `/metrics` | GET | Prometheus metrics |

⚠️ **Note**: Admin endpoints require authentication in production.
        """,
    },
]


# =============================================================================
# MAIN API DESCRIPTION (Swagger UI Landing Page)
# =============================================================================
API_DESCRIPTION = """
# 🛡️ AdSphere Content Moderation API

<div align="center">

**Enterprise-grade AI/ML content moderation for digital advertising**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.12+-green.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-teal.svg)]()

</div>

---

## 🏗️ System Architecture

### Full Architecture Diagram (Detailed)
```
                                 ┌─────────────────────────────────────────────────────────────┐
                                 │                 AdSphere Microservices                      │
                                 └─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                           Ingress / LB (nginx/HAProxy)                                       │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
┌───────────────┐      ┌───────────────┐      ┌───────────────┐                                                                     
│  PUBLIC (8001)│      │ COMPANY (8003)│      │  ADMIN (8004) │  ← PHP apps                                                         
│  Browse ads   │      │ Upload/Manage │      │ Control/Stats │                                                                     
└──────┬────────┘      └──────┬────────┘      └──────┬────────┘                                                                     
       │                      │                       │                                                                             
       └──────────────┬───────┴──────────────┬────────┴──────────────────────────────────────────────────────────────────────────┐
                      │                      │                                                                                  │
                      ▼                      ▼                                                                                  │
               ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐             │
               │                       MODERATION SERVICE (FastAPI, Port 8002)                                    │             │
               └──────────────────────────────────────────────────────────────────────────────────────────────────┘             │
               ┌───────────────────────────────────────┐   ┌─────────────────────────────────────────────┐                      │
               │           API Gateway Layer           │   │         WebSocket Streaming Layer           │                      │
               │  REST: /moderate/* /search/* /admin/* │   │  ws://.../ws/moderate   ws://.../ws/search │                      │
               └───────────────┬───────────────────────┘   └──────────────────────────┬──────────────────┘                      │
                               │                                          ▲                                                │
                               ▼                                          │                                                │
               ┌───────────────────────────────────────┐   ┌─────────────────────────────────────────────┐                      │
               │         Orchestration Layer           │   │         Caching & Intelligence Layer        │                      │
               │  • Master Pipeline Coordinator        │   │  L1 Memory  L2 Redis  L3 SQLite  Fingerprint│                      │
               │  • Queue Manager (Redis/In-Memory)    │   │  • Context & Intent Engine (multi-modal)   │                      │
               │  • Backpressure & Rate Limiter        │   │  • Duplicate/Similarity (pHash/n-grams)    │                      │
               └───────────────┬───────────────────────┘   └──────────────────────────┬──────────────────┘                      │
                               │                                          ▲                                                │
                               ▼                                          │                                                │
               ┌───────────────────────────────────────┐   ┌─────────────────────────────────────────────┐                      │
               │            Security Engine            │   │             Decision Engine                 │                      │
               │  • File Signature/Structure           │   │  • Score Aggregation (fusion/weights)       │                      │
               │  • Entropy / LSB / DCT Steg Detection │   │  • Policy Evaluation (policy.yaml rules)    │                      │
               │  • Hidden Data & Metadata Scan        │   │  • Risk Classification (low/med/high/crit)  │                      │
               │  • Sanitization (clean WebP, strip)   │   │  • Final Decision + Audit Logging           │                      │
               └───────────────┬───────────────────────┘   └──────────────────────────┬──────────────────┘                      │
                               │                                          ▲                                                │
                               ▼                                          │                                                │
               ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐             │
               │                         Moderation Pipelines (Parallel/Async)                                   │             │
               ├──────────────────────────────────────────────────────────────────────────────────────────────────┤             │
               │  TEXT (10 steps): normalize → tokenize → lang-detect → embed → similarity → intent → context → │             │
               │  toxicity → aggregate → policy → decision                                                      │             │
               ├──────────────────────────────────────────────────────────────────────────────────────────────────┤             │
               │  IMAGE (10 steps): security-scan → sanitize → compress → OCR → NSFW → weapons → violence →    │             │
               │  blood → scene → aggregate → policy → decision                                                 │             │
               ├──────────────────────────────────────────────────────────────────────────────────────────────────┤             │
               │  VIDEO (7 steps): split A/V → 2FPS frames → parallel frame analysis → ASR → temporal coherence │             │
               │  → aggregate → policy → decision                                                               │             │
               ├──────────────────────────────────────────────────────────────────────────────────────────────────┤             │
               │  AUDIO (5 steps): chunking → ASR → text moderation → aggregate → policy → decision            │             │
               └──────────────────────────────────────────────────────────────────────────────────────────────────┘             │
                               │                                                                                                 │
                               ▼                                                                                                 │
               ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐             │
               │                              ML Models & Tools                                                  │             │
               │  • NudeNet (NSFW)  • YOLOv8 (objects/weapons)  • Violence CNN  • Blood CNN                     │             │
               │  • PaddleOCR (OCR) • Whisper (ASR) • Sentence-Transformers (semantic match)                     │             │
               │  • XLM-RoBERTa (lang/context) • DeBERTa (intent) • Detoxify (toxicity)                          │             │
               └──────────────────────────────────────────────────────────────────────────────────────────────────┘             │
                               │                                                                                                 │
                               ▼                                                                                                 │
               ┌──────────────────────────────┐    ┌──────────────────────────────┐    ┌──────────────────────────────┐          │
               │          Redis (Cache)      │    │       SQLite (Audit/Jobs)    │    │    Model Weights Store       │          │
               │  L2 cache + queues + stats  │    │  Persistent logs & decisions │    │  Auto-download + checksums    │          │
               └──────────────────────────────┘    └──────────────────────────────┘    └──────────────────────────────┘          │
```

---

## 🧠 Context & Intent Intelligence

- Contextual analysis merges text, image, audio cues to understand intent.
- Detects ambiguity, sarcasm, and implied threats using transformer classifiers.
- Adjusts policy thresholds based on detected context (e.g., news vs promotion).

---

## 🔐 Security & Sanitization Engine

- Multi-detector security prefilter for images: file signature, entropy, LSB/DCT steganography, hidden data, metadata anomalies, file size heuristics.
- Sanitizer removes EXIF/XMP, re-encodes to clean WebP, strips suspicious channels before content analysis.

---

## ⚙️ Caching Architecture

- L1 Memory cache (fast, short TTL) → L2 Redis (optional, medium TTL) → L3 SQLite (persistent)
- Fingerprint cache: image pHash, video MD5, text n-gram fingerprints to avoid reprocessing.

---

## 🔄 Detailed Pipelines

### 1) Text Moderation (10 steps)
1. Normalize input (Unicode NFC, whitespace)
2. Tokenize (spaCy multilingual)
3. Language detection (XLM-RoBERTa)
4. Semantic embedding (Sentence-Transformers, multilingual)
5. Similarity search (FAISS/Qdrant)
6. Intent classification (DeBERTa-v3)
7. Context classification (XLM-RoBERTa-large)
8. Toxicity detection (Detoxify)
9. Feature aggregation (weighted fusion)
10. Policy evaluation (policy.yaml thresholds) → decision

### 2) Image Moderation (10 steps)
1. Security scan (steg, forensics, hidden data, metadata, heuristics)
2. Sanitization (clean re-encode)
3. Compression (≤1MB WebP, adaptive quality)
4. OCR (PaddleOCR → send text to Text Pipeline)
5. NSFW detection (NudeNet)
6. Weapons detection (YOLOv8 + post-filters)
7. Violence detection (CNN)
8. Blood/gore detection (CNN segmentation)
9. Scene understanding (CLIP/ResNet)
10. Aggregation + Policy → decision

### 3) Video Moderation (7 steps)
1. Separate audio/video (FFmpeg)
2. Extract frames (2 FPS, temp JPEGs)
3. Parallel frame analysis (Image Pipeline)
4. Audio ASR (Whisper → Text Pipeline)
5. Temporal coherence analysis
6. Score aggregation (frame/audio patterns)
7. Policy evaluation, cleanup → decision

### 4) Audio Moderation (5 steps)
1. Chunk audio (6s segments)
2. ASR transcription (Whisper)
3. Text moderation (pipeline)
4. Aggregate chunk scores
5. Policy evaluation → decision

---

## 🧮 Decision Engine

- Aggregates category scores (nudity, violence, weapons, hate, drugs, scam, spam).
- Applies risk classification matrix (low/medium/high/critical).
- Outputs decision with reasons, audit_id, processing_time.

---

## 📈 Monitoring & Ops

- Prometheus metrics: requests, errors, latency, decisions.
- Grafana dashboards for throughput, queue depth, GPU/CPU utilization.
- Admin endpoints for cache control, worker supervision, logs.

---
"""


# =============================================================================
# LICENSE & CONTACT INFO
# =============================================================================
API_LICENSE = {
    "name": "Proprietary License",
    "url": "https://adsphere.com/terms",
}

API_CONTACT = {
    "name": "AdSphere API Support",
    "url": "https://adsphere.com/support",
    "email": "api-support@adsphere.com",
}


# =============================================================================
# CUSTOM CSS FOR SWAGGER UI (Optional Enhancement)
# =============================================================================
SWAGGER_UI_CSS = """
.swagger-ui .topbar { display: none; }
.swagger-ui .info .title { font-size: 2.5em; }
.swagger-ui .info .description h1 { color: #3b82f6; }
.swagger-ui .info .description pre { background: #1e293b; color: #e2e8f0; }
"""
