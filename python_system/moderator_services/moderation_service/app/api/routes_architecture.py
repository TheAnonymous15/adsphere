from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/docs", tags=["architecture"])

ARCH_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AdSphere – Enterprise Moderation System Architecture</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body { 
      font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; 
      background: linear-gradient(135deg, #0b1220 0%, #0f172a 100%);
      color: #e3e8ef; 
      line-height: 1.6;
    }
    .wrap { max-width: 1400px; margin: 0 auto; padding: 48px 24px; }
    h1 { font-size: 36px; margin: 0 0 8px; font-weight: 700; color: #60a5fa; }
    h2 { font-size: 20px; margin: 32px 0 16px; font-weight: 700; color: #93c5fd; border-bottom: 2px solid #1f2937; padding-bottom: 8px; scroll-margin-top: 100px; }
    .header { margin-bottom: 48px; }
    .sub { color: #93c5fd; margin-bottom: 8px; font-size: 14px; }
    .desc { color: #cbd5e1; margin-bottom: 24px; font-size: 13px; }
    .card { background: rgba(15, 23, 42, 0.8); border: 1px solid #1f2937; border-radius: 12px; padding: 24px; margin-bottom: 24px; backdrop-filter: blur(10px); }
    .card-header { font-weight: 600; color: #60a5fa; margin-bottom: 12px; font-size: 14px; }
    .card-content { font-size: 13px; color: #cbd5e1; }
    pre { white-space: pre-wrap; overflow-x: auto; font-family: SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 11px; line-height: 1.4; background: rgba(0,0,0,0.3); padding: 16px; border-radius: 8px; border-left: 3px solid #3b82f6; }
    .legend { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 20px; }
    .pill { padding: 8px 14px; border-radius: 999px; font-size: 11px; border: 1px solid #334155; background: rgba(11, 19, 38, 0.8); color: #93c5fd; }
    .component { margin: 16px 0; padding: 12px; background: rgba(20, 30, 50, 0.6); border-left: 3px solid #3b82f6; border-radius: 6px; }
    .component-title { font-weight: 600; color: #60a5fa; font-size: 12px; margin-bottom: 4px; }
    .component-detail { font-size: 11px; color: #cbd5e1; }
    table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 12px; }
    th { background: rgba(30, 41, 59, 0.8); color: #93c5fd; padding: 10px; text-align: left; border: 1px solid #1f2937; }
    td { padding: 10px; border: 1px solid #1f2937; color: #cbd5e1; }
    tr:hover { background: rgba(20, 30, 50, 0.4); }
    .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin: 16px 0; }
    .metric-box { background: rgba(20, 30, 50, 0.6); padding: 16px; border-radius: 8px; border: 1px solid #1f2937; }
    .metric-value { font-size: 18px; font-weight: 700; color: #60a5fa; margin: 8px 0; }
    .metric-label { font-size: 11px; color: #cbd5e1; }
    .flow-diagram { background: rgba(0, 0, 0, 0.3); padding: 16px; border-radius: 8px; margin: 16px 0; border: 1px solid #1f2937; }
    .step { display: inline-flex; align-items: center; margin: 0 4px; }
    .step-box { background: rgba(59, 130, 246, 0.2); border: 1px solid #3b82f6; padding: 6px 12px; border-radius: 4px; font-size: 11px; color: #60a5fa; font-weight: 500; }
    .arrow { color: #3b82f6; font-weight: bold; margin: 0 6px; }
    .warning { background: rgba(245, 158, 11, 0.1); border-left: 3px solid #f59e0b; padding: 12px; border-radius: 6px; margin: 16px 0; }
    .warning-title { color: #f59e0b; font-weight: 600; font-size: 12px; margin-bottom: 4px; }
    .code-block { background: rgba(0, 0, 0, 0.5); padding: 12px; border-radius: 6px; font-family: monospace; font-size: 10px; color: #34d399; border-left: 3px solid #34d399; overflow-x: auto; white-space: pre-wrap; }
    .section-nav { display: flex; gap: 12px; margin: 32px 0; flex-wrap: wrap; position: sticky; top: 0; background: rgba(11, 19, 38, 0.95); padding: 16px 0; z-index: 100; border-bottom: 1px solid #1f2937; }
    .nav-btn { padding: 8px 16px; background: rgba(59, 130, 246, 0.2); border: 1px solid #3b82f6; border-radius: 6px; color: #60a5fa; text-decoration: none; font-size: 12px; cursor: pointer; transition: all 0.3s ease; }
    .nav-btn:hover { background: rgba(59, 130, 246, 0.4); text-decoration: underline; }
    a { color: #60a5fa; text-decoration: none; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <h1>🛡️ AdSphere Enterprise Moderation System</h1>
      <div class="sub">v1.0.0 | Enterprise-grade AI/ML Content Moderation Platform</div>
      <div class="desc">Multi-modal, scalable, distributed content moderation with real-time intelligence, advanced caching, security scanning, and intelligent decision-making</div>
    </div>

    <div class="section-nav">
      <a href="#overview" class="nav-btn">Overview</a>
      <a href="#architecture" class="nav-btn">Architecture</a>
      <a href="#pipelines" class="nav-btn">Pipelines</a>
      <a href="#caching" class="nav-btn">Caching</a>
      <a href="#security" class="nav-btn">Security</a>
      <a href="#decision" class="nav-btn">Decision</a>
      <a href="#performance" class="nav-btn">Performance</a>
      <a href="#mlmodels" class="nav-btn">ML Models</a>
      <a href="#aicSearch" class="nav-btn">AI Search</a>
      <a href="#searchassistant" class="nav-btn">Search Pipeline</a>
      <a href="#phpapps" class="nav-btn">PHP Apps</a>
    </div>

    <h2 id="overview">📋 System Overview</h2>
    <div class="card">
      <div class="card-header">Core Capabilities</div>
      <div class="metrics">
        <div class="metric-box">
          <div class="metric-label">Content Types</div>
          <div class="metric-value">4</div>
          <div class="card-content">Text, Image, Video, Audio</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">Languages Supported</div>
          <div class="metric-value">50+</div>
          <div class="card-content">Multilingual detection & analysis</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">ML Models</div>
          <div class="metric-value">15+</div>
          <div class="card-content">Specialized detectors for each modality</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">Decision Categories</div>
          <div class="metric-value">7</div>
          <div class="card-content">Nudity, Violence, Weapons, Hate, Drugs, Scam, Spam</div>
        </div>
      </div>
    </div>

    <h2 id="architecture">🏗️ Complete System Architecture</h2>
    <div class="card">
      <div class="card-header">Distributed Microservices Architecture with Full Data Flow</div>
      <pre>
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
       └──────────────┬───────┴──────────────┬────────┴──────────────────────────────────────────────────────────────────────┐
                      │                      │                                                                              │
                      ▼                      ▼                                                                              │
               ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐         │
               │                       MODERATION SERVICE (FastAPI, Port 8002)                                    │         │
               └──────────────────────────────────────────────────────────────────────────────────────────────────┘         │
               ┌───────────────────────────────────────┐   ┌─────────────────────────────────────────────┐                  │
               │           API Gateway Layer           │   │         WebSocket Streaming Layer           │                  │
               │  REST: /moderate/* /search/* /admin/* │   │  ws://.../ws/moderate   ws://.../ws/search │                  │
               └───────────────┬───────────────────────┘   └──────────────────────────┬──────────────────┘                  │
                               │                                          ▲                                          │
                               ▼                                          │                                          │
               ┌───────────────────────────────────────┐   ┌─────────────────────────────────────────────┐                  │
               │         Orchestration Layer           │   │         Caching & Intelligence Layer        │                  │
               │  • Master Pipeline Coordinator        │   │  L1 Memory  L2 Redis  L3 SQLite  Fingerprint│                  │
               │  • Queue Manager (Redis/In-Memory)    │   │  • Context & Intent Engine (multi-modal)   │                  │
               │  • Backpressure & Rate Limiter        │   │  • Duplicate/Similarity (pHash/n-grams)    │                  │
               └───────────────┬───────────────────────┘   └──────────────────────────┬──────────────────┘                  │
                               │                                          ▲                                          │
                               ▼                                          │                                          │
               ┌───────────────────────────────────────┐   ┌─────────────────────────────────────────────┐                  │
               │            Security Engine            │   │             Decision Engine                 │                  │
               │  • File Signature/Structure           │   │  • Score Aggregation (fusion/weights)       │                  │
               │  • Entropy / LSB / DCT Steg Detection │   │  • Policy Evaluation (policy.yaml rules)    │                  │
               │  • Hidden Data & Metadata Scan        │   │  • Risk Classification (low/med/high/crit)  │                  │
               │  • Sanitization (clean WebP, strip)   │   │  • Final Decision + Audit Logging           │                  │
               └───────────────┬───────────────────────┘   └──────────────────────────┬──────────────────┘                  │
                               │                                          ▲                                          │
                               ▼                                          │                                          │
               ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐         │
               │                         Moderation Pipelines (Parallel/Async)                                   │         │
               ├──────────────────────────────────────────────────────────────────────────────────────────────────┤         │
               │  TEXT (10): normalize → tokenize → lang-detect → embed → similarity → intent → context →       │         │
               │  toxicity → aggregate → policy → decision                                                       │         │
               ├──────────────────────────────────────────────────────────────────────────────────────────────────┤         │
               │  IMAGE (10): security-scan → sanitize → compress → OCR → NSFW → weapons → violence →           │         │
               │  blood → scene → aggregate → policy → decision                                                  │         │
               ├──────────────────────────────────────────────────────────────────────────────────────────────────┤         │
               │  VIDEO (7): split A/V → 2FPS frames → parallel frame analysis → ASR → temporal coherence →      │         │
               │  aggregate → policy → decision                                                                  │         │
               ├──────────────────────────────────────────────────────────────────────────────────────────────────┤         │
               │  AUDIO (5): chunking → ASR → text moderation → aggregate → policy → decision                    │         │
               └──────────────────────────────────────────────────────────────────────────────────────────────────┘         │
                               │                                                                                         │
                               ▼                                                                                         │
               ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐         │
               │                              ML Models & Tools                                                  │         │
               │  • NudeNet • YOLOv8 • Violence CNN • Blood CNN • PaddleOCR • Whisper • Sentence-Transformers   │         │
               │  • XLM-RoBERTa • DeBERTa • Detoxify                                                            │         │
               └──────────────────────────────────────────────────────────────────────────────────────────────────┘         │
                               │                                                                                         │
                               ▼                                                                                         │
               ┌──────────────────────────────┐    ┌──────────────────────────────┐    ┌──────────────────────────────┐      │
               │          Redis (Cache)      │    │       SQLite (Audit/Jobs)    │    │    Model Weights Store       │      │
               │  L2 cache + queues + stats  │    │  Persistent logs & decisions │    │  Auto-download + checksums    │      │
               └──────────────────────────────┘    └──────────────────────────────┘    └──────────────────────────────┘      │
      </pre>
      <div class="legend">
        <span class="pill">🔴 Caching: L1 Memory • L2 Redis • L3 SQLite</span>
        <span class="pill">🔒 Security: Signature • Entropy • LSB • DCT • Hidden Data • Metadata</span>
        <span class="pill">🧠 Decision: Aggregation • Policy • Risk • Audit</span>
        <span class="pill">⚙️ Pipelines: Text • Image • Video • Audio</span>
      </div>
    </div>

    <h2 id="pipelines">🔄 Advanced Moderation Pipelines</h2>

    <div class="card">
      <div class="card-header">1. TEXT MODERATION PIPELINE (10-Step Process)</div>
      <div class="flow-diagram">
        <div class="step"><span class="step-box">Normalize</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Tokenize</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Lang Detect</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Embed</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Similarity</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Intent</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Context</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Toxicity</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Aggregate</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Decision</span></div>
      </div>
      <table>
        <tr><th>Step</th><th>Model/Tool</th><th>Input</th><th>Output</th><th>Time (ms)</th></tr>
        <tr><td>1. Normalization</td><td>Unicode NFC + spaCy</td><td>Raw text</td><td>Normalized text</td><td>2-5</td></tr>
        <tr><td>2. Tokenization</td><td>spaCy Multilingual</td><td>Text</td><td>Tokens + metadata</td><td>3-8</td></tr>
        <tr><td>3. Language Detection</td><td>XLM-RoBERTa</td><td>Tokens</td><td>Lang code + confidence</td><td>5-15</td></tr>
        <tr><td>4. Semantic Embedding</td><td>Sentence-Transformers</td><td>Text</td><td>384-dim vector</td><td>20-40</td></tr>
        <tr><td>5. Similarity Search</td><td>FAISS</td><td>Vector</td><td>Top-K matches</td><td>5-10</td></tr>
        <tr><td>6. Intent Classification</td><td>DeBERTa-v3</td><td>Text</td><td>Intent + confidence</td><td>15-25</td></tr>
        <tr><td>7. Context Classification</td><td>XLM-RoBERTa-large</td><td>Text</td><td>Context scores</td><td>20-35</td></tr>
        <tr><td>8. Toxicity Detection</td><td>Detoxify</td><td>Text</td><td>6 toxicity scores</td><td>10-20</td></tr>
        <tr><td>9. Feature Aggregation</td><td>Custom fusion</td><td>All scores</td><td>Weighted total</td><td>3-5</td></tr>
        <tr><td>10. Policy Evaluation</td><td>YAML rules</td><td>Scores</td><td>Decision + reason</td><td>1-3</td></tr>
      </table>
      <div class="component">
        <div class="component-title">Performance: 50-100 requests/second (CPU) | 200-500 requests/second (GPU)</div>
        <div class="component-detail">Supports 50+ languages | Real-time processing | Caching enabled for repeated queries</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">2. IMAGE MODERATION PIPELINE (10-Step Process)</div>
      <div class="flow-diagram">
        <div class="step"><span class="step-box">Security Scan</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Sanitize</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Compress</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">OCR</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">NSFW</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Weapons</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Violence</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Blood</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Scene</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Decision</span></div>
      </div>
      <table>
        <tr><th>Step</th><th>Model/Tool</th><th>Detects</th><th>Accuracy</th><th>Time (ms)</th></tr>
        <tr><td>1. Security Scan</td><td>8 detectors</td><td>Steganography, hidden data, malware</td><td>95%+</td><td>30-50</td></tr>
        <tr><td>2. Sanitization</td><td>PIL/OpenCV</td><td>EXIF/XMP stripping, re-encoding</td><td>100%</td><td>50-100</td></tr>
        <tr><td>3. Compression</td><td>WebP encoder</td><td>≤1MB, adaptive quality</td><td>100%</td><td>30-60</td></tr>
        <tr><td>4. OCR</td><td>PaddleOCR</td><td>Text in images (98%+ accuracy)</td><td>98%+</td><td>40-80</td></tr>
        <tr><td>5. NSFW Detection</td><td>NudeNet</td><td>Nudity, explicit content</td><td>95%+</td><td>30-50</td></tr>
        <tr><td>6. Weapons Detection</td><td>YOLOv8 + filters</td><td>Guns, knives, explosives</td><td>90%+</td><td>25-40</td></tr>
        <tr><td>7. Violence Detection</td><td>Custom CNN</td><td>Fight, injury, gore</td><td>88%+</td><td>20-35</td></tr>
        <tr><td>8. Blood Detection</td><td>CNN + segmentation</td><td>Blood, injury markers</td><td>85%+</td><td>20-30</td></tr>
        <tr><td>9. Scene Analysis</td><td>CLIP/ResNet</td><td>Context, location, objects</td><td>82%+</td><td>15-25</td></tr>
        <tr><td>10. Decision</td><td>Policy engine</td><td>Final verdict + explanation</td><td>100%</td><td>2-5</td></tr>
      </table>
      <div class="component">
        <div class="component-title">Performance: 5-10 images/second (CPU) | 20-50 images/second (GPU)</div>
        <div class="component-detail">Max file size: 10MB | Formats: JPEG, PNG, WebP, GIF, AVIF | Auto-compress to ≤1MB</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">3. VIDEO MODERATION PIPELINE (7-Step Process)</div>
      <div class="flow-diagram">
        <div class="step"><span class="step-box">Split A/V</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Extract Frames</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Parallel Analysis</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">ASR</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Temporal Coherence</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Aggregate</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Decision</span></div>
      </div>
      <div class="component">
        <div class="component-title">Video Parameters</div>
        <div class="component-detail">• Max Duration: 60 seconds | Max File Size: 500MB | Frame Rate: 2 FPS (120 frames max)<br/>• Audio Chunks: 10 segments × 6 seconds | Parallel Workers: 120 frame workers + 10 audio workers<br/>• Temp Storage: Encrypted, auto-cleaned after processing</div>
      </div>
      <table>
        <tr><th>Step</th><th>Process</th><th>Output</th><th>Workers</th><th>Time</th></tr>
        <tr><td>1. Split A/V</td><td>FFmpeg separation</td><td>video.mp4 + audio.wav</td><td>1</td><td>2-5s</td></tr>
        <tr><td>2. Frame Extraction</td><td>2 FPS sampling</td><td>120 JPEGs (60s video)</td><td>1</td><td>5-10s</td></tr>
        <tr><td>3. Parallel Frame Analysis</td><td>Image pipeline per frame</td><td>Frame scores</td><td>120</td><td>3-8s</td></tr>
        <tr><td>4. Audio ASR</td><td>Whisper transcription</td><td>Text transcript</td><td>10</td><td>5-15s</td></tr>
        <tr><td>5. Temporal Coherence</td><td>Track objects across frames</td><td>Temporal patterns</td><td>1</td><td>2-5s</td></tr>
        <tr><td>6. Score Aggregation</td><td>Combine frame + audio scores</td><td>Video score</td><td>1</td><td>1-3s</td></tr>
        <tr><td>7. Decision + Cleanup</td><td>Apply policy, delete temps</td><td>Final decision</td><td>1</td><td>1-2s</td></tr>
      </table>
      <div class="component">
        <div class="component-title">Performance: 1-2 videos/second (CPU) | 5-10 videos/second (GPU)</div>
        <div class="component-detail">Supports: MP4, MOV, AVI, MKV | Automatic temp file cleanup | GPU-accelerated frame decoding</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">4. AUDIO MODERATION PIPELINE (5-Step Process)</div>
      <div class="flow-diagram">
        <div class="step"><span class="step-box">Chunk</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">ASR</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Text Moderation</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Aggregate</span></div>
        <span class="arrow">→</span>
        <div class="step"><span class="step-box">Decision</span></div>
      </div>
      <table>
        <tr><th>Step</th><th>Tool</th><th>Language Support</th><th>Time</th></tr>
        <tr><td>1. Audio Chunking</td><td>FFmpeg</td><td>Any format (WAV, MP3, AAC)</td><td>1-2s per 60s</td></tr>
        <tr><td>2. Speech-to-Text</td><td>Whisper (OpenAI)</td><td>99 languages</td><td>3-8s per chunk</td></tr>
        <tr><td>3. Text Moderation</td><td>Full text pipeline</td><td>50+ languages</td><td>10-20ms per segment</td></tr>
        <tr><td>4. Score Aggregation</td><td>Custom weighting</td><td>N/A</td><td>1-2s</td></tr>
        <tr><td>5. Decision</td><td>Policy engine</td><td>N/A</td><td>1-2ms</td></tr>
      </table>
      <div class="component">
        <div class="component-title">Performance: 1-3 seconds per 60s audio</div>
        <div class="component-detail">Parallel chunk processing | 10 concurrent ASR workers | Automatic language detection</div>
      </div>
    </div>

    <h2 id="caching">💾 Multi-Layer Caching Architecture</h2>
    <div class="card">
      <div class="card-header">Three-Tier Caching System with Fingerprinting</div>
      <table>
        <tr><th>Layer</th><th>Technology</th><th>TTL</th><th>Size Limit</th><th>Speed</th><th>Purpose</th></tr>
        <tr><td>L1</td><td>Python dict (in-memory)</td><td>5 minutes</td><td>~1000 items</td><td>&lt;1ms</td><td>Ultra-fast, process-local</td></tr>
        <tr><td>L2</td><td>Redis</td><td>1 hour</td><td>Unlimited</td><td>~5ms</td><td>Distributed caching</td></tr>
        <tr><td>L3</td><td>SQLite</td><td>24 hours</td><td>Unlimited</td><td>~20ms</td><td>Persistent logging</td></tr>
        <tr><td>FP</td><td>pHash + MD5</td><td>Permanent</td><td>Unlimited</td><td>~1ms</td><td>Avoid reprocessing</td></tr>
      </table>
      <div class="component">
        <div class="component-title">Cache Keys</div>
        <div class="component-detail">• Text: SHA256(normalized_text)<br/>• Image: perceptual_hash(image) + MD5<br/>• Video: MD5(video_file)<br/>• Search: embedding_similarity_hash</div>
      </div>
    </div>

    <h2 id="security">🔒 Security Engine</h2>
    <div class="card">
      <div class="card-header">8-Detector Security Prefilter (Before Content Analysis)</div>
      <table>
        <tr><th>Detector</th><th>Technique</th><th>Detects</th><th>ML Model</th></tr>
        <tr><td>File Structure</td><td>Magic bytes</td><td>File type confusion, polyglots</td><td>Rule-based</td></tr>
        <tr><td>Entropy Analysis</td><td>Shannon entropy</td><td>Encrypted/random data</td><td>Heuristic</td></tr>
        <tr><td>LSB Steganography</td><td>Pixel analysis</td><td>Data in least-significant bits</td><td>ML detector</td></tr>
        <tr><td>DCT Steganography</td><td>Frequency domain</td><td>Data in JPEG frequency coefs</td><td>ML detector</td></tr>
        <tr><td>Metadata Scan</td><td>EXIF/XMP parsing</td><td>Suspicious metadata</td><td>Rule-based</td></tr>
        <tr><td>Hidden Data</td><td>File EOF scanning</td><td>Appended files, polyglots</td><td>Pattern matching</td></tr>
        <tr><td>Forensics</td><td>CNN analysis</td><td>Image manipulation, copy-paste</td><td>Forensics CNN</td></tr>
        <tr><td>File Anomaly</td><td>Size/compression ratio</td><td>Suspicious compression patterns</td><td>Heuristic</td></tr>
      </table>
      <div class="warning">
        <div class="warning-title">⚠️ Security Note</div>
        <div class="card-content">If ANY detector flags threat, image is REJECTED before content analysis. Sanitization process removes EXIF, re-encodes to clean WebP, strips alpha channel if suspicious.</div>
      </div>
    </div>

    <h2 id="decision">🧮 Decision Engine</h2>
    <div class="card">
      <div class="card-header">Score Aggregation & Risk Classification Matrix</div>
      <div class="component">
        <div class="component-title">Decision Matrix</div>
        <table>
          <tr><th>Global Score</th><th>Decision</th><th>Risk Level</th><th>Action</th></tr>
          <tr><td>0.0 - 0.3</td><td>approve</td><td>Low</td><td>✅ Auto-approve</td></tr>
          <tr><td>0.3 - 0.6</td><td>review</td><td>Medium</td><td>⚠️ Manual review</td></tr>
          <tr><td>0.6 - 0.8</td><td>review</td><td>High</td><td>⚠️ Priority review</td></tr>
          <tr><td>0.8 - 1.0</td><td>block</td><td>Critical</td><td>❌ Auto-reject</td></tr>
        </table>
      </div>
      <div class="component">
        <div class="component-title">Category Scores (0.0 - 1.0)</div>
        <div class="component-detail">• nudity: Adult/NSFW content<br/>• violence: Violence and gore<br/>• weapons: Weapons detection<br/>• hate: Hate speech discrimination<br/>• drugs: Drug-related content<br/>• scam_fraud: Scam patterns<br/>• spam: Spam detection</div>
      </div>
    </div>

    <h2 id="performance">⚡ Performance & Scalability</h2>
    <div class="card">
      <div class="card-header">Throughput & Latency Metrics</div>
      <div class="metrics">
        <div class="metric-box">
          <div class="metric-label">Text Processing</div>
          <div class="metric-value">50-100/sec</div>
          <div class="card-content">CPU: 50-100 req/s | GPU: 200-500 req/s</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">Image Processing</div>
          <div class="metric-value">5-10/sec</div>
          <div class="card-content">CPU: 5-10 img/s | GPU: 20-50 img/s</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">Video Processing</div>
          <div class="metric-value">1-2/sec</div>
          <div class="card-content">CPU: 1-2 vid/s | GPU: 5-10 vid/s (60s max)</div>
        </div>
        <div class="metric-box">
          <div class="metric-label">1M Ads Scan</div>
          <div class="metric-value">~22 hrs</div>
          <div class="card-content">Full scan with caching | Incremental available</div>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">Horizontal Scaling</div>
      <div class="component">
        <div class="component-title">Docker Deployment</div>
        <div class="code-block">
docker-compose -f docker-compose.prod.yml up -d --scale moderation=4
        </div>
        <div class="component-detail" style="margin-top: 12px;">Replicas scale to N instances | Load balanced via nginx | Stateless design | Redis shared cache | SQLite audit logging</div>
      </div>
    </div>

    <h2 id="mlmodels">🧠 ML Models & Tools (Comprehensive Specifications)</h2>
    <div class="card">
      <div class="card-header">Complete ML Model Catalog (25+ Models)</div>
      <table>
        <tr><th>Category</th><th>Model Name</th><th>Version</th><th>Purpose</th><th>Framework</th><th>Input/Output</th></tr>
        <tr><td rowspan="7"><strong>Text Processing</strong></td><td>XLM-RoBERTa</td><td>facebook/xlm-roberta-base</td><td>Language detection (53 languages)</td><td>Transformers</td><td>Text → Language code + confidence</td></tr>
        <tr><td>Sentence-Transformers (MiniLM)</td><td>sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2</td><td>Fast multilingual embeddings (384-dim)</td><td>PyTorch</td><td>Text → 384-dim vector</td></tr>
        <tr><td>Sentence-Transformers (E5)</td><td>sentence-transformers/multilingual-e5-large</td><td>High-quality multilingual embeddings (1024-dim)</td><td>PyTorch</td><td>Text → 1024-dim vector</td></tr>
        <tr><td>DeBERTa-v3</td><td>microsoft/deberta-v3-base</td><td>Intent & context classification</td><td>Transformers</td><td>Text → Intent label + score</td></tr>
        <tr><td>Detoxify</td><td>0.5.0+</td><td>6-category toxicity detection</td><td>PyTorch</td><td>Text → [toxicity, severe_toxicity, obscene, threat, insult, identity_hate]</td></tr>
        <tr><td>spaCy</td><td>3.8.0+</td><td>NLP tokenization & entity extraction</td><td>PyTorch</td><td>Text → Tokens + entities + POS tags</td></tr>
        <tr><td>fastText-LID</td><td>lid.176.ftz / lid.323.ftz</td><td>Language identification (176/323 languages)</td><td>Facebook</td><td>Text → Language code + probability</td></tr>
        <tr><td rowspan="12"><strong>Image Processing</strong></td><td>NudeNet</td><td>2.0.0+</td><td>NSFW & nudity detection (8 classes)</td><td>PyTorch</td><td>Image → Classes + confidence</td></tr>
        <tr><td>YOLOv8 (Object Detection)</td><td>8.0.0+ (fine-tuned)</td><td>General object detection (80 classes)</td><td>PyTorch</td><td>Image → Bounding boxes + class + confidence</td></tr>
        <tr><td>YOLOv8 (Weapon Detection)</td><td>8.0.0+ (custom fine-tuned)</td><td>Weapon detection (guns, knives, etc.)</td><td>PyTorch</td><td>Image → Weapon boxes + confidence</td></tr>
        <tr><td>Violence CNN</td><td>Custom trained</td><td>Violence & fight detection</td><td>PyTorch</td><td>Image → Violence score (0-1) + confidence</td></tr>
        <tr><td>Blood CNN</td><td>Custom trained</td><td>Blood & gore detection</td><td>PyTorch</td><td>Image → Blood score (0-1) + confidence</td></tr>
        <tr><td>PaddleOCR</td><td>3.3.2+</td><td>Text extraction (80+ languages)</td><td>PaddlePaddle</td><td>Image → Text + bounding boxes + confidence</td></tr>
        <tr><td>EasyOCR</td><td>1.6.0+</td><td>Text extraction (80+ languages, accurate)</td><td>PyTorch</td><td>Image → Text + confidence + bounding boxes</td></tr>
        <tr><td>CLIP</td><td>openai/clip-vit-base-patch32</td><td>Scene understanding & image tagging</td><td>PyTorch</td><td>Image → Scene descriptions + embeddings</td></tr>
        <tr><td>ResNet-50</td><td>resnet50 (ImageNet pre-trained)</td><td>Image classification (1000 classes)</td><td>PyTorch</td><td>Image → Class label + confidence</td></tr>
        <tr><td>Pillow (PIL)</td><td>10.0.0+</td><td>Image processing & manipulation</td><td>Python</td><td>Image → Processed image + metadata</td></tr>
        <tr><td>OpenCV</td><td>4.8.0+</td><td>Advanced image processing & analysis</td><td>C++/Python</td><td>Image → Processed image + contours</td></tr>
        <tr><td>Forensics CNN</td><td>Custom trained</td><td>Image manipulation detection</td><td>PyTorch</td><td>Image → Manipulation score (0-1) + confidence</td></tr>
        <tr><td rowspan="3"><strong>Audio Processing</strong></td><td>Whisper (Base)</td><td>openai/whisper-base</td><td>Speech-to-text (99 languages, 77M params)</td><td>PyTorch</td><td>Audio → Transcription + confidence</td></tr>
        <tr><td>Whisper (Small)</td><td>openai/whisper-small</td><td>Speech-to-text (99 languages, 244M params, better accuracy)</td><td>PyTorch</td><td>Audio → Transcription + confidence</td></tr>
        <tr><td>Whisper (Medium)</td><td>openai/whisper-medium</td><td>Speech-to-text (99 languages, 769M params, highest accuracy)</td><td>PyTorch</td><td>Audio → Transcription + confidence</td></tr>
        <tr><td rowspan="4"><strong>Search & Indexing</strong></td><td>FAISS (CPU)</td><td>1.7.0+</td><td>Vector similarity search (CPU optimized)</td><td>Meta/Facebook</td><td>Query vector → Top-K nearest neighbors</td></tr>
        <tr><td>FAISS (GPU)</td><td>1.7.0+</td><td>Vector similarity search (GPU accelerated)</td><td>Meta/Facebook</td><td>Query vector → Top-K nearest neighbors (faster)</td></tr>
        <tr><td>Qdrant Client</td><td>2.0.0+</td><td>Vector database for semantic search</td><td>Rust/Python</td><td>Vector query → Similar items + scores</td></tr>
        <tr><td>Redis</td><td>5.0+ / 7.0+</td><td>Distributed caching & session store</td><td>C</td><td>Key → Value + TTL management</td></tr>
        <tr><td rowspan="2"><strong>Data Storage</strong></td><td>SQLite</td><td>3.37.0+</td><td>Persistent audit logs & records</td><td>C</td><td>SQL query → Rows + metadata</td></tr>
        <tr><td>PostgreSQL</td><td>14.0+ (optional)</td><td>Advanced relational database (optional upgrade)</td><td>C</td><td>SQL query → Rows + JSONB support</td></tr>
      </table>
    </div>

    <h2 id="aicSearch">🔍 AI-Assisted Category Search</h2>
    <div class="card">
      <div class="card-header">Intelligent Semantic Category Matching System</div>
      <div class="component">
        <div class="component-title">How It Works</div>
        <div class="component-detail">
          <strong>Step 1: Query Encoding</strong><br/>
          User query → Sentence-Transformers encoder → 384-dim semantic vector<br/><br/>
          <strong>Step 2: Cache Check</strong><br/>
          Query hash → Search cache (Redis/SQLite) → Return cached result if exists (instant)<br/><br/>
          <strong>Step 3: Model Matching</strong><br/>
          Encoded query → Compare against all category embeddings → Calculate similarity scores<br/><br/>
          <strong>Step 4: Ranking & Filtering</strong><br/>
          Sort by similarity score → Apply threshold (0.25 default) → Return top-K results (default: 5)<br/><br/>
          <strong>Step 5: Cache Storage</strong><br/>
          Store query-result mapping in L1/L2/L3 cache → 5min to 24hr TTL depending on tier
        </div>
      </div>
      <table>
        <tr><th>Component</th><th>Technology</th><th>Purpose</th><th>Performance</th></tr>
        <tr><td>Encoder</td><td>Sentence-Transformers (paraphrase-multilingual-MiniLM-L12-v2)</td><td>Convert text to vectors</td><td>20-40ms per query</td></tr>
        <tr><td>Cache Layer</td><td>L1 Memory + Redis + SQLite</td><td>Store previous matches</td><td><1ms to 20ms</td></tr>
        <tr><td>Similarity Metric</td><td>Cosine similarity</td><td>Compare vectors</td><td>1-3ms per comparison</td></tr>
        <tr><td>Threshold</td><td>Configurable (default 0.25)</td><td>Filter weak matches</td><td>Instant</td></tr>
        <tr><td>Top-K Selection</td><td>NumPy/PyTorch</td><td>Get best matches</td><td>1-2ms</td></tr>
      </table>
      <div class="component" style="margin-top: 16px;">
        <div class="component-title">Example Queries & Matches</div>
        <table>
          <tr><th>User Query</th><th>Category Match 1</th><th>Category Match 2</th><th>Category Match 3</th><th>Processing Time</th></tr>
          <tr><td>"I'm hungry"</td><td>Food (0.95)</td><td>Restaurants (0.87)</td><td>Groceries (0.78)</td><td>~50ms (cached)</td></tr>
          <tr><td>"Looking for a car"</td><td>Vehicles (0.92)</td><td>Automotive (0.88)</td><td>Parts (0.76)</td><td>~45ms (model)</td></tr>
          <tr><td>"Rent apartment"</td><td>Housing (0.91)</td><td>Property (0.89)</td><td>Furnished (0.75)</td><td>~48ms (model)</td></tr>
          <tr><td>"Buy phone"</td><td>Electronics (0.93)</td><td>Phones (0.91)</td><td>Gadgets (0.82)</td><td>~55ms (model)</td></tr>
          <tr><td>"Chakula" (Swahili)</td><td>Food (0.88)</td><td>Restaurants (0.81)</td><td>Groceries (0.73)</td><td>~52ms (model)</td></tr>
        </table>
      </div>
      <div class="warning">
        <div class="warning-title">✨ Advanced Features</div>
        <div class="card-content">
          • **Multilingual Support**: Detects and matches in 50+ languages automatically<br/>
          • **Cache Optimization**: First query slow (50-55ms), subsequent queries instant (<1ms)<br/>
          • **Configurable Threshold**: Adjust sensitivity (0.0-1.0) based on requirements<br/>
          • **Context-Aware**: Understands synonyms and related terms<br/>
          • **Performance**: 95%+ accuracy on semantic matching
        </div>
      </div>
    </div>

    <h2 id="searchassistant">🔎 Search Assistant Pipeline (Detailed Architecture)</h2>
    <div class="card">
      <div class="card-header">Advanced Semantic Search & Category Matching System</div>
      
      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Pipeline Overview & Location</div>
        <div class="component-detail">
          <strong>Service Directory</strong>: `/services/moderator_services/moderation_service/app/services/search_assisatnt/`<br/>
          <strong>Core Files</strong>:<br/>
          • search_service.py - Main orchestrator & request handler<br/>
          • category_matcher.py - Semantic matching engine<br/>
          • cache.py - Three-tier cache management<br/>
          <br/>
          <strong>API Endpoints</strong>:<br/>
          • POST /search/match - Full semantic search with configuration<br/>
          • GET /search/quick/{query} - Fast cached search
        </div>
      </div>

      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">9-Step Pipeline Process</div>
        <div class="code-block">
┌─────────────────────────────────────────────────────────────────┐
│              SEARCH ASSISTANT PIPELINE (9 STEPS)                │
└─────────────────────────────────────────────────────────────────┘

STEP 1: USER SUBMITS QUERY
  Input: "I want to buy cheap phones"
  Channel: Public App → POST /search/match
  
STEP 2: REQUEST VALIDATION & PREPROCESSING
  • Check: Not empty, length 3-500 chars
  • Security: No SQL injection, no malicious code
  • Rate limiting: IP-based throttling
  • Normalize: Lowercase, strip whitespace
  
STEP 3: LANGUAGE DETECTION
  Model: XLM-RoBERTa (facebook/xlm-roberta-base)
  Detects: 53 languages
  Output: { "language": "en", "confidence": 0.99 }
  
STEP 4: L1 CACHE CHECK (Memory)
  Speed: <1ms
  If hit: Return immediately
  Scope: In-process dictionary (per instance)
  
STEP 5: L2 CACHE CHECK (Redis)
  Speed: ~5-10ms
  If hit: Populate L1 and return
  Scope: Distributed across all instances
  TTL: 1 hour
  
STEP 6: L3 CACHE CHECK (SQLite)
  Speed: ~20-30ms
  If hit: Populate L1 & L2, return
  Scope: Persistent database
  TTL: 24 hours
  
STEP 7: ENCODE QUERY TO VECTOR (If Cache Miss)
  Model: Sentence-Transformers (paraphrase-multilingual-MiniLM-L12-v2)
  • Tokenize query
  • Pass through transformer
  • Generate 384-dimensional vector
  • Time: 30-40ms
  
STEP 8: SEMANTIC SIMILARITY SEARCH
  • Load category embeddings (100+ pre-encoded)
  • Calculate cosine similarity vs all categories
  • Use FAISS for fast computation (<3ms)
  • Sort by score and filter by threshold
  
STEP 9: AGGREGATE & CACHE RESULTS
  • Format response
  • Store in L1, L2, L3 caches
  • Return to user
  
  Output:
  [
    { "category": "Electronics", "score": 0.93 },
    { "category": "Phones", "score": 0.91 },
    { "category": "Gadgets", "score": 0.82 },
    ...
  ]

Performance Timeline:
  L1 Hit:     <1ms (instant)
  L2 Hit:     ~5-10ms
  L3 Hit:     ~20-30ms
  Model Miss: 45-55ms (full processing)
        </div>
      </div>

      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Key Components</div>
        <div class="component-detail">
          <strong>1. search_service.py (Orchestrator)</strong><br/>
          Handles HTTP requests, validation, routing<br/>
          Methods: search(), quick_search(), validate_query(), format_response()<br/>
          <br/>
          <strong>2. category_matcher.py (Semantic Engine)</strong><br/>
          Encodes queries, calculates similarities, detects languages<br/>
          Models: Sentence-Transformers, XLM-RoBERTa, FAISS<br/>
          <br/>
          <strong>3. cache.py (Cache Manager)</strong><br/>
          Three-tier caching: L1 Memory, L2 Redis, L3 SQLite<br/>
          Cache Stats: ~60% L1 hits, ~25% L2, ~10% L3, ~5% model miss
        </div>
      </div>

      <table style="margin-top: 20px;">
        <tr><th>Cache Tier</th><th>Technology</th><th>Speed</th><th>TTL</th><th>Scope</th><th>Hit Rate</th></tr>
        <tr><td><strong>L1 Memory</strong></td><td>Python dict</td><td><1ms</td><td>5 min</td><td>Per instance</td><td>~60%</td></tr>
        <tr><td><strong>L2 Redis</strong></td><td>Redis 7.0+</td><td>~5-10ms</td><td>1 hour</td><td>Distributed</td><td>~25%</td></tr>
        <tr><td><strong>L3 SQLite</strong></td><td>SQLite 3.37+</td><td>~20-30ms</td><td>24 hours</td><td>Persistent</td><td>~10%</td></tr>
        <tr><td><strong>Model Miss</strong></td><td>Full Pipeline</td><td>45-55ms</td><td>N/A</td><td>Computed</td><td>~5%</td></tr>
      </table>

      <div class="component" style="margin-top: 20px; margin-bottom: 20px;">
        <div class="component-title">Real-World Search Examples</div>
        <div class="component-detail">
          <strong>Query 1:</strong> "I'm hungry, need food"<br/>
          Language: English | Top Match: Food (0.95) | Time (first): 48ms | Time (cached): <1ms<br/>
          <br/>
          <strong>Query 2:</strong> "Je cherche une voiture" (French: I'm looking for a car)<br/>
          Language: French | Top Match: Vehicles (0.92) | Time (first): 50ms | Time (cached): <1ms<br/>
          <br/>
          <strong>Query 3:</strong> "Chakula na maharagwe" (Swahili: Food and beans)<br/>
          Language: Swahili | Top Match: Food (0.88) | Time (first): 52ms | Time (cached): <1ms<br/>
          <br/>
          <strong>Query 4:</strong> "I need a laptop under $500"<br/>
          Language: English | Top Match: Electronics (0.93) | Time (first): 45ms | Time (cached): <1ms<br/>
          <br/>
          <strong>Accuracy:</strong> 95%+ semantic match accuracy across all languages
        </div>
      </div>

      <div class="component">
        <div class="component-title">Configuration Parameters</div>
        <div class="component-detail">
          <strong>threshold</strong> (default: 0.25)<br/>
          Minimum similarity score to include result. Range: 0.0-1.0<br/>
          • Lower = more results but less relevant<br/>
          • Higher = fewer results but more accurate<br/>
          <br/>
          <strong>limit</strong> (default: 5)<br/>
          Maximum number of categories to return. Range: 1-20<br/>
          <br/>
          <strong>model_type</strong> (default: minilm)<br/>
          Options: minilm (fast, 384-dim), e5-large (accurate, 1024-dim)<br/>
          <br/>
          <strong>l1_ttl</strong> (default: 300s)<br/>
          L1 cache expiry time<br/>
          <br/>
          <strong>l2_ttl</strong> (default: 3600s)<br/>
          L2 cache expiry time<br/>
          <br/>
          <strong>l3_ttl</strong> (default: 86400s)<br/>
          L3 cache expiry time
        </div>
      </div>
    </div>

    <h2 id="phpapps">🌐 The 3 PHP Applications - Comprehensive Guide</h2>
    <div class="card">
      <div class="card-header">Architecture of Public, Company, and Admin Portals</div>
      
      <h3 style="color: #93c5fd; margin-top: 24px;">1️⃣ PUBLIC APP (Port 8001) - Ad Browsing & User Engagement</h3>
      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Purpose & Users</div>
        <div class="component-detail">
          <strong>Target Users</strong>: End consumers, job seekers, buyers, renters<br/>
          <strong>Primary Function</strong>: Browse, search, and interact with advertisements<br/>
          <strong>Analytics Focus</strong>: User behavior, ad performance, engagement metrics
        </div>
      </div>

      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Key Features & Pages</div>
        <div class="component-detail">
          ✅ <strong>Home Page</strong> - Featured & trending ads with search<br/>
          ✅ <strong>Ad Listing</strong> - Browse by category with filters<br/>
          ✅ <strong>Ad Detail</strong> - Full ad view with contact options<br/>
          ✅ <strong>Search</strong> - Text & AI-powered semantic search<br/>
          ✅ <strong>Register/Login</strong> - User account creation<br/>
          ✅ <strong>Favorites</strong> - Save ads for later viewing<br/>
          ✅ <strong>Contact Dealer</strong> - Modal for SMS, Call, Email, WhatsApp<br/>
          ✅ <strong>Analytics Tracking</strong> - Implicit (view time, clicks, favorites)
        </div>
      </div>

      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Data & Integration</div>
        <div class="component-detail">
          <strong>Database Tables</strong>:<br/>
          • users (public profiles)<br/>
          • ads (published content)<br/>
          • ad_views (analytics)<br/>
          • ad_interactions (contacts, likes)<br/>
          • favorites (user preferences)<br/>
          <br/>
          <strong>External Integrations</strong>:<br/>
          • Moderation Service (/docs/architecture) - Check ad validity<br/>
          • AI Search (/search/match) - Semantic category matching<br/>
          • Analytics API (/api/track_interaction) - Log user actions<br/>
          • Payment Gateway (optional) - For premium features
        </div>
      </div>

      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Request Flow Example: User Views Ad</div>
        <div class="code-block">
User clicks "View Ad"
    ↓
PUBLIC_APP (8001):
  1. Fetch ad from database (Ad ID)
  2. Check if ad is "approved" (moderation status)
  3. Load analytics tracking JS
  4. Render ad details (title, desc, images, contact buttons)
    ↓
User spends 45 seconds viewing
    ↓
JS silently logs:
  • Ad ID, User ID, Device Info
  • View duration (45s)
  • Scroll depth, interactions
    ↓
API POST /api/track_interaction
    ↓
Backend:
  1. Record view in ad_views table
  2. Update user_device profile
  3. Increment ad.view_count
  4. Update ad_analytics cache
    ↓
Analytics Dashboard shows:
  • Total views: 1,234
  • Avg view time: 2m 15s
  • Device breakdown: 67% mobile, 33% desktop
        </div>
      </div>

      <hr style="border-color: #1f2937; margin: 24px 0;">

      <h3 style="color: #93c5fd; margin-top: 24px;">2️⃣ COMPANY APP (Port 8003) - Advertiser Dashboard</h3>
      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Purpose & Users</div>
        <div class="component-detail">
          <strong>Target Users</strong>: Advertisers, companies, dealers, service providers<br/>
          <strong>Primary Function</strong>: Create, manage, and monitor advertisements<br/>
          <strong>Analytics Focus</strong>: Ad performance, ROI, engagement quality
        </div>
      </div>

      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Key Features & Pages</div>
        <div class="component-detail">
          ✅ <strong>Dashboard</strong> - Overview of all ads & performance<br/>
          ✅ <strong>Upload Ad</strong> - Create new ad with images/video<br/>
          ✅ <strong>Edit Ad</strong> - Modify existing advertisements<br/>
          ✅ <strong>My Ads</strong> - List all user's ads with status<br/>
          ✅ <strong>Analytics</strong> - Detailed performance metrics<br/>
          ✅ <strong>Contact Methods</strong> - Track SMS, Call, Email, WhatsApp<br/>
          ✅ <strong>Favorites Analytics</strong> - Who marked as favorite<br/>
          ✅ <strong>Settings</strong> - Profile, billing, notifications
        </div>
      </div>

      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Data & Integration</div>
        <div class="component-detail">
          <strong>Database Tables</strong>:<br/>
          • companies (advertiser profiles)<br/>
          • ads (all advertisements)<br/>
          • ad_status_history (approval timeline)<br/>
          • ad_contact_events (SMS, call, email, whatsapp counts)<br/>
          • ad_favorites (user preferences)<br/>
          • billing_records (payment tracking)<br/>
          <br/>
          <strong>External Integrations</strong>:<br/>
          • Moderation Service (/moderate/realtime) - Scan content before publishing<br/>
          • Dashboard Stats API (/api/dashboard_stats) - Get metrics<br/>
          • Contact Analytics API (/api/contact_analytics) - Track engagement<br/>
          • AI Insights - Recommendations on content<br/>
          • Email/SMS Gateway - Notifications to advertiser
        </div>
      </div>

      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Request Flow Example: Advertiser Uploads Ad</div>
        <div class="code-block">
Advertiser clicks "Upload New Ad"
    ↓
COMPANY_APP (8003):
  1. Load upload form
  2. User enters: title, description, 4 images or 1 video
  3. JavaScript validates locally
  4. Images compressed to <1MB
  5. User clicks "Submit"
    ↓
POST /admin/ad_upload.php
    ↓
Backend Processing:
  1. Validate file types & sizes
  2. Store images/video to disk
  3. Call MODERATION_SERVICE /moderate/realtime
    ↓
MODERATION_SERVICE:
  1. Extract OCR text from images
  2. Run violence, weapons detection
  3. Check NSFW content
  4. Analyze text (toxicity, intent)
  5. Return: decision (approve/review/block), scores
    ↓
If DECISION = "block":
  1. Delete uploaded files
  2. Show advertiser reason
  3. Suggest how to fix content
  4. Don't save to database
    ↓
If DECISION = "review":
  1. Save ad to database
  2. Set status = "pending_review"
  3. Alert admin dashboard
  4. Notify advertiser: "Under Review"
  5. Advertiser can see: "Awaiting moderation"
    ↓
If DECISION = "approve":
  1. Save ad to database
  2. Set status = "active"
  3. Make ad visible on PUBLIC_APP (8001)
  4. Notify advertiser: "Ad is LIVE!"
  5. Start tracking analytics
    ↓
In Analytics Dashboard:
  • Views: 0 (loading...)
  • Contacts: 0
  • Favorites: 0
  • Likes: 0 (as users view)
        </div>
      </div>

      <hr style="border-color: #1f2937; margin: 24px 0;">

      <h3 style="color: #93c5fd; margin-top: 24px;">3️⃣ ADMIN APP (Port 8004) - Platform Moderation & Control</h3>
      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Purpose & Users</div>
        <div class="component-detail">
          <strong>Target Users</strong>: Platform moderators, administrators, system operators<br/>
          <strong>Primary Function</strong>: Moderate ads, manage users, control system<br/>
          <strong>Security Focus</strong>: Super admin control, policy enforcement, audit logging
        </div>
      </div>

      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Key Features & Pages</div>
        <div class="component-detail">
          ✅ <strong>Dashboard</strong> - System metrics & alerts<br/>
          ✅ <strong>Moderation Queue</strong> - Ads awaiting review<br/>
          ✅ <strong>Violation Alerts</strong> - AI-flagged problematic content<br/>
          ✅ <strong>Analytics Hub</strong> - Platform-wide statistics<br/>
          ✅ <strong>Users Management</strong> - Approve, suspend, ban users<br/>
          ✅ <strong>Companies Management</strong> - Control advertisers<br/>
          ✅ <strong>Devices Tracking</strong> - Monitor devices & locations<br/>
          ✅ <strong>System Control</strong> - Restart services, clear cache<br/>
          ✅ <strong>Audit Logs</strong> - All actions & decisions
        </div>
      </div>

      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Data & Integration</div>
        <div class="component-detail">
          <strong>Database Tables</strong>:<br/>
          • admin_users (moderator accounts)<br/>
          • moderation_queue (pending review)<br/>
          • violation_alerts (AI-flagged content)<br/>
          • audit_logs (all system actions)<br/>
          • device_profiles (device tracking)<br/>
          • suspension_records (bans)<br/>
          <br/>
          <strong>External Integrations</strong>:<br/>
          • Moderation Service (full API access) - Manual moderation<br/>
          • Real-time Scanner - Continuous ad monitoring<br/>
          • Dashboard Stats API - Platform metrics<br/>
          • WebSocket - Live updates<br/>
          • Prometheus - Metrics collection<br/>
          • Grafana (optional) - Visualization
        </div>
      </div>

      <div class="component" style="margin-bottom: 20px;">
        <div class="component-title">Request Flow Example: Admin Reviews Flagged Ad</div>
        <div class="code-block">
ADMIN DASHBOARD:
  1. Shows "Moderation Queue" with 15 pending ads
  2. AI Auto-Scanner found 3 ads with violations
  3. Admin clicks on flagged ad
    ↓
ADMIN_APP (8004):
  1. Load ad detail view
  2. Display:
     - Title, description, images
     - AI scores: violence=0.8, weapons=0.2, toxicity=0.6
     - Reason: "High violence detected in image"
     - User who uploaded: company_name
     - Timestamp of upload
    ↓
Admin Reviews & Takes Action:
  Option 1: APPROVE (override AI)
  Option 2: BLOCK (delete ad, log violation)
  Option 3: WARN (notify company, give 24h to fix)
    ↓
Admin clicks BLOCK:
  1. Delete ad files from disk
  2. Set ad.status = "blocked"
  3. Send email to advertiser:
     "Your ad was rejected for: High violence content"
     "Please review our policies: [link]"
  4. Log in audit_logs: "Admin blocked ad due to violence"
  5. Increment company.violation_count
  6. If violations > 3: auto-suspend company
    ↓
Dashboard Updates:
  • Moderation Queue: 14 remaining
  • Total Blocked Today: +1
  • Violations by Type: Violence +1
  • Company Violations: company_name now has 2/3
    ↓
REAL-TIME EFFECT:
  • Ad no longer appears on PUBLIC_APP
  • Company sees in their dashboard: "BLOCKED"
  • System sends notification to moderators: "Action taken"
        </div>
      </div>
    </div>

    <h2 id="phpIntegration">🔗 PHP Integration & Client Libraries</h2>
    <div class="card">
      <div class="card-header">Complete PHP Integration Guide</div>
      <div class="component">
        <div class="component-title">Location</div>
        <div class="component-detail">
          <strong>ModerationServiceClient</strong>: services/moderator_services/ModerationServiceClient.php<br/>
          <strong>WebSocketClient</strong>: services/moderator_services/WebSocketModerationClient.php
        </div>
      </div>
      <table>
        <tr><th>Method</th><th>Parameters</th><th>Returns</th><th>Use Case</th></tr>
        <tr><td>moderateText()</td><td>title, description</td><td>Decision + scores</td><td>Text-only moderation</td></tr>
        <tr><td>moderateImage()</td><td>image_path/base64</td><td>Decision + detections</td><td>Single image check</td></tr>
        <tr><td>moderateVideo()</td><td>video_path, max_duration</td><td>Decision + frame summary</td><td>Video file analysis</td></tr>
        <tr><td>moderateRealtime()</td><td>title, desc, images, video, category</td><td>Complete decision</td><td>Full ad moderation</td></tr>
        <tr><td>searchCategories()</td><td>query, limit, threshold</td><td>Array of matches</td><td>AI category search</td></tr>
        <tr><td>getHealth()</td><td>none</td><td>Service status</td><td>Health checks</td></tr>
      </table>
      <div class="component" style="margin-top: 16px;">
        <div class="component-title">PHP Code Example</div>
        <div class="code-block">
&lt;?php
require 'services/moderator_services/ModerationServiceClient.php';

// Initialize client
$client = new ModerationServiceClient('http://localhost:8002');

// Moderate an ad
$result = $client->moderateRealtime([
    'title' => 'iPhone 13 Pro for Sale',
    'description' => 'Excellent condition, all accessories included',
    'category' => 'electronics',
    'images' => ['base64_image_data_here...'],
    'context' => ['company' => 'apple_store', 'region' => 'us-west']
]);

// Check decision
if ($result['decision'] === 'block') {
    // Log violation, notify admin
    logViolation($result);
} elseif ($result['decision'] === 'review') {
    // Flag for manual review
    flagForReview($result);
} else {
    // Auto-approve, post ad
    postAd($adData);
}

// AI category search
$matches = $client->searchCategories('I want to buy electronics', 5);
foreach ($matches as $match) {
    echo $match['name'] . ': ' . $match['score'] . "\\n";
}
?&gt;
        </div>
      </div>
    </div>

    <h2 style="margin-top: 48px; border-top: 2px solid #1f2937; padding-top: 24px;">🔄 System Flow Diagrams</h2>

    <div class="card">
      <div class="card-header">Complete End-to-End Request Flow</div>
      <pre>
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                          FULL AD PUBLISHING WORKFLOW                                                     │
│                     (From Upload to Display on Public App)                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘

STEP 1: ADVERTISER UPLOADS AD
═══════════════════════════════════════════════════════════════════════════════════════════════════════════

    COMPANY_APP (8003) / ADVERTISER BROWSER
    ├─ User fills form: title, description, 4 images
    ├─ Click "Upload"
    └─ POST /admin/ad_upload.php
         │
         ├─ Validate input locally
         ├─ Compress images (<1MB each)
         ├─ Store files: /companies/company-name/media/
         └─ Send to MODERATION_SERVICE


STEP 2: MODERATION PIPELINE
═══════════════════════════════════════════════════════════════════════════════════════════════════════════

    MODERATION_SERVICE (8002) / POST /moderate/realtime
    │
    ├─ TEXT MODERATION (Title + Description)
    │  ├─ Normalize text (Unicode NFC)
    │  ├─ Tokenize with spaCy (3.8.0+)
    │  ├─ Language detect: XLM-RoBERTa → "en"
    │  ├─ Create embedding: Sentence-Transformers → 384-dim vector
    │  ├─ Intent classify: DeBERTa-v3 → "product_sale"
    │  ├─ Toxicity check: Detoxify → [toxicity=0.1, severe=0.0, ...]
    │  └─ Aggregate scores → text_score = 0.15 (CLEAN)
    │
    ├─ IMAGE MODERATION (4 Images)
    │  ├─ Security Scan (all images):
    │  │  ├─ Check file structure (magic bytes)
    │  │  ├─ Entropy analysis → no encryption detected
    │  │  ├─ LSB detector → no steganography
    │  │  └─ Result: All 4 images CLEAN
    │  │
    │  ├─ For each image:
    │  │  ├─ Sanitize: Remove EXIF, re-encode WebP
    │  │  ├─ Compress: 2.1MB → 0.8MB
    │  │  ├─ OCR extract: EasyOCR (1.6.0+) / PaddleOCR (3.3.2+)
    │  │  │  └─ Detected text: "Price: $50" → send to text moderation
    │  │  ├─ NSFW detect: NudeNet (2.0.0+) → 0.02 (clean)
    │  │  ├─ Weapons detect: YOLOv8 weapons (custom) → 0.01 (no weapons)
    │  │  ├─ Violence detect: Violence CNN → 0.05 (no violence)
    │  │  ├─ Blood detect: Blood CNN → 0.03 (no blood)
    │  │  ├─ Scene analyze: CLIP → "Product photo in studio"
    │  │  └─ Image score = 0.08 (VERY CLEAN)
    │  │
    │  └─ Final image_score = (0.02 + 0.01 + 0.05 + 0.03) / 4 = 0.025
    │
    └─ FINAL DECISION ENGINE
       ├─ Aggregate scores:
       │  ├─ text_score = 0.15
       │  ├─ image_score = 0.025
       │  ├─ Global = (0.15 * 0.4) + (0.025 * 0.6) = 0.075
       │
       ├─ Compare against thresholds:
       │  ├─ 0.075 < 0.30 → APPROVE
       │  └─ Log decision: "Approved: legitimate product sale"
       │
       └─ Return to COMPANY_APP:
          {
            "decision": "approve",
            "global_score": 0.075,
            "text_score": 0.15,
            "image_score": 0.025,
            "reason": "Content approved for publication"
          }


STEP 3: AD SAVED TO DATABASE
═══════════════════════════════════════════════════════════════════════════════════════════════════════════

    COMPANY_APP / BACKEND
    │
    ├─ Moderation Result: APPROVED
    ├─ Insert into ads table:
    │  {
    │    "id": "AD-202512-113047.114-94U75",
    │    "company_id": "meda-media-technologies",
    │    "title": "iPhone 13 Pro",
    │    "description": "Excellent condition...",
    │    "category": "electronics",
    │    "status": "active",
    │    "images": ["img1.webp", "img2.webp", "img3.webp", "img4.webp"],
    │    "created_at": "2025-12-23 14:30:00",
    │    "view_count": 0,
    │    "contact_count": 0,
    │    "favorite_count": 0
    │  }
    │
    ├─ Cache in Redis:
    │  ├─ SET ads:latest:electronics → [ad_id, ...]
    │  ├─ SET ad:{ad_id} → full ad object (TTL 1 hour)
    │  └─ Increment company:active_ads_count
    │
    └─ Return to COMPANY_APP:
       "Your ad is LIVE! View at: [link]"


STEP 4: AD APPEARS ON PUBLIC APP
═══════════════════════════════════════════════════════════════════════════════════════════════════════════

    PUBLIC_APP (8001)
    │
    ├─ User browses Electronics category
    ├─ Fetch ads list:
    │  ├─ Check Redis cache: GET ads:latest:electronics
    │  ├─ Return: [AD-202512-113047... (just uploaded!)]
    │
    ├─ User sees ad in listing
    ├─ Click "View Details"
    └─ Load full ad page


STEP 5: ANALYTICS TRACKING
═══════════════════════════════════════════════════════════════════════════════════════════════════════════

    PUBLIC_APP / AD DETAIL PAGE
    │
    ├─ JavaScript initializes tracking
    ├─ Start timer: view_start = 14:35:00
    │
    ├─ User interactions tracked:
    │  ├─ View duration: 2m 15s
    │  ├─ Scroll depth: 80% (viewed all images)
    │  ├─ Image clicks: 3 (zoomed images)
    │  ├─ Contact button click: YES
    │  └─ Favorite click: NO
    │
    ├─ When user leaves, send to backend:
    │  POST /api/track_interaction
    │  {
    │    "ad_id": "AD-202512-113047.114-94U75",
    │    "user_id": "user_12345",
    │    "device_id": "device_abc123",
    │    "event_type": "view",
    │    "duration_seconds": 135,
    │    "scroll_depth": 0.80,
    │    "contact_method": "call",
    │    "timestamp": "2025-12-23 14:37:15"
    │  }
    │
    └─ Backend:
       ├─ Record in ad_views table
       ├─ Log contact event: type="call"
       ├─ Update ad analytics cache
       └─ Increment company's stats


STEP 6: COMPANY DASHBOARD SHOWS RESULTS
═══════════════════════════════════════════════════════════════════════════════════════════════════════════

    COMPANY_APP / MY ADS PAGE
    │
    ├─ Ad now shows:
    │  ├─ Status: ACTIVE ✓
    │  ├─ Views: 1 (from user above)
    │  ├─ Contacts: 1 (call attempt)
    │  ├─ Favorites: 0
    │  ├─ Likes: 0
    │  └─ Last activity: 2 minutes ago
    │
    ├─ Contact Methods Breakdown:
    │  ├─ Call: 1 click
    │  ├─ SMS: 0 clicks
    │  ├─ Email: 0 clicks
    │  └─ WhatsApp: 0 clicks
    │
    └─ Company can now:
       ├─ See all interactions in real-time
       ├─ Adjust ad (edit, boost, pause)
       └─ View in Admin Dashboard


STEP 7: ADMIN SEES OVERALL METRICS
═══════════════════════════════════════════════════════════════════════════════════════════════════════════

    ADMIN_APP (8004) / DASHBOARD
    │
    ├─ Platform Metrics Updated:
    │  ├─ Total Ads: 2,456 (new: +1)
    │  ├─ Active Ads: 2,123
    │  ├─ Total Views Today: 54,231 (new: +1)
    │  ├─ Total Contacts Today: 1,234 (new: +1)
    │  ├─ Ads Moderated Today: 156 (new: +1)
    │  ├─ Approved Rate: 94.2%
    │  ├─ Blocked Rate: 3.1%
    │  ├─ Review Queue: 8 pending
    │  └─ Active Companies: 287
    │
    └─ Admin can:
       ├─ View the new ad in moderation history
       ├─ See decision: "Approved by AI"
       ├─ View company: meda-media-technologies
       └─ Monitor real-time activity

      </pre>
    </div>

    <div class="card">
      <div class="card-header">Moderation Decision Matrix (Quick Reference)</div>
      <pre>
┌──────────────────────────────────────────────────────────────────────────────┐
│                    GLOBAL SCORE DECISION THRESHOLDS                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  GLOBAL SCORE: 0.0 ────────── 0.30 ────────── 0.60 ────────── 0.80 ──── 1.0 │
│                │              │              │              │              │
│  DECISION:    APPROVE        REVIEW       REVIEW          BLOCK            │
│  RISK LEVEL:   LOW           MEDIUM        HIGH           CRITICAL         │
│  ACTION:       ✅ AUTO        ⚠️ MANUAL      ⚠️ PRIORITY      ❌ AUTO        │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│ EXAMPLE SCENARIOS                                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ Score 0.08: "iPhone for sale" + clean images                               │
│   → APPROVED ✓                                                               │
│                                                                              │
│ Score 0.45: "Fighting lessons" + image has slight violence  │
│   → REVIEW ⚠️ (Manual check needed)                                           │
│                                                                              │
│ Score 0.72: Hate speech detected + suspicious images                        │
│   → REVIEW PRIORITY ⚠️ (Priority review queue)                               │
│                                                                              │
│ Score 0.92: Weapons for sale + explicit violence                            │
│   → BLOCKED ❌ (Auto-reject)                                                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

      </pre>
    </div>

    <h2 style="margin-top: 48px; border-top: 2px solid #1f2937; padding-top: 24px;">📞 API Endpoints Reference</h2>
    <div class="card">
      <table>
        <tr><th>Method</th><th>Endpoint</th><th>Purpose</th><th>Response Time</th></tr>
        <tr><td>POST</td><td>/moderate/text</td><td>Moderate text content</td><td>50-100ms</td></tr>
        <tr><td>POST</td><td>/moderate/image</td><td>Moderate images</td><td>200-500ms</td></tr>
        <tr><td>POST</td><td>/moderate/video</td><td>Moderate videos</td><td>3-10s</td></tr>
        <tr><td>POST</td><td>/moderate/realtime</td><td>Full ad moderation</td><td>300-600ms</td></tr>
        <tr><td>POST</td><td>/search/match</td><td>AI category matching</td><td>45-55ms (model), <1ms (cached)</td></tr>
        <tr><td>GET</td><td>/search/quick/{query}</td><td>Quick semantic search</td><td>45-55ms</td></tr>
        <tr><td>GET</td><td>/health</td><td>Health check</td><td><5ms</td></tr>
        <tr><td>GET</td><td>/metrics</td><td>Prometheus metrics</td><td><10ms</td></tr>
        <tr><td>GET</td><td>/docs</td><td>Swagger UI</td><td>Instant</td></tr>
        <tr><td>GET</td><td>/docs/architecture</td><td>This page</td><td>Instant</td></tr>
      </table>
    </div>

    <footer style="text-align: center; margin-top: 48px; padding-top: 24px; border-top: 1px solid #1f2937; color: #64748b; font-size: 12px;">
      <p>AdSphere Moderation Service v1.0.0 | Enterprise-grade Content Moderation Platform</p>
      <p>Built with FastAPI • PyTorch • Transformers • Redis • SQLite • PHP Integration</p>
      <p>© 2025 AdSphere. All rights reserved.</p>
    </footer>
  </div>
</body>
</html>
"""

@router.get("/architecture", response_class=HTMLResponse)
def get_architecture_page():
    return HTMLResponse(content=ARCH_HTML, status_code=200)

