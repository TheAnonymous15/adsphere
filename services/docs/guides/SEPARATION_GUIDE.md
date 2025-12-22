# AdSphere System Separation Guide

## Overview

The AdSphere platform has THREE distinct user areas:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ADSPHERE PLATFORM                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐    │
│  │  PLATFORM ADMIN    │  │  COMPANY PORTAL    │  │  PUBLIC FRONTEND   │    │
│  │  /app/admin/       │  │  /app/companies/   │  │  / (root)          │    │
│  │                    │  │                    │  │                    │    │
│  │  👤 Super Admins   │  │  👤 Advertisers    │  │  👤 General Public │    │
│  │  🔐 2FA Required   │  │  🔐 Login Required │  │  🔓 No Auth        │    │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 1. Platform Admin (`/app/admin/`)

**Who**: Platform owners, system administrators

**Access URL**: `http://localhost/app/admin/login.php`

**Authentication**:
```php
// Session variables for admin
$_SESSION['admin_logged_in'] = true;
$_SESSION['admin_username'] = 'admin';
$_SESSION['admin_role'] = 'super_admin';
$_SESSION['admin_2fa_verified'] = true;  // REQUIRED
```

**Features**:
- ✅ Manage ALL companies
- ✅ Manage ALL ads
- ✅ Content moderation
- ✅ System settings
- ✅ View platform-wide analytics
- ✅ Ad scanner controls
- ✅ Category management

**Files**:
```
/app/admin/
├── login.php               # Admin login (with 2FA)
├── logout.php              # Admin logout
├── admin_dashboard.php     # Main dashboard
├── moderation_dashboard.php # Content moderation
├── categories.php          # Manage categories
├── company_register.php    # Register companies
├── handlers/
│   ├── setup_2fa.php      # 2FA setup
│   ├── verify_2fa.php     # 2FA verification
│   └── twoauth.php        # 2FA authentication
└── logger/                 # Activity logs
```

---

## 2. Company Portal (`/app/companies/`)

**Who**: Businesses who advertise on the platform

**Access URL**: `http://localhost/app/companies/handlers/login.php`

**Authentication**:
```php
// Session variables for company
$_SESSION['company'] = 'company-slug';
$_SESSION['company_name'] = 'Company Name';
$_SESSION['company_logged_in'] = true;
```

**Features**:
- ✅ Upload/edit THEIR OWN ads only
- ✅ View THEIR OWN analytics
- ✅ Manage company profile
- ❌ Cannot see other companies' data
- ❌ Cannot access admin features

**Files**:
```
/app/companies/
├── handlers/
│   └── login.php          # Company login
├── home/
│   ├── dashboard.php      # Company dashboard
│   ├── upload_ad.php      # Upload ads
│   ├── my_ads.php         # View their ads
│   ├── edit_ad.php        # Edit ads
│   └── profile.php        # Company profile
├── analytics/             # Company analytics
├── data/                  # Company data
└── metadata/              # Company metadata
```

---

## 3. Public Frontend (`/` root)

**Who**: General public browsing ads

**Access URL**: `http://localhost/` or `http://localhost/ad_page.php`

**Authentication**: None required

**Features**:
- ✅ Browse all active ads
- ✅ Search and filter
- ✅ Contact dealers (SMS, Call, Email, WhatsApp)
- ✅ Save favorites (localStorage)
- ❌ Cannot upload ads
- ❌ Cannot see analytics

**Files**:
```
/ (root)
├── index.php              # Homepage
├── ad_page.php            # Browse ads
└── home.php               # Alternative home
```

---

## Authentication Flow

### Admin Login Flow
```
1. Visit /app/admin/login.php
2. Enter username/password
3. If valid → Redirect to 2FA setup/verification
4. Enter 2FA code from authenticator app
5. If valid → Access admin_dashboard.php
```

### Company Login Flow
```
1. Visit /app/companies/handlers/login.php
2. Enter company credentials
3. If valid → Access dashboard.php
```

### Public Access
```
1. Visit / or /ad_page.php
2. Browse ads freely
3. Click "Contact Dealer" to interact
```

---

## Security Notes

| Area | Auth Level | 2FA | Session Timeout |
|------|------------|-----|-----------------|
| Admin | Required | **Required** | 1 hour |
| Company | Required | Optional | 2 hours |
| Public | None | N/A | N/A |

---

## Quick Links

- **Admin Dashboard**: `/app/admin/admin_dashboard.php`
- **Company Dashboard**: `/app/companies/home/dashboard.php`
- **Public Homepage**: `/index.php` or `/ad_page.php`
- **Admin Login**: `/app/admin/login.php`
- **Company Login**: `/app/companies/handlers/login.php`

