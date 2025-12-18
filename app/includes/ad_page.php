<section id="ads-feed" class="w-full text-white mt-20">

        <!-- FILTERS -->
        <div class="sticky top-0 bg-black/30 backdrop-blur-xl shadow py-4 z-50">
            <div class="max-w-7xl mx-auto flex justify-between items-center px-3 gap-3">

                <input id="search"
                    class="text-black px-3 py-2 rounded w-44 sm:w-56 md:w-80"
                    placeholder="Search ads">

                <select id="categoryFilter"
                    class="text-black rounded px-3 py-2">
                    <option value="">All</option>
                </select>

                <select id="sortFilter"
                    class="text-black rounded px-3 py-2">
                    <option value="date">Latest</option>
                    <option value="views">Most Viewed</option>
                    <option value="favs">Favorites</option>
                </select>

                <button id="btnSearch"
                    class="px-4 py-2 rounded bg-indigo-600 hover:bg-indigo-700 font-semibold">
                    Go
                </button>

            </div>
        </div>

        <h2 class="text-3xl font-bold mt-10 mb-4 px-4">
            Latest Ads
        </h2>

        <p id="no-results" class="hidden text-center text-gray-300 py-12 text-lg">
            No ads found.
        </p>

        <!-- cards -->
        <div id="ads-grid"
            class="columns-1 sm:columns-2 md:columns-3 lg:columns-4 gap-4 space-y-4 px-3">
        </div>

        <!-- loading -->
        <div id="loading" class="hidden py-10 space-y-4">
            <div class="animate-pulse flex flex-col gap-4">
                <div class="rounded-xl bg-white/10 h-60"></div>
                <div class="rounded bg-white/10 h-4 w-3/4"></div>
                <div class="rounded bg-white/10 h-4 w-1/2"></div>
            </div>
        </div>
    </section>

<!-- ===================== CONTACT MODAL ===================== -->
<div id="contactDealerModal"
     class="fixed inset-0 bg-black/50 backdrop-blur-sm hidden z-50">

  <div id="contactDealerCard"
    class="w-11/12 max-w-lg rounded-2xl bg-slate-900 p-8 shadow-xl transform scale-95 opacity-0 transition-all duration-300">

    <!-- HEADER -->
    <div class="mb-5 flex items-center justify-between">
      <h3 class="text-lg font-bold text-white">Contact Seller</h3>
      <button id="closeDealerModalBtn" class="text-white text-xl hover:text-gray-300">&times;</button>
    </div>

    <!-- YOUR INFO -->
    <div class="mb-4 space-y-3">
      <input id="senderName" type="text" placeholder="Your Name" maxlength="50"
        class="w-full rounded-xl border border-gray-700 bg-slate-800 p-3 text-white placeholder-white/70
               focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm">

      <input id="senderContact" type="text" placeholder="Your Phone/Email" maxlength="50"
        class="w-full rounded-xl border border-gray-700 bg-slate-800 p-3 text-white placeholder-white/70
               focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm">
    </div>

    <!-- MESSAGE -->
    <textarea id="contactDealerMessage" rows="8" placeholder="Type your message..." maxlength="500"
      class="mb-2 w-full rounded-xl border border-gray-700 bg-slate-800 p-3 text-white placeholder-white/70
             focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none text-sm"></textarea>
    <div class="text-xs text-gray-400 text-right mb-4">
      <span id="charCount">0</span>/500 characters
    </div>

    <!-- ACTION BUTTONS -->
    <div class="grid grid-cols-2 gap-2">
      <button id="sendDealerWhatsApp" class="rounded bg-green-600 py-2 font-semibold hover:bg-green-700">WhatsApp</button>
      <button id="sendDealerSMS" class="rounded bg-blue-600 py-2 font-semibold hover:bg-blue-700">SMS</button>
      <button id="sendDealerEmail" class="rounded bg-indigo-600 py-2 font-semibold hover:bg-indigo-700">Email</button>
      <button id="callDealerNow" class="rounded bg-red-600 py-2 font-semibold hover:bg-red-700">Call</button>
    </div>

  </div>

</div>



    <script>
/*
  ============================================
  ADS FEED SCRIPT (REWRITTEN & FIXED)
  - Fixes modal button click issues
  - Proper event propagation handling
  - Clean structure & comments
  ============================================
*/

// ==============================
// GLOBAL STATE
// ==============================

let page = 1;
let loading = false;
let finished = false;
let q = "";
let category = "";
let sort = "date";

