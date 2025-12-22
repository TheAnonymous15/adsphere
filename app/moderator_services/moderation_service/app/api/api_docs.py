"""
API Documentation Configuration

This module provides comprehensive API documentation for the AdSphere Moderation Service.
The documentation is auto-generated and available at /docs (Swagger UI) and /redoc (ReDoc).
"""

# API Tags Metadata - Organizes endpoints into logical groups
TAGS_METADATA = [
    {
        "name": "health",
        "description": "Health check and service status endpoints. Use these to monitor service availability.",
    },
    {
        "name": "moderation",
        "description": """
## Content Moderation Endpoints

The core moderation APIs for analyzing content:

### Communication Methods
- **WebSocket (Primary)**: Real-time streaming with progress updates
- **REST (Fallback)**: Traditional request-response

### Supported Content Types
- **Text**: Titles, descriptions, comments
- **Images**: JPEG, PNG, WebP, GIF
- **Videos**: MP4, MOV, AVI (max 5 minutes)

### Decision Outcomes
| Decision | Action |
|----------|--------|
| `approve` | Content is safe, proceed |
| `review` | Flagged for manual review |
| `block` | Content rejected |
        """,
    },
    {
        "name": "text",
        "description": """
## Text Moderation

Analyzes text content for:
- Violence/hate speech
- Adult content
- Spam/scam patterns
- Profanity
- Personal information (PII)

### Languages Supported
50+ languages with automatic detection
        """,
    },
    {
        "name": "image",
        "description": """
## Image Moderation

Full image processing pipeline:
1. **Security Scan**: Detect hidden/malicious data
2. **Sanitization**: Remove steganography
3. **Compression**: Optimize to <1MB WebP
4. **OCR**: Extract and moderate text
5. **Content Analysis**: Detect inappropriate content

### Detections
- Nudity/explicit content
- Violence/gore
- Weapons
- Hate symbols
- Text overlays
        """,
    },
    {
        "name": "video",
        "description": """
## Video Moderation

Comprehensive video analysis:
1. **Frame Extraction**: 2 FPS sampling
2. **Audio Separation**: Speech-to-text
3. **Frame Analysis**: Same as image moderation
4. **Audio Analysis**: Hate speech, explicit language

### Limits
- Max duration: 5 minutes
- Max size: 500MB
- Supported: MP4, MOV, AVI, MKV
        """,
    },
    {
        "name": "scanner",
        "description": """
## Real-time Ad Scanner

Background scanning system for existing ads:

### Scan Modes
| Mode | Description |
|------|-------------|
| `incremental` | Scan ads from last 24 hours |
| `priority` | Scan high-risk ads first |
| `full` | Scan all ads |
| `single` | Scan specific ad by ID |

### Features
- Cached results (skip recently scanned)
- Priority queue
- Background workers
        """,
    },
    {
        "name": "websocket",
        "description": """
## WebSocket Streaming

Real-time bidirectional communication for:
- Progress updates during processing
- Streaming results
- Live monitoring

### Connection
```
ws://localhost:8002/ws/moderate
```

### Message Format (Protobuf)
```protobuf
message ModerationFrame {
  string task_id = 1;
  int64 sequence = 2;
  bool final = 3;
  bytes payload = 4;
}
```
        """,
    },
    {
        "name": "admin",
        "description": """
## Administrative Controls

System management endpoints:

### Service Control
- Restart/shutdown service
- View system status
- Check health

### Cache Management
- Clear Redis cache
- View cache statistics

### Worker Management
- Start/stop workers
- View worker status

### Scaling
- View current scale
- Scaling instructions

⚠️ **Authentication Required** for production
        """,
    },
]

# API Description (shown on docs home)
API_DESCRIPTION = """
# 🛡️ AdSphere Content Moderation API

Enterprise-grade AI/ML content moderation service for the AdSphere advertising platform.

## Overview

This API provides real-time content moderation for:
- **Text**: Ad titles, descriptions, comments
- **Images**: Product photos, banners
- **Videos**: Video ads (up to 5 minutes)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Your Application                         │
│                  (PHP, JavaScript, etc.)                     │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Moderation Service (Port 8002)                  │
│  ┌─────────────────┐  ┌─────────────────┐                   │
│  │   REST API      │  │   WebSocket     │                   │
│  │   /moderate/*   │  │   /ws/moderate  │                   │
│  └─────────────────┘  └─────────────────┘                   │
│                              │                               │
│  ┌───────────────────────────┴───────────────────────────┐  │
│  │              AI/ML Processing Pipeline                 │  │
│  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐        │  │
│  │  │Text │  │Image│  │Video│  │ OCR │  │Audio│        │  │
│  │  └─────┘  └─────┘  └─────┘  └─────┘  └─────┘        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Check Service Health
```bash
curl http://localhost:8002/health
```

### 2. Moderate Text
```bash
curl -X POST http://localhost:8002/moderate/text/process \\
  -H "Content-Type: application/json" \\
  -d '{"title": "Car for sale", "description": "Great condition, low mileage"}'
```

### 3. Moderate Image
```bash
curl -X POST http://localhost:8002/moderate/image/process \\
  -H "Content-Type: application/json" \\
  -d '{"image_data": "base64...", "filename": "photo.jpg"}'
```

## Communication Methods

| Method | Use Case | Features |
|--------|----------|----------|
| **REST** | Quick operations | Simple, stateless |
| **WebSocket** | Long operations | Streaming, progress |

## Response Format

All endpoints return JSON:

```json
{
  "success": true,
  "decision": "approve",
  "risk_level": "low",
  "global_score": 0.12,
  "flags": [],
  "reasons": [],
  "processing_time_ms": 145
}
```

## Decision Values

| Decision | Meaning | Action |
|----------|---------|--------|
| `approve` | Content is safe | Allow |
| `review` | Needs manual check | Queue for review |
| `block` | Policy violation | Reject |

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Text | 500 req/s |
| Image | 100 req/s |
| Video | 20 req/s |
| Scanner | 50 req/s |

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Bad request (invalid input) |
| 401 | Unauthorized |
| 413 | File too large |
| 429 | Rate limit exceeded |
| 500 | Server error |
| 503 | Service unavailable |

## Support

- **Documentation**: http://localhost:8002/docs
- **Health Check**: http://localhost:8002/health
- **Metrics**: http://localhost:8002/metrics

---
*AdSphere Moderation Service v1.0.0*
"""

# License info
API_LICENSE = {
    "name": "Proprietary",
    "url": "https://adsphere.com/terms",
}

# Contact info
API_CONTACT = {
    "name": "AdSphere API Support",
    "url": "https://adsphere.com/support",
    "email": "api@adsphere.com",
}

