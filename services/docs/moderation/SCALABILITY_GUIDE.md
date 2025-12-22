# =============================================================================
# AdSphere Moderation Service - Scalability Guide
# =============================================================================

## Current Single-Instance Limitations

Running on a single port (8002) with one instance:
- **Max Throughput**: ~50-100 requests/second
- **Memory**: Limited to single server RAM
- **CPU**: Limited to single server cores
- **Single Point of Failure**: If it crashes, everything stops

## Scalable Architecture

```
                                    ┌─────────────────────────────────────────┐
                                    │            LOAD BALANCER                 │
                                    │         (Nginx on port 8002)             │
                                    └─────────────────┬───────────────────────┘
                                                      │
                    ┌─────────────────────────────────┼─────────────────────────────────┐
                    │                                 │                                 │
                    ▼                                 ▼                                 ▼
        ┌───────────────────┐           ┌───────────────────┐           ┌───────────────────┐
        │  Moderation API   │           │  Moderation API   │           │  Moderation API   │
        │   Instance 1      │           │   Instance 2      │           │   Instance 3      │
        │   (port 8001)     │           │   (port 8001)     │           │   (port 8001)     │
        └─────────┬─────────┘           └─────────┬─────────┘           └─────────┬─────────┘
                  │                               │                               │
                  └───────────────────────────────┴───────────────────────────────┘
                                                  │
                                    ┌─────────────┴─────────────┐
                                    │                           │
                                    ▼                           ▼
                        ┌───────────────────┐       ┌───────────────────┐
                        │       REDIS       │       │     DATABASE      │
                        │  (Cache & Queue)  │       │     (SQLite)      │
                        └───────────────────┘       └───────────────────┘
```

## Scaling Options

### Option 1: Horizontal Scaling with Docker (Recommended)

```bash
# Start with 4 API instances
docker-compose -f docker-compose.prod.yml up -d --scale moderation-api=4

# Scale up to 8 instances during peak hours
docker-compose -f docker-compose.prod.yml up -d --scale moderation-api=8

# Scale down during off-peak
docker-compose -f docker-compose.prod.yml up -d --scale moderation-api=2
```

**Capacity per instance:**
- Text moderation: ~100 req/s
- Image moderation: ~20 req/s
- Video moderation: ~2 req/s

**With 4 instances:**
- Text: ~400 req/s
- Image: ~80 req/s
- Video: ~8 req/s

### Option 2: Kubernetes Auto-Scaling

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: moderation-api
spec:
  replicas: 4
  selector:
    matchLabels:
      app: moderation-api
  template:
    spec:
      containers:
      - name: moderation-api
        image: adsphere/moderation:latest
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2000m"
            memory: "4Gi"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: moderation-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: moderation-api
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Option 3: Serverless / Cloud Functions

For extreme scalability, deploy endpoints as serverless functions:

- **AWS Lambda** + API Gateway
- **Google Cloud Functions**
- **Azure Functions**

Each endpoint scales independently to thousands of instances.

## Service Separation Strategy

For very high scale, separate into microservices:

| Service | Port | Purpose | Scale Factor |
|---------|------|---------|--------------|
| `text-moderator` | 8010 | Text analysis only | High (easy to scale) |
| `image-moderator` | 8011 | Image processing | Medium |
| `video-moderator` | 8012 | Video processing | Low (resource heavy) |
| `realtime-scanner` | 8013 | Background scanning | Medium |
| `api-gateway` | 8002 | Routes to services | High |

## Performance Benchmarks

### Single Instance (Current)
```
Text:   100 req/s,  10ms avg latency
Image:   20 req/s, 500ms avg latency
Video:    2 req/s,  30s avg latency
Scanner: 50 ads/s
```

### 4 Instances + Redis
```
Text:   400 req/s,  15ms avg latency
Image:   80 req/s, 600ms avg latency
Video:    8 req/s,  35s avg latency
Scanner: 200 ads/s
```

### 10 Instances + Redis + Dedicated Workers
```
Text:  1000 req/s,  20ms avg latency
Image:  200 req/s, 700ms avg latency
Video:   20 req/s,  40s avg latency
Scanner: 500 ads/s
```

## Quick Start Commands

### Development (Single Instance)
```bash
cd app/moderator_services/moderation_service
uvicorn app.main:app --host 0.0.0.0 --port 8002 --workers 4
```

### Production (Docker Compose)
```bash
cd app/moderator_services

# Start infrastructure
docker-compose -f docker-compose.prod.yml up -d redis

# Start API with 4 replicas
docker-compose -f docker-compose.prod.yml up -d --scale moderation-api=4

# Start load balancer
docker-compose -f docker-compose.prod.yml up -d nginx

# Check status
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f moderation-api
```

### Health Check
```bash
# Check if load balancer is working
curl http://localhost:8002/health

# Check individual instances
docker-compose -f docker-compose.prod.yml exec moderation-api curl http://localhost:8000/health
```

## Redis Configuration for High Scale

```bash
# redis.conf for production
maxmemory 4gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec

# Connection pooling
tcp-keepalive 300
timeout 0
```

## Monitoring

### Prometheus Metrics
```
# Scrape config
- job_name: 'moderation-api'
  static_configs:
    - targets: ['moderation-api:8000']
  metrics_path: /metrics
```

### Key Metrics to Watch
- `moderation_requests_total` - Total requests
- `moderation_latency_seconds` - Response times
- `moderation_queue_depth` - Job queue size
- `moderation_cache_hit_rate` - Cache efficiency
- `moderation_errors_total` - Error rate

## Cost Estimates (Cloud)

| Scale | Monthly Cost | Capacity |
|-------|--------------|----------|
| Small (2 instances) | $100-200 | 10K ads/day |
| Medium (4 instances) | $300-500 | 50K ads/day |
| Large (10 instances) | $800-1500 | 200K ads/day |
| Enterprise (20+ instances) | $3000+ | 1M+ ads/day |

## Summary

**Single port 8002 is fine because:**
1. Nginx load balancer distributes traffic
2. Multiple backend instances handle load
3. Redis provides distributed caching
4. Workers process heavy tasks asynchronously

**To scale further:**
1. Add more API instances (`--scale moderation-api=N`)
2. Add dedicated worker pools for video/image
3. Use Kubernetes for auto-scaling
4. Consider serverless for extreme scale