let favs = [];
try {
  const stored = localStorage.getItem("ads_favorites");
  if (stored) {
    const parsed = JSON.parse(stored);
    // Validate that it's an array and contains only strings
    if (Array.isArray(parsed) && parsed.every(item => typeof item === 'string')) {
      // Limit array size to prevent DoS
      favs = parsed.slice(0, 1000);
    }
  }
} catch (e) {
  console.warn("Failed to load favorites:", e);
  favs = [];
  localStorage.removeItem("ads_favorites"); // Clear corrupted data
}
const grid = document.getElementById("ads-grid");
const loadingEl = document.getElementById("loading");
const noResultsEl = document.getElementById("no-results");

// Store active contact info
let activeContact = {};

// ==============================
// DEVICE FINGERPRINTING & AI
// ==============================
let userProfile = null;
let deviceReady = false;
let personalizedAds = [];

// Rate limiting for contact actions
const contactAttempts = new Map();
const RATE_LIMIT_WINDOW = 60000; // 1 minute
const MAX_ATTEMPTS = 3;

function checkRateLimit(action) {
  const now = Date.now();
  const key = `${action}-${activeContact.phone || activeContact.email}`;

  if (!contactAttempts.has(key)) {
    contactAttempts.set(key, []);
  }

  const attempts = contactAttempts.get(key);
  const recentAttempts = attempts.filter(time => now - time < RATE_LIMIT_WINDOW);

  if (recentAttempts.length >= MAX_ATTEMPTS) {
    alert("Too many attempts. Please wait a minute before trying again.");
    return false;
  }

  recentAttempts.push(now);
  contactAttempts.set(key, recentAttempts);
  return true;
}

// ==============================
// FAVORITES
// ==============================
async function toggleFav(id) {
  id = String(id);

  const isCurrentlyFavorited = favs.includes(id);
  const action = isCurrentlyFavorited ? 'unfavorite' : 'favorite';

  if (isCurrentlyFavorited) {
    favs = favs.filter(f => f !== id);
  } else {
    favs.push(id);
  }

  localStorage.setItem("ads_favorites", JSON.stringify(favs));

  // Track favorite interaction with analytics API
  try {
    await fetch('/app/api/track_interaction.php', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        interaction_type: action === 'favorite' ? 'favorite' : 'unfavorite',
        ad_id: id
      })
    });
  } catch (e) {
    console.error('Failed to track favorite:', e);
  }

  // Track with device fingerprinting (AI learning)
  if (window.deviceFingerprint && deviceReady) {
    try {
      // Favorites are treated as strong positive signals
      if (action === 'favorite') {
        await window.deviceFingerprint.trackInteraction(id, 'favorite');

        // Track category preference
        const card = document.querySelector(`[data-fav="${id}"]`)?.closest('.break-inside-avoid');
        const category = card?.dataset.category;
        if (category) {
          await window.deviceFingerprint.trackCategoryInteraction(category, true);
        }
      }
    } catch (e) {
      console.error('Failed to track AI learning for favorite:', e);
    }
  }
}

// ==============================
// FEED RESET
// ==============================
function resetFeed() {
  page = 1;
  finished = false;
  grid.innerHTML = "";
  noResultsEl.classList.add("hidden");
}

// ==============================
// LOAD CATEGORIES
// ==============================
async function loadCategories() {
  try {
    const res = await fetch("/app/api/get_categories.php");
    const data = await res.json();

    const select = document.getElementById("categoryFilter");
    select.innerHTML = '<option value="">All</option>';

    (data.categories || []).forEach(cat => {
      const opt = document.createElement("option");
      opt.value = cat;
      opt.textContent = cat;
      select.appendChild(opt);
    });
  } catch (e) {
    console.warn("loadCategories error", e);
  }
}

// ==============================
// INITIALIZE DEVICE INTELLIGENCE
// ==============================
async function initializeDeviceIntelligence() {
  if (deviceReady) return;

  try {
    // Initialize device fingerprint
    userProfile = await window.deviceFingerprint.init();
    deviceReady = true;

    console.log('🧠 AI Intelligence Active');
    console.log('Profile Strength:', userProfile ?
      (userProfile.behavior.total_interactions < 5 ? 'Learning...' :
       userProfile.behavior.total_interactions < 20 ? 'Building...' : 'Strong') :
      'New');

    // Get personalized recommendations
    if (userProfile && userProfile.behavior.total_interactions > 3) {
      const recommendations = await window.deviceFingerprint.getRecommendations();
      if (recommendations && recommendations.length > 0) {
        personalizedAds = recommendations.map(r => r.ad);
        console.log(`📊 Personalized: ${personalizedAds.length} ads ranked by relevance`);
      }
    }
  } catch (e) {
    console.warn('Device intelligence initialization failed:', e);
    deviceReady = false;
  }
}

