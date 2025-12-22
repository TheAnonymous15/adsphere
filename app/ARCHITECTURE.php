<?php
/**
 * ============================================================================
 * ADSPHERE SYSTEM ARCHITECTURE
 * ============================================================================
 *
 * The AdSphere platform is divided into THREE distinct areas:
 *
 * 1. PLATFORM ADMIN (Super Admins)
 *    Path: /app/admin/
 *    Who: Platform owners, system administrators
 *    Access: Highest level - can manage everything
 *    Features:
 *      - Manage all companies
 *      - Manage all ads across platform
 *      - System configuration
 *      - View all analytics
 *      - Content moderation controls
 *      - Admin user management
 *      - Security settings (2FA enforced)
 *
 * 2. COMPANY DASHBOARD (Business Customers)
 *    Path: /app/companies/
 *    Who: Businesses who advertise on the platform
 *    Access: Can only manage their own ads
 *    Features:
 *      - Upload/edit their ads
 *      - View their analytics
 *      - Manage their profile
 *      - Contact information
 *
 * 3. PUBLIC FRONTEND (End Users)
 *    Path: / (root - index.php, ad_page.php, home.php)
 *    Who: General public browsing ads
 *    Access: Read-only, can contact advertisers
 *    Features:
 *      - Browse ads
 *      - Search/filter
 *      - Contact dealers
 *      - Save favorites
 *
 * ============================================================================
 * DIRECTORY STRUCTURE
 * ============================================================================
 *
 * /app/
 * ├── admin/                   <-- PLATFORM ADMIN (Super Admins)
 * │   ├── login.php            <-- Admin login (2FA enforced)
 * │   ├── logout.php           <-- Admin logout
 * │   ├── admin_dashboard.php  <-- Main admin dashboard
 * │   ├── moderation_dashboard.php <-- Content moderation
 * │   ├── categories.php       <-- Manage categories
 * │   ├── company_register.php <-- Register new companies
 * │   ├── handlers/            <-- Backend handlers
 * │   │   ├── setup_2fa.php    <-- 2FA setup
 * │   │   ├── verify_2fa.php   <-- 2FA verification
 * │   │   ├── twoauth.php      <-- 2FA authentication
 * │   │   └── diagnostic.php   <-- System diagnostics
 * │   └── logger/              <-- Admin activity logs
 * │
 * ├── companies/               <-- COMPANY PORTAL (Advertisers)
 * │   ├── handlers/
 * │   │   └── login.php        <-- Company login
 * │   ├── home/
 * │   │   ├── dashboard.php    <-- Company dashboard
 * │   │   ├── upload_ad.php    <-- Upload ads
 * │   │   ├── my_ads.php       <-- View their ads
 * │   │   ├── edit_ad.php      <-- Edit ads
 * │   │   └── profile.php      <-- Company profile
 * │   ├── analytics/           <-- Company analytics
 * │   ├── data/                <-- Company data
 * │   └── metadata/            <-- Company metadata
 * │
 * ├── api/                     <-- SHARED API ENDPOINTS
 * │   ├── get_ads.php          <-- Get ads
 * │   ├── get_analytics.php    <-- Get analytics
 * │   ├── get_categories.php   <-- Get categories
 * │   ├── get_companies.php    <-- Get companies
 * │   └── admin_stats.php      <-- Admin statistics
 * │
 * ├── database/                <-- DATABASE LAYER
 * │   ├── Database.php         <-- Database class
 * │   └── adsphere.db          <-- SQLite database
 * │
 * ├── moderator_services/      <-- AI/ML MODERATION SERVICE
 * │   ├── ModerationServiceClient.php
 * │   ├── WebSocketModerationClient.php
 * │   ├── moderation_service/  <-- Python FastAPI service
 * │   └── docker-compose.prod.yml
 * │
 * └── (root files)
 *     ├── index.php            <-- Public homepage
 *     ├── ad_page.php          <-- Browse ads
 *     └── home.php             <-- Alternative home
 *
 * ============================================================================
 * ACCESS CONTROL - SESSION VARIABLES
 * ============================================================================
 *
 * PLATFORM ADMIN (app/admin/):
 *   $_SESSION['admin_logged_in'] = true
 *   $_SESSION['admin_username'] = 'admin'
 *   $_SESSION['admin_role'] = 'super_admin'
 *   $_SESSION['admin_2fa_verified'] = true   <-- REQUIRED for admin
 *
 * COMPANY USER (app/companies/):
 *   $_SESSION['company'] = 'company-slug'
 *   $_SESSION['company_name'] = 'Company Name'
 *   $_SESSION['company_logged_in'] = true
 *   (2FA optional for companies)
 *
 * ============================================================================
 * URL ROUTING
 * ============================================================================
 *
 * Platform Admin:
 *   /app/admin/login.php          → Admin login
 *   /app/admin/admin_dashboard.php → Admin dashboard
 *   /app/admin/moderation_dashboard.php → Moderation
 *
 * Company Portal:
 *   /app/companies/handlers/login.php → Company login
 *   /app/companies/home/dashboard.php → Company dashboard
 *   /app/companies/home/upload_ad.php → Upload ads
 *
 * Public:
 *   /                             → Homepage
 *   /ad_page.php                  → Browse ads
 *
 * ============================================================================
 * SECURITY LEVELS
 * ============================================================================
 *
 * Level 1 - Public (No auth required):
 *   - Browse ads
 *   - View ad details
 *   - Contact dealers
 *
 * Level 2 - Company (Company login required):
 *   - Upload/edit own ads
 *   - View own analytics
 *   - Manage profile
 *
 * Level 3 - Admin (Admin login + 2FA required):
 *   - Full platform access
 *   - Content moderation
 *   - User management
 *   - System settings
 *
 * ============================================================================
 */

// This is a documentation file - no executable code

