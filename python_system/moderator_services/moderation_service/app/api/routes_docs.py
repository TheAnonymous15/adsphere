from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/docs", tags=["documentation"])

DETAILED_DOCS_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AdSphere – Complete Technical Documentation</title>
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
    h1 { font-size: 40px; margin: 0 0 8px; font-weight: 700; color: #60a5fa; }
    h2 { font-size: 24px; margin: 48px 0 20px; font-weight: 700; color: #93c5fd; border-bottom: 3px solid #3b82f6; padding-bottom: 12px; scroll-margin-top: 100px; }
    h3 { font-size: 16px; margin: 24px 0 12px; font-weight: 600; color: #60a5fa; }
    .header { margin-bottom: 48px; text-align: center; }
    .sub { color: #93c5fd; margin-bottom: 8px; font-size: 16px; }
    .desc { color: #cbd5e1; margin-bottom: 24px; font-size: 14px; max-width: 800px; }
    .card { background: rgba(15, 23, 42, 0.8); border: 1px solid #1f2937; border-radius: 12px; padding: 24px; margin-bottom: 24px; backdrop-filter: blur(10px); }
    .card-header { font-weight: 600; color: #60a5fa; margin-bottom: 16px; font-size: 14px; }
    table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 13px; }
    th { background: rgba(59, 130, 246, 0.2); color: #93c5fd; padding: 12px; text-align: left; border: 1px solid #3b82f6; font-weight: 600; }
    td { padding: 12px; border: 1px solid #1f2937; color: #cbd5e1; }
    tr:nth-child(even) { background: rgba(20, 30, 50, 0.3); }
    tr:hover { background: rgba(59, 130, 246, 0.1); }
    .section { margin: 32px 0; }
    .code-block { background: rgba(0, 0, 0, 0.6); padding: 16px; border-radius: 8px; font-family: monospace; font-size: 11px; color: #34d399; border-left: 4px solid #34d399; overflow-x: auto; white-space: pre-wrap; line-height: 1.5; }
    .nav-fixed { position: sticky; top: 0; background: rgba(11, 19, 38, 0.98); padding: 16px 0; z-index: 100; border-bottom: 2px solid #3b82f6; margin-bottom: 24px; }
    .nav-btn { display: inline-block; padding: 10px 18px; background: rgba(59, 130, 246, 0.2); border: 1px solid #3b82f6; border-radius: 6px; color: #60a5fa; text-decoration: none; font-size: 12px; margin-right: 8px; margin-bottom: 8px; transition: all 0.3s ease; }
    .nav-btn:hover { background: rgba(59, 130, 246, 0.4); box-shadow: 0 0 15px rgba(59, 130, 246, 0.3); }
    .badge { display: inline-block; background: rgba(59, 130, 246, 0.3); color: #60a5fa; padding: 4px 10px; border-radius: 999px; font-size: 10px; font-weight: 600; margin: 4px 4px 4px 0; }
    .info-box { background: rgba(59, 130, 246, 0.1); border-left: 4px solid #60a5fa; padding: 16px; border-radius: 6px; margin: 16px 0; }
    .warning-box { background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; padding: 16px; border-radius: 6px; margin: 16px 0; }
    .success-box { background: rgba(52, 211, 153, 0.1); border-left: 4px solid #34d399; padding: 16px; border-radius: 6px; margin: 16px 0; }
    .feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin: 16px 0; }
    .feature-card { background: rgba(20, 30, 50, 0.6); border: 1px solid #1f2937; padding: 16px; border-radius: 8px; }
    .feature-title { font-weight: 600; color: #60a5fa; margin-bottom: 8px; }
    footer { text-align: center; margin-top: 64px; padding-top: 24px; border-top: 2px solid #1f2937; color: #64748b; font-size: 12px; }
    a { color: #60a5fa; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <h1>📚 AdSphere Technical Documentation</h1>
      <div class="sub">Complete Guide to Moderation System, API, and Integration</div>
      <div class="desc">Enterprise-grade content moderation platform with AI/ML, distributed caching, security scanning, and intelligent decision-making</div>
    </div>

    <div class="nav-fixed">
      <a href="#quickstart" class="nav-btn">Quick Start</a>
      <a href="#system" class="nav-btn">System</a>
      <a href="#deployment" class="nav-btn">Deployment</a>
      <a href="#php" class="nav-btn">PHP Integration</a>
      <a href="#models" class="nav-btn">ML Models</a>
      <a href="#search" class="nav-btn">AI Search</a>
      <a href="#api" class="nav-btn">API</a>
      <a href="#troubleshooting" class="nav-btn">Troubleshooting</a>
    </div>

    <h2 id="quickstart">🚀 Quick Start</h2>
    <div class="card">
      <h3>Installation & Setup</h3>
      <div class="code-block">
# Navigate to moderation service
cd python_system/moderator_services/moderation_service

# Install dependencies
pip install -r requirements.txt

# Start the service
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload

# Service will be available at:
# - Swagger UI: http://localhost:8002/docs
# - Architecture: http://localhost:8002/docs/architecture
# - ReDoc: http://localhost:8002/redoc
      </div>
    </div>

    <h2 id="system">🏗️ System Overview</h2>
    <div class="card">
      <h3>Core Components</h3>
      <table>
        <tr><th>Component</th><th>Technology</th><th>Purpose</th><th>Port</th></tr>
        <tr><td>Moderation Service</td><td>FastAPI 0.100+</td><td>Core moderation logic</td><td>8002</td></tr>
        <tr><td>Caching Layer</td><td>Redis 5.0+ / SQLite 3.37+</td><td>L2/L3 caching</td><td>6379</td></tr>
        <tr><td>Public App</td><td>PHP 8.4+</td><td>Customer-facing browse</td><td>8001</td></tr>
        <tr><td>Company Portal</td><td>PHP 8.4+</td><td>Advertiser management</td><td>8003</td></tr>
        <tr><td>Admin Panel</td><td>PHP 8.4+</td><td>System administration</td><td>8004</td></tr>
      </table>
    </div>

    <h2 id="deployment">🐳 Deployment</h2>
    <div class="card">
      <h3>Docker Deployment (Production)</h3>
      <div class="code-block">
# Navigate to service
cd moderation_service

# Build Docker image
docker build -t adsphere-moderation:latest .

# Run with Docker Compose (single instance)
docker-compose up -d

# Scale to multiple instances
docker-compose -f docker-compose.prod.yml up -d --scale moderation=4

# Check status
docker-compose ps

# View logs
docker-compose logs -f moderation

# Stop all services
docker-compose down
      </div>
      <div class="info-box">
        <strong>✅ Horizontal Scaling:</strong> Deploy multiple instances behind nginx/HAProxy load balancer for high availability
      </div>
    </div>

    <h2 id="php">🔗 PHP Integration</h2>
    <div class="card">
      <h3>Client Library Usage</h3>
      <div class="code-block">
&lt;?php
require 'services/moderator_services/ModerationServiceClient.php';

// Initialize
$client = new ModerationServiceClient('http://localhost:8002');

// Check health
$health = $client->getHealth();
if ($health['status'] === 'healthy') {
    echo "Service is ready\\n";
}

// Moderate an ad
$result = $client->moderateRealtime([
    'title' => 'iPhone 13 Pro for Sale',
    'description' => 'Excellent condition, all accessories included',
    'category' => 'electronics',
    'images' => ['base64_image_data'],
    'context' => ['company' => 'tech_store', 'region' => 'us']
]);

// Check result
if ($result['decision'] === 'block') {
    logViolation($result);
    sendAdminNotification($result);
} elseif ($result['decision'] === 'review') {
    flagForManualReview($result);
} else {
    publishAd($adData);
    trackAnalytics('ad_approved');
}
?&gt;
      </div>
    </div>

    <h2 id="models">🧠 ML Models & Specifications</h2>
    <div class="card">
      <h3>Complete Model List with Versions</h3>
      <table>
        <tr>
          <th>Model Name</th>
          <th>Version</th>
          <th>Framework</th>
          <th>Purpose</th>
          <th>Languages</th>
          <th>Performance</th>
        </tr>
        <tr><td>XLM-RoBERTa</td><td>facebook/xlm-roberta-base</td><td>Transformers</td><td>Language detection</td><td>53</td><td>99%+ accuracy</td></tr>
        <tr><td>Sentence-Transformers</td><td>paraphrase-multilingual-MiniLM-L12-v2</td><td>PyTorch</td><td>Semantic embeddings</td><td>50+</td><td>384-dim vectors</td></tr>
        <tr><td>DeBERTa-v3</td><td>microsoft/deberta-v3-base</td><td>Transformers</td><td>Intent classification</td><td>Multi</td><td>95%+ accuracy</td></tr>
        <tr><td>Detoxify</td><td>0.5.0</td><td>PyTorch</td><td>6-category toxicity</td><td>Multi</td><td>92%+ accuracy</td></tr>
        <tr><td>NudeNet</td><td>2.0.0</td><td>PyTorch</td><td>NSFW detection</td><td>N/A</td><td>95%+ accuracy</td></tr>
        <tr><td>YOLOv8</td><td>8.0.0 (fine-tuned)</td><td>PyTorch</td><td>Object/weapon detection</td><td>N/A</td><td>90%+ accuracy</td></tr>
        <tr><td>Whisper</td><td>openai/whisper-base</td><td>PyTorch</td><td>Speech-to-text</td><td>99</td><td>85%+ WER</td></tr>
        <tr><td>PaddleOCR</td><td>3.3.2</td><td>PaddlePaddle</td><td>Text extraction</td><td>Multi</td><td>98%+ accuracy</td></tr>
        <tr><td>CLIP</td><td>openai/clip-vit-base-patch32</td><td>PyTorch</td><td>Image understanding</td><td>Multi</td><td>Vision-text aligned</td></tr>
        <tr><td>FAISS</td><td>1.7.0</td><td>Meta</td><td>Vector similarity</td><td>N/A</td><td><1ms per query</td></tr>
      </table>
    </div>

    <h2 id="search">🔍 AI-Assisted Search</h2>
    <div class="card">
      <h3>Semantic Category Matching</h3>
      <div class="info-box">
        <strong>How It Works:</strong><br/>
        1. User enters query → Encoded to 384-dim vector<br/>
        2. Compared against category embeddings → Cosine similarity<br/>
        3. Filtered by threshold (default 0.25) → Ranked by score<br/>
        4. Results cached in L1/L2/L3 for future queries<br/>
        5. 50+ languages supported automatically
      </div>
      <table>
        <tr><th>Query</th><th>Top Match</th><th>Score</th><th>Alternative 1</th><th>Alternative 2</th></tr>
        <tr><td>"I'm hungry"</td><td>Food (0.95)</td><td>95%</td><td>Restaurants (0.87)</td><td>Groceries (0.78)</td></tr>
        <tr><td>"Buy phone"</td><td>Electronics (0.93)</td><td>93%</td><td>Phones (0.91)</td><td>Gadgets (0.82)</td></tr>
        <tr><td>"Rent apartment"</td><td>Housing (0.91)</td><td>91%</td><td>Property (0.89)</td><td>Furnished (0.75)</td></tr>
        <tr><td>"Chakula" (Swahili)</td><td>Food (0.88)</td><td>88%</td><td>Restaurants (0.81)</td><td>Groceries (0.73)</td></tr>
      </table>
    </div>

    <h2 id="api">📡 API Reference</h2>
    <div class="card">
      <h3>All Endpoints</h3>
      <table>
        <tr><th>Method</th><th>Endpoint</th><th>Purpose</th><th>Latency</th><th>Rate Limit</th></tr>
        <tr><td>POST</td><td>/moderate/text</td><td>Text content analysis</td><td>50-100ms</td><td>1000/min</td></tr>
        <tr><td>POST</td><td>/moderate/image</td><td>Image content analysis</td><td>200-500ms</td><td>100/min</td></tr>
        <tr><td>POST</td><td>/moderate/video</td><td>Video content analysis</td><td>3-10s</td><td>10/min</td></tr>
        <tr><td>POST</td><td>/moderate/realtime</td><td>Full ad moderation</td><td>300-600ms</td><td>500/min</td></tr>
        <tr><td>POST</td><td>/search/match</td><td>AI category matching</td><td>45-55ms (first), <1ms (cached)</td><td>2000/min</td></tr>
        <tr><td>GET</td><td>/search/quick/{query}</td><td>Quick search</td><td>45-55ms</td><td>2000/min</td></tr>
        <tr><td>GET</td><td>/health</td><td>Service health</td><td><5ms</td><td>Unlimited</td></tr>
        <tr><td>GET</td><td>/metrics</td><td>Prometheus metrics</td><td><10ms</td><td>Unlimited</td></tr>
        <tr><td>GET</td><td>/docs</td><td>Swagger UI</td><td>Instant</td><td>Unlimited</td></tr>
      </table>
    </div>

    <h2 id="troubleshooting">🔧 Troubleshooting</h2>
    <div class="card">
      <h3>Common Issues & Solutions</h3>
      <table>
        <tr><th>Issue</th><th>Cause</th><th>Solution</th></tr>
        <tr><td>Service won't start</td><td>Port already in use</td><td>Kill process on port 8002: lsof -ti:8002 | xargs kill -9</td></tr>
        <tr><td>Model not loading</td><td>Missing dependencies</td><td>Run: pip install -r requirements.txt</td></tr>
        <tr><td>Redis connection failed</td><td>Redis not running</td><td>Start Redis: redis-server</td></tr>
        <tr><td>Out of memory</td><td>Model inference heavy</td><td>Enable GPU acceleration or scale horizontally</td></tr>
        <tr><td>Slow responses</td><td>No caching</td><td>Check Redis is running, verify L1/L2/L3 tiers</td></tr>
      </table>
    </div>

    <footer>
      <p>AdSphere Technical Documentation | v1.0.0 | Updated: December 23, 2025</p>
      <p>For API details, visit: <a href="http://localhost:8002/docs" target="_blank">http://localhost:8002/docs</a></p>
      <p>For architecture, visit: <a href="http://localhost:8002/docs/architecture" target="_blank">http://localhost:8002/docs/architecture</a></p>
      <p>© 2025 AdSphere. All rights reserved.</p>
    </footer>
  </div>
</body>
</html>
"""

@router.get("/detailed", response_class=HTMLResponse)
def get_detailed_docs():
    return HTMLResponse(content=DETAILED_DOCS_HTML, status_code=200)