// ==============================
// LOAD ADS (INTELLIGENT)
// ==============================
async function loadAds(reset = false) {
  if (reset) resetFeed();
  if (loading || finished) return;

  loading = true;
  loadingEl.classList.remove("hidden");

  try {
    // Initialize device intelligence on first load
    if (!deviceReady) {
      await initializeDeviceIntelligence();
    }

    // Get ads from API
    const res = await fetch(
      `/app/api/get_ads.php?page=${page}&q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}&sort=${encodeURIComponent(sort)}`
    );

    const data = await res.json();

    if (!data.ads || !data.ads.length) {
      finished = true;
      if (page === 1) noResultsEl.classList.remove("hidden");
    } else {
      let adsToRender = data.ads;

      // INTELLIGENT SORTING: Use personalized recommendations if available
      if (personalizedAds.length > 0 && !q && !category && sort === 'date') {
        adsToRender = sortAdsByPersonalization(data.ads);

        // Show intelligence indicator
        if (page === 1) {
          showIntelligenceIndicator();
        }
      }

      renderAds(adsToRender);
      page++;
    }
  } catch (e) {
    finished = true;
    console.warn("loadAds error", e);
  }

  loading = false;
  loadingEl.classList.add("hidden");
}

// ==============================
// INTELLIGENT AD SORTING
// ==============================
function sortAdsByPersonalization(ads) {
  if (!personalizedAds.length) return ads;

  // Create a map of personalized ad IDs with their scores
  const scoreMap = new Map();
  personalizedAds.forEach((ad, index) => {
    scoreMap.set(ad.ad_id, 1000 - index); // Higher score for higher ranked ads
  });

  // Sort ads by personalization score
  return ads.sort((a, b) => {
    const scoreA = scoreMap.get(a.ad_id) || 0;
    const scoreB = scoreMap.get(b.ad_id) || 0;
    return scoreB - scoreA;
  });
}

// ==============================
// SHOW INTELLIGENCE INDICATOR
// ==============================
function showIntelligenceIndicator() {
  const indicator = document.createElement('div');
  indicator.className = 'fixed top-20 right-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white px-4 py-2 rounded-lg shadow-lg z-50 animate-pulse';
  indicator.innerHTML = `
    <div class="flex items-center gap-2">
      <i class="fas fa-brain"></i>
      <span class="text-sm font-semibold">AI Personalized</span>
    </div>
  `;
  document.body.appendChild(indicator);

  // Remove after 3 seconds
  setTimeout(() => {
    indicator.style.opacity = '0';
    indicator.style.transition = 'opacity 0.5s';
    setTimeout(() => indicator.remove(), 500);
  }, 3000);
}

