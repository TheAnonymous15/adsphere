<?php
/********************************************
 * Content Moderation Dashboard
 * Real-time ad scanning and moderation interface
 ********************************************/
session_start();

// Check admin access (implement proper authentication)
// For now, allowing access - add proper admin check later
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Content Moderation Dashboard - AdSphere</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        .glass-effect {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .scanning {
            animation: pulse 1.5s infinite;
        }

        .severity-critical {
            border-left: 4px solid #dc2626;
            background: rgba(220, 38, 38, 0.1);
        }

        .severity-high {
            border-left: 4px solid #ea580c;
            background: rgba(234, 88, 12, 0.1);
        }

        .severity-medium {
            border-left: 4px solid #f59e0b;
            background: rgba(245, 158, 11, 0.1);
        }

        .severity-low {
            border-left: 4px solid #eab308;
            background: rgba(234, 179, 8, 0.1);
        }
    </style>
</head>
<body class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen text-white p-6">

<div class="container mx-auto max-w-7xl">

    <!-- Header -->
    <div class="glass-effect rounded-2xl p-6 mb-6">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-4xl font-bold flex items-center gap-3">
                    <i class="fas fa-shield-alt text-purple-400"></i>
                    Content Moderation Dashboard
                </h1>
                <p class="text-gray-400 mt-2">Real-time AI-powered ad monitoring and moderation</p>
            </div>
            <button onclick="runScan()" id="scanBtn" class="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-xl font-bold transition flex items-center gap-2">
                <i class="fas fa-radar"></i>
                <span>Run Scan Now</span>
            </button>
        </div>
    </div>

    <!-- Statistics -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <div class="glass-effect rounded-xl p-4">
            <div class="flex items-center gap-3 mb-2">
                <i class="fas fa-database text-blue-400 text-2xl"></i>
                <span class="text-gray-400 text-sm">Total Scanned</span>
            </div>
            <p class="text-3xl font-bold" id="totalScanned">-</p>
        </div>

        <div class="glass-effect rounded-xl p-4">
            <div class="flex items-center gap-3 mb-2">
                <i class="fas fa-skull-crossbones text-red-500 text-2xl"></i>
                <span class="text-gray-400 text-sm">Critical</span>
            </div>
            <p class="text-3xl font-bold text-red-500" id="criticalCount">-</p>
        </div>

        <div class="glass-effect rounded-xl p-4">
            <div class="flex items-center gap-3 mb-2">
                <i class="fas fa-exclamation-triangle text-orange-500 text-2xl"></i>
                <span class="text-gray-400 text-sm">High Risk</span>
            </div>
            <p class="text-3xl font-bold text-orange-500" id="highCount">-</p>
        </div>

        <div class="glass-effect rounded-xl p-4">
            <div class="flex items-center gap-3 mb-2">
                <i class="fas fa-exclamation-circle text-yellow-500 text-2xl"></i>
                <span class="text-gray-400 text-sm">Medium Risk</span>
            </div>
            <p class="text-3xl font-bold text-yellow-500" id="mediumCount">-</p>
        </div>

        <div class="glass-effect rounded-xl p-4">
            <div class="flex items-center gap-3 mb-2">
                <i class="fas fa-check-circle text-green-500 text-2xl"></i>
                <span class="text-gray-400 text-sm">Clean</span>
            </div>
            <p class="text-3xl font-bold text-green-500" id="cleanCount">-</p>
        </div>
    </div>

    <!-- Filters -->
    <div class="glass-effect rounded-xl p-4 mb-6 flex gap-4 items-center">
        <span class="text-gray-400">Filter by Severity:</span>
        <button onclick="filterBySeverity('all')" class="filter-btn px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition active">All</button>
        <button onclick="filterBySeverity('critical')" class="filter-btn px-4 py-2 bg-red-600/20 hover:bg-red-600/30 rounded-lg transition">Critical</button>
        <button onclick="filterBySeverity('high')" class="filter-btn px-4 py-2 bg-orange-600/20 hover:bg-orange-600/30 rounded-lg transition">High</button>
        <button onclick="filterBySeverity('medium')" class="filter-btn px-4 py-2 bg-yellow-600/20 hover:bg-yellow-600/30 rounded-lg transition">Medium</button>
        <button onclick="filterBySeverity('low')" class="filter-btn px-4 py-2 bg-yellow-500/20 hover:bg-yellow-500/30 rounded-lg transition">Low</button>
    </div>

    <!-- Flagged Ads List -->
    <div class="glass-effect rounded-2xl p-6">
        <h2 class="text-2xl font-bold mb-4 flex items-center gap-2">
            <i class="fas fa-flag text-red-400"></i>
            Flagged Advertisements
        </h2>

        <div id="flaggedAds" class="space-y-4">
            <p class="text-gray-400 text-center py-12">Click "Run Scan Now" to check for policy violations</p>
        </div>
    </div>

</div>

<script>
let currentFilter = 'all';
let scanData = null;

// Load latest report on page load
window.addEventListener('DOMContentLoaded', loadLatestReport);

async function loadLatestReport() {
    try {
        const res = await fetch('/app/api/scanner.php?action=report');
        const data = await res.json();

        if (data.success && data.data && data.data.total_scanned) {
            scanData = data.data;
            displayResults(scanData);
        }
    } catch (error) {
        console.error('Failed to load report:', error);
    }
}

async function runScan() {
    const btn = document.getElementById('scanBtn');
    const originalContent = btn.innerHTML;

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Scanning...</span>';
    btn.classList.add('scanning');

    try {
        const res = await fetch('/app/api/scanner.php?action=scan');
        const data = await res.json();

        if (data.success) {
            scanData = data.data;
            displayResults(scanData);

            // Show success notification
            showNotification('Scan complete! Found ' + scanData.flagged_ads.length + ' flagged ads.', 'success');
        } else {
            showNotification('Scan failed: ' + data.error, 'error');
        }
    } catch (error) {
        console.error('Scan error:', error);
        showNotification('Scan failed: Network error', 'error');
    }

    btn.disabled = false;
    btn.innerHTML = originalContent;
    btn.classList.remove('scanning');
}

function displayResults(data) {
    // Update statistics
    document.getElementById('totalScanned').textContent = data.total_scanned;
    document.getElementById('criticalCount').textContent = data.statistics.critical;
    document.getElementById('highCount').textContent = data.statistics.high;
    document.getElementById('mediumCount').textContent = data.statistics.medium;
    document.getElementById('cleanCount').textContent = data.clean_ads;

    // Display flagged ads
    displayFlaggedAds(data.flagged_ads);
}

function displayFlaggedAds(flaggedAds) {
    const container = document.getElementById('flaggedAds');

    if (flaggedAds.length === 0) {
        container.innerHTML = '<p class="text-green-400 text-center py-12"><i class="fas fa-check-circle text-4xl mb-3"></i><br>No policy violations found! All ads are clean.</p>';
        return;
    }

    // Filter by severity
    const filtered = currentFilter === 'all'
        ? flaggedAds
        : flaggedAds.filter(ad => ad.severity_level === currentFilter);

    container.innerHTML = filtered.map(ad => `
        <div class="severity-${ad.severity_level} rounded-xl p-6 hover:bg-white/5 transition">
            <div class="flex justify-between items-start mb-4">
                <div class="flex-1">
                    <div class="flex items-center gap-3 mb-2">
                        <span class="px-3 py-1 bg-${getSeverityColor(ad.severity_level)}-600 rounded-full text-xs font-bold uppercase">
                            ${ad.severity_level}
                        </span>
                        <span class="text-sm text-gray-400">AI Score: ${ad.ai_score}/100</span>
                        <span class="text-sm text-gray-400">Risk: ${ad.risk_level}</span>
                    </div>
                    <h3 class="text-xl font-bold mb-1">${escapeHtml(ad.title)}</h3>
                    <p class="text-gray-400 text-sm mb-2">${escapeHtml(ad.description)}</p>
                    <div class="flex gap-4 text-sm text-gray-500">
                        <span><i class="fas fa-building mr-1"></i>${escapeHtml(ad.company)}</span>
                        <span><i class="fas fa-tag mr-1"></i>${escapeHtml(ad.category)}</span>
                        <span><i class="fas fa-clock mr-1"></i>${formatTime(ad.created_at)}</span>
                    </div>
                </div>
                <div class="text-right">
                    <span class="px-3 py-1 bg-purple-600/30 rounded-lg text-xs">
                        ${ad.recommendation.urgency.toUpperCase()}
                    </span>
                </div>
            </div>

            <!-- Violations -->
            <div class="bg-black/30 rounded-lg p-4 mb-4">
                <h4 class="font-bold mb-2 text-red-400"><i class="fas fa-exclamation-triangle mr-2"></i>Violations Detected:</h4>
                <div class="space-y-2 text-sm">
                    ${ad.violations.content_issues.map(issue => `
                        <div class="flex items-start gap-2">
                            <i class="fas fa-times-circle text-red-500 mt-1"></i>
                            <span>${escapeHtml(issue)}</span>
                        </div>
                    `).join('')}
                    ${ad.violations.pattern_flags.map(flag => `
                        <div class="flex items-start gap-2">
                            <i class="fas fa-flag text-orange-500 mt-1"></i>
                            <span>${escapeHtml(flag)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- AI Recommendation -->
            <div class="bg-purple-600/20 border border-purple-600/50 rounded-lg p-4 mb-4">
                <h4 class="font-bold mb-2 text-purple-400"><i class="fas fa-robot mr-2"></i>AI Recommendation:</h4>
                <div class="mb-3">
                    <span class="text-lg font-bold text-white">${getActionIcon(ad.recommendation.primary_action)} ${ad.recommendation.primary_action.toUpperCase()}</span>
                </div>
                <div class="space-y-1 text-sm">
                    ${ad.recommendation.reasoning.map(reason => `
                        <div class="flex items-start gap-2">
                            <i class="fas fa-angle-right text-purple-400 mt-1"></i>
                            <span>${escapeHtml(reason)}</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex gap-2 flex-wrap">
                <button onclick="takeAction('${ad.ad_id}', 'delete')" class="px-4 py-2 bg-red-600 hover:bg-red-700 rounded-lg transition text-sm">
                    <i class="fas fa-trash mr-2"></i>Delete Ad
                </button>
                <button onclick="takeAction('${ad.ad_id}', 'pause')" class="px-4 py-2 bg-yellow-600 hover:bg-yellow-700 rounded-lg transition text-sm">
                    <i class="fas fa-pause mr-2"></i>Pause Ad
                </button>
                <button onclick="takeAction('${ad.ad_id}', 'ban')" class="px-4 py-2 bg-gray-700 hover:bg-gray-800 rounded-lg transition text-sm">
                    <i class="fas fa-ban mr-2"></i>Ban Company
                </button>
                <button onclick="viewDetails('${ad.ad_id}')" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition text-sm">
                    <i class="fas fa-eye mr-2"></i>View Full Details
                </button>
            </div>
        </div>
    `).join('');
}

function filterBySeverity(severity) {
    currentFilter = severity;

    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    if (scanData) {
        displayFlaggedAds(scanData.flagged_ads);
    }
}

function getSeverityColor(severity) {
    switch(severity) {
        case 'critical': return 'red';
        case 'high': return 'orange';
        case 'medium': return 'yellow';
        case 'low': return 'yellow';
        default: return 'gray';
    }
}

function getActionIcon(action) {
    switch(action) {
        case 'ban': return '🚫';
        case 'delete': return '🗑️';
        case 'pause': return '⏸️';
        case 'warn': return '⚠️';
        case 'report': return '📢';
        default: return '❓';
    }
}

function formatTime(timestamp) {
    const date = new Date(timestamp * 1000);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);

    if (diff < 3600) return Math.floor(diff / 60) + ' mins ago';
    if (diff < 86400) return Math.floor(diff / 3600) + ' hours ago';
    return Math.floor(diff / 86400) + ' days ago';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function takeAction(adId, action) {
    if (!confirm(`Are you sure you want to ${action} this ad?`)) return;

    try {
        // Get violation ID from the ad
        const violationId = await getViolationIdForAd(adId);

        if (!violationId) {
            showNotification('Could not find violation for this ad', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('action', 'take_action');
        formData.append('violation_id', violationId);
        formData.append('action_type', action);
        formData.append('admin_user', 'Admin');
        formData.append('reason', 'Moderation dashboard action');

        const res = await fetch('/app/api/moderation_violations.php', {
            method: 'POST',
            body: formData
        });

        const data = await res.json();

        if (data.success) {
            let message = `Action ${action} executed successfully`;
            if (data.notification === 'sent') {
                message += ' ✉️ Owner notified';
            } else if (data.notification === 'failed') {
                message += ' ⚠️ Notification failed';
            }
            showNotification(message, 'success');

            // Reload the scan to refresh the list
            setTimeout(() => loadLatestReport(), 1000);
        } else {
            showNotification(`Action failed: ${data.error}`, 'error');
        }
    } catch (error) {
        console.error('Action error:', error);
        showNotification('Action failed: Network error', 'error');
    }
}

async function getViolationIdForAd(adId) {
    try {
        const res = await fetch('/app/api/moderation_violations.php?action=list&status=pending');
        const data = await res.json();

        if (data.success && data.violations) {
            const violation = data.violations.find(v => v.ad_id === adId);
            return violation ? violation.id : null;
        }
        return null;
    } catch (error) {
        console.error('Failed to get violation ID:', error);
        return null;
    }
}

function viewDetails(adId) {
    // Open ad details in modal or new page
    console.log('View details for ad:', adId);
}

function showNotification(message, type) {
    // Simple notification - enhance with better UI
    const color = type === 'success' ? 'green' : 'red';
    const div = document.createElement('div');
    div.className = `fixed top-4 right-4 px-6 py-4 bg-${color}-600 text-white rounded-lg shadow-xl z-50`;
    div.innerHTML = message;
    document.body.appendChild(div);

    setTimeout(() => div.remove(), 3000);
}

// Auto-refresh every 5 minutes
setInterval(loadLatestReport, 300000);
</script>

</body>
</html>

