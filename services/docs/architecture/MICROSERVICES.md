# AdSphere Microservices Architecture

## Overview

AdSphere is now a **microservices-based** platform with 3 separate services running on different ports:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ADSPHERE MICROSERVICES                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐    │
│  │   PUBLIC SERVICE   │  │   ADMIN SERVICE    │  │  COMPANY SERVICE   │    │
│  │   Port: 8001       │  │   Port: 8002       │  │   Port: 8003       │    │
│  │                    │  │                    │  │                    │    │
│  │  📢 Browse Ads     │  │  🔴 Platform Admin │  │  🔵 Company Portal │    │
│  │  🔓 No Auth        │  │  🔐 2FA Required   │  │  🔐 Login Required │    │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    MODERATION SERVICE (Port: 8004)                   │   │
│  │                    🤖 AI/ML Content Moderation                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    SHARED SERVICES                                   │   │
│  │    📦 Database    📦 Redis Cache    📦 File Storage                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Services

### 1. Public Service (Port 8001)
**URL:** `http://localhost:8001`

**Purpose:** Public-facing website for browsing ads

**Authentication:** None required

**Features:**
- Browse all active ads
- Search and filter
- View ad details
- Contact dealers (SMS, Call, Email, WhatsApp)
- Save favorites (localStorage)

**Routes:**
| Route | Description |
|-------|-------------|
| `/` | Homepage |
| `/ads` | Browse all ads |
| `/ad/{id}` | View single ad |
| `/search?q=...` | Search ads |
| `/categories` | List categories |
| `/category/{name}` | Ads by category |
| `/health` | Health check |

---

### 2. Admin Service (Port 8002)
**URL:** `http://localhost:8002`

**Purpose:** Platform administration for super admins

**Authentication:** Username/Password + **2FA Required**

**Features:**
- Manage ALL companies
- Manage ALL ads
- Content moderation
- Ad scanner controls
- System settings
- Admin user management
- View platform-wide analytics

**Routes:**
| Route | Description |
|-------|-------------|
| `/login` | Admin login |
| `/2fa` | 2FA verification |
| `/dashboard` | Main dashboard |
| `/companies` | Manage companies |
| `/ads` | Manage all ads |
| `/moderation` | Content moderation |
| `/flagged` | Flagged content |
| `/scanner` | Ad scanner |
| `/categories` | Manage categories |
| `/analytics` | Platform analytics |
| `/users` | Admin users |
| `/settings` | System settings |
| `/logs` | System logs |
| `/logout` | Logout |
| `/health` | Health check |

---

### 3. Company Service (Port 8003)
**URL:** `http://localhost:8003`

**Purpose:** Company portal for advertisers

**Authentication:** Company ID/Password

**Features:**
- Upload/edit THEIR OWN ads only
- View THEIR OWN analytics
- Manage company profile
- View notifications

**Routes:**
| Route | Description |
|-------|-------------|
| `/login` | Company login |
| `/register` | New company registration |
| `/forgot-password` | Password recovery |
| `/dashboard` | Company dashboard |
| `/ads` | My ads |
| `/upload` | Upload new ad |
| `/edit/{id}` | Edit ad |
| `/analytics` | My analytics |
| `/profile` | Company profile |
| `/settings` | Account settings |
| `/notifications` | Notifications |
| `/logout` | Logout |
| `/health` | Health check |

---

### 4. Moderation Service (Port 8004)
**URL:** `http://localhost:8004`

**Purpose:** AI/ML content moderation

**Authentication:** API Key (internal)

**Features:**
- Text moderation
- Image moderation (security scan, OCR, content analysis)
- Video moderation
- Real-time ad scanner

**Endpoints:** See `/docs` for full API documentation

---

## Directory Structure

```
adsphere/
├── services/                    # MICROSERVICES
│   ├── public/                  # Port 8001
│   │   ├── index.php           # Router
│   │   ├── pages/              # Page files
│   │   └── assets/             # CSS, JS
│   │
│   ├── admin/                   # Port 8002
│   │   ├── index.php           # Router
│   │   ├── pages/              # Page files
│   │   ├── api/                # Admin API
│   │   └── assets/             # CSS, JS
│   │
│   ├── company/                 # Port 8003
│   │   ├── index.php           # Router
│   │   ├── pages/              # Page files
│   │   ├── api/                # Company API
│   │   └── assets/             # CSS, JS
│   │
│   └── shared/                  # Shared code
│       ├── bootstrap.php       # Common setup
│       └── functions.php       # Utility functions
│
├── app/                         # LEGACY & SHARED
│   ├── api/                    # Shared API endpoints
│   ├── database/               # Database layer
│   ├── admin/                  # Legacy admin (reference)
│   ├── companies/              # Legacy company (reference)
│   └── moderator_services/     # AI/ML service
│
├── start_services.sh           # Startup script
├── docker-compose.services.yml # Docker setup
└── README.md
```

---

## Quick Start

### Option 1: Direct PHP (Development)

```bash
# Start all services
./start_services.sh

# Start individual service
./start_services.sh public
./start_services.sh admin
./start_services.sh company

# Check status
./start_services.sh status

# Stop all
./start_services.sh stop

# View logs
./start_services.sh logs public
```

### Option 2: Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.services.yml up -d

# Check status
docker-compose -f docker-compose.services.yml ps

# Stop all
docker-compose -f docker-compose.services.yml down
```

---

## Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Public** | http://localhost:8001 | Browse ads |
| **Admin** | http://localhost:8002 | Platform admin |
| **Company** | http://localhost:8003 | Company portal |
| **Moderation** | http://localhost:8004 | AI/ML API |
| **API Docs** | http://localhost:8004/docs | Moderation API docs |

---

## Session Management

Each service manages its own session:

### Public Service
- No session required for browsing
- Favorites stored in localStorage

### Admin Service
```php
$_SESSION['admin_logged_in'] = true;
$_SESSION['admin_username'] = 'admin';
$_SESSION['admin_role'] = 'super_admin';
$_SESSION['admin_2fa_verified'] = true;  // REQUIRED
$_SESSION['admin_last_activity'] = time();
```

### Company Service
```php
$_SESSION['company'] = 'company-slug';
$_SESSION['company_name'] = 'Company Name';
$_SESSION['company_logged_in'] = true;
$_SESSION['company_last_activity'] = time();
```

---

## Security

| Service | Auth Level | 2FA | Session Timeout | Rate Limit |
|---------|------------|-----|-----------------|------------|
| Public | None | N/A | N/A | 100 req/min |
| Admin | High | **Required** | 1 hour | 60 req/min |
| Company | Medium | Optional | 2 hours | 100 req/min |
| Moderation | API Key | N/A | N/A | 1000 req/min |

---

## Inter-Service Communication

Services communicate via:

1. **Shared Database** (SQLite) - `/app/database/adsphere.db`
2. **Redis** - Caching and message queue
3. **REST API** - Internal API calls
4. **WebSocket** - Real-time updates (moderation)

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Public  │     │  Admin  │     │ Company │
└────┬────┘     └────┬────┘     └────┬────┘
     │               │               │
     └───────────────┼───────────────┘
                     │
              ┌──────┴──────┐
              │   Shared    │
              │  Database   │
              │  + Redis    │
              └──────┬──────┘
                     │
              ┌──────┴──────┐
              │ Moderation  │
              │   Service   │
              └─────────────┘
```