// ==============================
// SECURITY: HTML SANITIZATION
// ==============================
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ==============================
// RENDER ADS
// ==============================
function renderAds(ads) {
  ads.forEach(ad => {
    const id = String(ad.ad_id || ad.id || Math.random());

    // Track view (only once per ad per session)
    trackAdView(id);

    // Create card container
    const card = document.createElement("div");
    card.className = "break-inside-avoid bg-white/10 rounded-xl overflow-hidden shadow-lg hover:shadow-xl transition hover:-translate-y-1";

    // Store contact data and ad info in dataset
    card.dataset.contact = JSON.stringify(ad.contact || {});
    card.dataset.adTitle = ad.title || 'Untitled';
    card.dataset.adDescription = ad.description || '';
    card.dataset.adId = id;
    card.dataset.category = ad.category || 'uncategorized';

    // Sanitize user inputs
    const safeTitle = escapeHtml(ad.title || 'Untitled');
    const safeCategory = escapeHtml(ad.category || '');
    const safeMedia = escapeHtml(ad.media || '');

    // Create media container
    const mediaContainer = document.createElement('div');
    mediaContainer.className = 'relative h-64 overflow-hidden';

    // Create favorite button
    const favBtn = document.createElement('button');
    favBtn.setAttribute('data-fav', id);
    favBtn.className = `absolute top-2 right-2 w-9 h-9 rounded-full flex items-center justify-center text-white text-xl ${favs.includes(id) ? 'bg-red-600' : 'bg-black/60'}`;
    favBtn.textContent = '❤️';
    mediaContainer.appendChild(favBtn);

    // Create media element
    const isVideo = ad.media && /\.(mp4|mov|webm)$/i.test(ad.media);
    if (isVideo) {
      const video = document.createElement('video');
      video.autoplay = true;
      video.muted = true;
      video.loop = true;
      video.playsInline = true;
      video.className = 'w-full h-full object-cover';

      const source = document.createElement('source');
      source.src = safeMedia;
      video.appendChild(source);

      mediaContainer.appendChild(video);
    } else {
      const img = document.createElement('img');
      img.src = safeMedia;
      img.alt = safeTitle;
      img.className = 'w-full h-full object-cover';
      mediaContainer.appendChild(img);
    }

    // Create category badge
    const categoryBadge = document.createElement('div');
    categoryBadge.className = 'absolute bottom-2 left-2 bg-black/60 px-2 rounded text-xs';
    categoryBadge.textContent = safeCategory;
    mediaContainer.appendChild(categoryBadge);

    // Create content section
    const contentDiv = document.createElement('div');
    contentDiv.className = 'p-3';

    // Create title
    const titleDiv = document.createElement('div');
    titleDiv.className = 'font-bold truncate';
    titleDiv.textContent = safeTitle;
    contentDiv.appendChild(titleDiv);

    // Create button container
    const buttonContainer = document.createElement('div');
    buttonContainer.className = 'mt-3 flex gap-2';

    // Create contact button (NO ID to avoid duplicates)
    const contactBtn = document.createElement('button');
    contactBtn.className = 'contact-dealer flex-1 bg-indigo-600 hover:bg-indigo-700 py-2 rounded text-sm';
    contactBtn.textContent = 'Contact Dealer';
    buttonContainer.appendChild(contactBtn);

    // Create more button
    const moreBtn = document.createElement('button');
    moreBtn.className = 'more-dealer flex-1 bg-gray-700 hover:bg-gray-800 py-2 rounded text-sm';
    moreBtn.textContent = 'More from them';
    buttonContainer.appendChild(moreBtn);

    contentDiv.appendChild(buttonContainer);

    // Create interaction buttons container (Like/Not Interested)
    const interactionContainer = document.createElement('div');
    interactionContainer.className = 'mt-2 flex gap-2';

    // Check if user already liked/disliked this ad
    const likedAds = getLikedAds();
    const dislikedAds = getDislikedAds();
    const isLiked = likedAds.includes(id);
    const isDisliked = dislikedAds.includes(id);

    // Create Like button
    const likeBtn = document.createElement('button');
    likeBtn.setAttribute('data-like', id);
    likeBtn.className = `like-btn flex-1 py-2 rounded text-sm transition-all ${
      isLiked
        ? 'bg-green-600 text-white'
        : 'bg-white/10 hover:bg-green-600/20 border border-white/20'
    }`;
    likeBtn.innerHTML = `<i class="fas fa-thumbs-up mr-1"></i>${isLiked ? 'Liked' : 'Like'}`;
    interactionContainer.appendChild(likeBtn);

    // Create Not Interested button
    const dislikeBtn = document.createElement('button');
    dislikeBtn.setAttribute('data-dislike', id);
    dislikeBtn.className = `dislike-btn flex-1 py-2 rounded text-sm transition-all ${
      isDisliked
        ? 'bg-red-600 text-white'
        : 'bg-white/10 hover:bg-red-600/20 border border-white/20'
    }`;
    dislikeBtn.innerHTML = `<i class="fas fa-thumbs-down mr-1"></i>${isDisliked ? 'Not Interested' : 'Not Interested'}`;
    interactionContainer.appendChild(dislikeBtn);

    contentDiv.appendChild(interactionContainer);

    // Assemble card
    card.appendChild(mediaContainer);
    card.appendChild(contentDiv);
    grid.appendChild(card);

    // Start tracking time for this ad
    startTrackingTime(id);
  });
}

// ==============================
// EVENTS
// ==============================
grid.addEventListener("click", e => {
  const favBtn = e.target.closest("[data-fav]");
  if (favBtn) {
    toggleFav(favBtn.dataset.fav);
    favBtn.classList.toggle("bg-red-600");
    favBtn.classList.toggle("bg-black/60");
    return;
  }

  // Handle Like button
  const likeBtn = e.target.closest("[data-like]");
  if (likeBtn) {
    const adId = likeBtn.dataset.like;
    handleLike(adId, likeBtn);
    return;
  }

  // Handle Dislike button
  const dislikeBtn = e.target.closest("[data-dislike]");
  if (dislikeBtn) {
    const adId = dislikeBtn.dataset.dislike;
    handleDislike(adId, dislikeBtn);
    return;
  }

  const contactBtn = e.target.closest(".contact-dealer");
  if (contactBtn) {
    const card = contactBtn.closest(".break-inside-avoid");
    let contact = {};
    try {
      contact = JSON.parse(card.dataset.contact || "{}");
    } catch (e) {
      console.error("Failed to parse contact data:", e);
      alert("Error loading contact information.");
      return;
    }

    // Extract ad info for auto-fill
    const adTitle = card.dataset.adTitle || '';
    const adDescription = card.dataset.adDescription || '';
    const adId = card.dataset.adId || '';

    // Add ad ID to contact object
    contact.adId = adId;

    openDealerModal(contact, adTitle, adDescription);
    return;
  }

});

// Search & filters
document.getElementById("btnSearch").onclick = () => {
  q = document.getElementById("search").value.trim();
  loadAds(true);
};

document.getElementById("categoryFilter").onchange = e => {
  category = e.target.value;
  loadAds(true);
};

document.getElementById("sortFilter").onchange = e => {
  sort = e.target.value;
  loadAds(true);
};

let debounce;
document.getElementById("search").oninput = e => {
  clearTimeout(debounce);
  debounce = setTimeout(() => {
    q = e.target.value.trim();
    loadAds(true);
  }, 350);
};

// Infinite scroll
window.addEventListener("scroll", () => {
  if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 450) {
    loadAds();
  }
});

// ==============================
// MODAL FUNCTIONS
// ==============================
function openDealerModal(contact = {}, adTitle = '', adDescription = '') {
  const modal = document.getElementById("contactDealerModal");
  const modalCard = document.getElementById("contactDealerCard");
  const messageBox = document.getElementById("contactDealerMessage");
  const charCount = document.getElementById("charCount");
  const senderName = document.getElementById("senderName");
  const senderContact = document.getElementById("senderContact");

  // Store contact data
  activeContact = contact;

  // Clear sender info fields
  senderName.value = "";
  senderContact.value = "";

  // Auto-fill message with ad details
  let autoMessage = "Hi, I'm interested in your ad";

  if (adTitle) {
    autoMessage += ` titled "${adTitle}"`;
  }

  if (adDescription) {
    autoMessage += `.\n\nDescription: ${adDescription}`;
  }

  autoMessage += ".\n\nCan I get more info on this?\n\nThank you.";

  // Ensure message doesn't exceed 500 characters
  if (autoMessage.length > 500) {
    // Truncate description if too long
    const maxDescLength = 500 - autoMessage.length + adDescription.length - 3;
    if (maxDescLength > 0) {
      const truncatedDesc = adDescription.substring(0, maxDescLength) + '...';
      autoMessage = "Hi, I'm interested in your ad";
      if (adTitle) {
        autoMessage += ` titled "${adTitle}"`;
      }
      autoMessage += `.\n\nDescription: ${truncatedDesc}`;
      autoMessage += ".\n\nCan I get more info on this?\n\nThank you.";
    } else {
      // If still too long, just use title
      autoMessage = `Hi, I'm interested in your ad "${adTitle}".\n\nCan I get more info on this?\n\nThank you.`;
    }
  }

  messageBox.value = autoMessage;
  if (charCount) charCount.textContent = autoMessage.length;

  // Show modal
  modal.classList.remove("hidden");
  modal.classList.add("flex", "items-center", "justify-center");

  // Animate modal card in
  setTimeout(() => {
    modalCard.classList.remove("scale-95", "opacity-0");
    modalCard.classList.add("scale-100", "opacity-100");
    messageBox.focus();
    // Move cursor to end of text
    messageBox.setSelectionRange(messageBox.value.length, messageBox.value.length);
  }, 10);
}

// Character counter for message textarea
const messageBox = document.getElementById("contactDealerMessage");
const charCount = document.getElementById("charCount");
if (messageBox && charCount) {
  messageBox.addEventListener("input", () => {
    charCount.textContent = messageBox.value.length;
  });
}

function closeDealerModal() {
  const modal = document.getElementById("contactDealerModal");
  const modalCard = document.getElementById("contactDealerCard");

  // Animate modal card out
  modalCard.classList.remove("scale-100", "opacity-100");
  modalCard.classList.add("scale-95", "opacity-0");

  // Hide modal after animation
  setTimeout(() => {
    modal.classList.remove("flex", "items-center", "justify-center");
    modal.classList.add("hidden");
  }, 200);
}

// Close modal when clicking outside (backdrop)
document.getElementById("contactDealerModal").addEventListener("click", (e) => {
  if (e.target.id === "contactDealerModal") {
    closeDealerModal();
  }
});

// Close modal with X button
document.getElementById("closeDealerModalBtn").addEventListener("click", closeDealerModal);

// ==============================
// CONTACT ACTIONS
// ==============================
// Build final message with sender info
function buildFinalMessage(message) {
  const senderName = document.getElementById("senderName").value.trim();
  const senderContact = document.getElementById("senderContact").value.trim();

  let finalMessage = message;

  if (senderName || senderContact) {
    finalMessage += "\n\n---\n";
    if (senderName) {
      finalMessage += `From: ${senderName}\n`;
    }
    if (senderContact) {
      finalMessage += `Contact: ${senderContact}\n`;
    }
  } else {
    finalMessage += "\n\n---\n";
  }

  // Add timestamp
  const now = new Date();
  const dateStr = now.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
  const timeStr = now.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  });

  finalMessage += `Sent on: ${dateStr} at: ${timeStr}`;

  return finalMessage;
}

// Input validation functions
function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(String(email).toLowerCase());
}

function validatePhone(phone) {
  const cleaned = String(phone).replace(/\D/g, '');
  return cleaned.length >= 9 && cleaned.length <= 15;
}

function sanitizeMessage(msg) {
  if (!msg) return '';
  // Limit message length
  let sanitized = String(msg).trim();
  if (sanitized.length > 500) {
    sanitized = sanitized.substring(0, 500);
  }
  // Remove potentially dangerous characters
  sanitized = sanitized.replace(/[<>]/g, '');
  return sanitized;
}

// Normalize phone number to international format
function normalizePhone(phone) {
  if (!phone) return "";
  let num = String(phone).replace(/\D/g, "");
  if (num.startsWith("0")) num = "254" + num.slice(1);
  if (!num.startsWith("254")) num = "254" + num;
  return num;
}

// Call button handler
document.getElementById("callDealerNow").addEventListener("click", () => {
  if (!checkRateLimit('call')) return;

  const phone = activeContact.phone;

  if (!phone) {
    alert("No phone number available for this seller.");
    return;
  }

  if (!validatePhone(phone)) {
    alert("Invalid phone number format.");
    return;
  }

  // Track contact event
  if (activeContact.adId) {
    trackContact(activeContact.adId, 'call');
  }

  const normalizedPhone = normalizePhone(phone);
  window.location.href = `tel:+${normalizedPhone}`;
});

// WhatsApp button handler
document.getElementById("sendDealerWhatsApp").addEventListener("click", () => {
  if (!checkRateLimit('whatsapp')) return;

  const phone = activeContact.phone;
  const rawMessage = document.getElementById("contactDealerMessage").value;

  if (!phone) {
    alert("No phone number available for this seller.");
    return;
  }

  if (!validatePhone(phone)) {
    alert("Invalid phone number format.");
    return;
  }

  const message = sanitizeMessage(rawMessage);
  if (!message) {
    alert("Please type a message first!");
    return;
  }

  // Build final message with sender info
  const finalMessage = buildFinalMessage(message);

  // Track contact event
  if (activeContact.adId) {
    trackContact(activeContact.adId, 'whatsapp');
  }

  const normalizedPhone = normalizePhone(phone);
  const encodedMessage = encodeURIComponent(finalMessage);
  window.open(`https://wa.me/${normalizedPhone}?text=${encodedMessage}`, "_blank");
});

// SMS button handler
document.getElementById("sendDealerSMS").addEventListener("click", () => {
  if (!checkRateLimit('sms')) return;

  const phone = activeContact.phone;
  const rawMessage = document.getElementById("contactDealerMessage").value;

  if (!phone) {
    alert("No phone number available for this seller.");
    return;
  }

  if (!validatePhone(phone)) {
    alert("Invalid phone number format.");
    return;
  }

  const message = sanitizeMessage(rawMessage);
  if (!message) {
    alert("Please type a message first!");
    return;
  }

  // Build final message with sender info
  const finalMessage = buildFinalMessage(message);

  // Track contact event
  trackContact(activeContact.adId, 'sms');

  const normalizedPhone = normalizePhone(phone);
  const encodedMessage = encodeURIComponent(finalMessage);
  window.location.href = `sms:+${normalizedPhone}?body=${encodedMessage}`;
});

// Email button handler
document.getElementById("sendDealerEmail").addEventListener("click", () => {
  if (!checkRateLimit('email')) return;

  const email = activeContact.email;
  const rawMessage = document.getElementById("contactDealerMessage").value;

  if (!email) {
    alert("No email address available for this seller.");
    return;
  }

  if (!validateEmail(email)) {
    alert("Invalid email address format.");
    return;
  }

  const message = sanitizeMessage(rawMessage);
  if (!message) {
    alert("Please type a message first!");
    return;
  }

  // Build final message with sender info
  const finalMessage = buildFinalMessage(message);

  // Track contact event
  if (activeContact.adId) {
    trackContact(activeContact.adId, 'email');
  }

  const encodedMessage = encodeURIComponent(finalMessage);
  const subject = encodeURIComponent("Inquiry about your ad");
  window.location.href = `mailto:${email}?subject=${subject}&body=${encodedMessage}`;
});

// ==============================
// LIKE/DISLIKE TRACKING
// ==============================
function getLikedAds() {
  try {
    const stored = localStorage.getItem("ads_liked");
    if (stored) {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed)) {
        return parsed.slice(0, 1000); // Limit to prevent abuse
      }
    }
  } catch (e) {
    console.warn("Failed to load liked ads:", e);
  }
  return [];
}

function getDislikedAds() {
  try {
    const stored = localStorage.getItem("ads_disliked");
    if (stored) {
      const parsed = JSON.parse(stored);
      if (Array.isArray(parsed)) {
        return parsed.slice(0, 1000);
      }
    }
  } catch (e) {
    console.warn("Failed to load disliked ads:", e);
  }
  return [];
}

function saveLikedAds(likedAds) {
  try {
    localStorage.setItem("ads_liked", JSON.stringify(likedAds));
  } catch (e) {
    console.warn("Failed to save liked ads:", e);
  }
}

function saveDislikedAds(dislikedAds) {
  try {
    localStorage.setItem("ads_disliked", JSON.stringify(dislikedAds));
  } catch (e) {
    console.warn("Failed to save disliked ads:", e);
  }
}

async function handleLike(adId, button) {
  const likedAds = getLikedAds();
  const dislikedAds = getDislikedAds();

  // Check if already liked
  if (likedAds.includes(adId)) {
    // Unlike
    const newLiked = likedAds.filter(id => id !== adId);
    saveLikedAds(newLiked);

    // Update button UI
    button.classList.remove('bg-green-600', 'text-white');
    button.classList.add('bg-white/10');
    button.innerHTML = '<i class="fas fa-thumbs-up mr-1"></i>Like';
    return;
  }

  // Remove from disliked if exists
  if (dislikedAds.includes(adId)) {
    const newDisliked = dislikedAds.filter(id => id !== adId);
    saveDislikedAds(newDisliked);

    // Update dislike button if visible
    const dislikeBtn = document.querySelector(`[data-dislike="${adId}"]`);
    if (dislikeBtn) {
      dislikeBtn.classList.remove('bg-red-600', 'text-white');
      dislikeBtn.classList.add('bg-white/10');
      dislikeBtn.innerHTML = '<i class="fas fa-thumbs-down mr-1"></i>Not Interested';
    }
  }

  // Add to liked
  likedAds.push(adId);
  saveLikedAds(likedAds);

  // Update button UI
  button.classList.remove('bg-white/10');
  button.classList.add('bg-green-600', 'text-white');
  button.innerHTML = '<i class="fas fa-thumbs-up mr-1"></i>Liked';

  // Track interaction (standard)
  try {
    await fetch('/app/api/track_interaction.php', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        interaction_type: 'like',
        ad_id: adId
      })
    });
  } catch (e) {
    console.error('Failed to track like:', e);
  }

  // Track with device fingerprinting (AI learning)
  if (window.deviceFingerprint && deviceReady) {
    try {
      await window.deviceFingerprint.trackInteraction(adId, 'like');

      // Find ad category and track it
      const card = button.closest('.break-inside-avoid');
      const category = card.dataset.category;
      if (category) {
        await window.deviceFingerprint.trackCategoryInteraction(category, true);
      }
    } catch (e) {
      console.error('Failed to track AI learning:', e);
    }
  }
}

async function handleDislike(adId, button) {
  const likedAds = getLikedAds();
  const dislikedAds = getDislikedAds();

  // Check if already disliked
  if (dislikedAds.includes(adId)) {
    // Un-dislike
    const newDisliked = dislikedAds.filter(id => id !== adId);
    saveDislikedAds(newDisliked);

    // Update button UI
    button.classList.remove('bg-red-600', 'text-white');
    button.classList.add('bg-white/10');
    button.innerHTML = '<i class="fas fa-thumbs-down mr-1"></i>Not Interested';
    return;
  }

  // Remove from liked if exists
  if (likedAds.includes(adId)) {
    const newLiked = likedAds.filter(id => id !== adId);
    saveLikedAds(newLiked);

    // Update like button if visible
    const likeBtn = document.querySelector(`[data-like="${adId}"]`);
    if (likeBtn) {
      likeBtn.classList.remove('bg-green-600', 'text-white');
      likeBtn.classList.add('bg-white/10');
      likeBtn.innerHTML = '<i class="fas fa-thumbs-up mr-1"></i>Like';
    }
  }

  // Add to disliked
  dislikedAds.push(adId);
  saveDislikedAds(dislikedAds);

  // Update button UI
  button.classList.remove('bg-white/10');
  button.classList.add('bg-red-600', 'text-white');
  button.innerHTML = '<i class="fas fa-thumbs-down mr-1"></i>Not Interested';

  // Track interaction
  try {
    await fetch('/app/api/track_interaction.php', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        interaction_type: 'dislike',
        ad_id: adId
      })
    });
  } catch (e) {
    console.error('Failed to track dislike:', e);
  }

  // Track with device fingerprinting (AI learning)
  if (window.deviceFingerprint && deviceReady) {
    try {
      await window.deviceFingerprint.trackInteraction(adId, 'dislike');

      // Find ad category and track negative preference
      const card = button.closest('.break-inside-avoid');
      const category = card.dataset.category;
      if (category) {
        await window.deviceFingerprint.trackCategoryInteraction(category, false);
      }
    } catch (e) {
      console.error('Failed to track AI learning:', e);
    }
  }
}

// ==============================
// TIME TRACKING
// ==============================
const adTimeTracking = new Map();

function startTrackingTime(adId) {
  if (!adTimeTracking.has(adId)) {
    adTimeTracking.set(adId, {
      startTime: Date.now(),
      reported: false
    });
  }
}

function stopTrackingTime(adId) {
  if (adTimeTracking.has(adId)) {
    const tracking = adTimeTracking.get(adId);
    if (!tracking.reported) {
      const timeSpent = Math.floor((Date.now() - tracking.startTime) / 1000); // Convert to seconds

      // Only report if user spent at least 3 seconds viewing
      if (timeSpent >= 3) {
        trackTimeSpent(adId, timeSpent);
      }

      tracking.reported = true;
    }
  }
}

async function trackTimeSpent(adId, seconds) {
  try {
    await fetch('/app/api/track_interaction.php', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        interaction_type: 'time_spent',
        ad_id: adId,
        value: seconds
      })
    });
  } catch (e) {
    console.error('Failed to track time:', e);
  }
}

// Track time when user leaves page or scrolls away
window.addEventListener('beforeunload', () => {
  adTimeTracking.forEach((tracking, adId) => {
    stopTrackingTime(adId);
  });
});

// Track time periodically for ads in viewport
let lastScrollTime = Date.now();
window.addEventListener('scroll', () => {
  const now = Date.now();

  // Only check every 2 seconds to avoid performance issues
  if (now - lastScrollTime < 2000) return;
  lastScrollTime = now;

  // Check which ads are in viewport and report time for those that scrolled away
  const cards = document.querySelectorAll('.break-inside-avoid');
  cards.forEach(card => {
    const adId = card.dataset.adId;
    if (!adId) return;

    const rect = card.getBoundingClientRect();
    const isInViewport = rect.top < window.innerHeight && rect.bottom > 0;

    if (!isInViewport && adTimeTracking.has(adId)) {
      stopTrackingTime(adId);
    }
  });
});

// ==============================
// ANALYTICS TRACKING
// ==============================
const viewedAds = new Set();

async function trackAdView(adId) {
  // Only track once per session
  if (viewedAds.has(adId)) return;
  viewedAds.add(adId);

  try {
    await fetch('/app/api/track_event.php', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: 'view',
        ad_id: adId,
        metadata: {
          referrer: document.referrer,
          page: window.location.pathname
        }
      })
    });
  } catch (e) {
    console.error('Failed to track view:', e);
  }
}

async function trackContact(adId, method) {
  try {
    await fetch('/app/api/track_event.php', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: 'contact',
        ad_id: adId,
        metadata: {
          method: method,
          timestamp: Date.now()
        }
      })
    });
  } catch (e) {
    console.error('Failed to track contact:', e);
  }
}

// ==============================
// INIT
// ==============================
loadCategories();
loadAds();

    </script>