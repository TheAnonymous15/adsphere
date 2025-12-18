<link rel="stylesheet" href="/app/assets/css/all.min.css">
<script src="/app/assets/css/tailwind.js"></script>

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

<!-- CONTACT MODAL -->
<div id="contactModal" class="fixed bottom-6 right-6 z-50 hidden">
  <div id="contactCard" class="w-80 rounded-2xl bg-slate-900 p-6 shadow-xl transform scale-95 opacity-0 transition-all duration-300">

    <!-- HEADER -->
    <div class="mb-4 flex items-center justify-between">
      <h3 class="text-lg font-bold text-white">Contact Seller</h3>
      <button id="closeModalBtn" class="text-white text-xl hover:text-gray-300">&times;</button>
    </div>

    <!-- MESSAGE -->
    <textarea id="contactMessage" rows="4" placeholder="Type your message..."
      class="mb-4 w-full rounded-xl border border-gray-700 bg-slate-800 p-3 text-white placeholder-white/70
             focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"></textarea>

    <!-- ACTION BUTTONS -->
    <div class="grid grid-cols-2 gap-2">
      <button id="sendWhatsapp" class="rounded bg-green-600 py-2 font-semibold hover:bg-green-700">WhatsApp</button>
      <button id="sendSMS" class="rounded bg-blue-600 py-2 font-semibold hover:bg-blue-700">SMS</button>
      <button id="sendEmail" class="rounded bg-indigo-600 py-2 font-semibold hover:bg-indigo-700">Email</button>
      <button id="callNow" class="rounded bg-red-600 py-2 font-semibold hover:bg-red-700">Call</button>
    </div>

  </div>
</div>

<script>
const grid = document.getElementById("ads-grid");
const loadingEl = document.getElementById("loading");
const noResultsEl = document.getElementById("no-results");

const contactModal = document.getElementById('contactModal');
const contactCard = document.getElementById('contactCard');
const closeModalBtn = document.getElementById('closeModalBtn');
const contactMessage = document.getElementById('contactMessage');
const sendWhatsapp = document.getElementById('sendWhatsapp');
const sendSMS = document.getElementById('sendSMS');
const sendEmail = document.getElementById('sendEmail');
const callNow = document.getElementById('callNow');

const phoneNumber = '+2547267817247'; // seller number
const emailAddress = 'example@example.com'; // seller email

// ==============================
// GLOBAL STATE
// ==============================
let page = 1, loading = false, finished = false;
let q = "", category = "", sort = "date";
let favs = [];
try { favs = JSON.parse(localStorage.getItem("ads_favorites")) || []; } catch(e){ favs = []; }

// ==============================
// MODAL FUNCTIONS
// ==============================
function openContactModal(contact = {}) {
  contactMessage.value = "";
  contactModal.classList.remove('hidden');
  requestAnimationFrame(() => {
    contactCard.classList.remove('scale-95', 'opacity-0');
    contactCard.classList.add('scale-100', 'opacity-100');
    contactMessage.focus();
  });
}

closeModalBtn.addEventListener('click', () => {
  contactCard.classList.add('scale-95', 'opacity-0');
  setTimeout(() => contactModal.classList.add('hidden'), 200);
});

// Close clicking outside modal
document.addEventListener('click', e => {
  if(!contactCard.contains(e.target) && !e.target.closest(".contact-dealer") && !contactModal.classList.contains('hidden')) {
    contactCard.classList.add('scale-95', 'opacity-0');
    setTimeout(() => contactModal.classList.add('hidden'), 200);
  }
});

// Modal actions
sendWhatsapp.addEventListener('click', () => {
  const msg = encodeURIComponent(contactMessage.value.trim());
  if(msg) window.open(`https://wa.me/${phoneNumber}?text=${msg}`, '_blank');
  else alert('Please type a message first!');
});

sendSMS.addEventListener('click', () => {
  const msg = encodeURIComponent(contactMessage.value.trim());
  if(msg) window.open(`sms:${phoneNumber}?body=${msg}`, '_blank');
  else alert('Please type a message first!');
});

sendEmail.addEventListener('click', () => {
  const msg = encodeURIComponent(contactMessage.value.trim());
  window.open(`mailto:${emailAddress}?body=${msg}`, '_blank');
});

callNow.addEventListener('click', () => {
  window.open(`tel:${phoneNumber}`, '_self');
});

// ==============================
// FAVORITES
// ==============================
function toggleFav(id){
  id = String(id);
  if(favs.includes(id)) favs = favs.filter(f => f!==id);
  else favs.push(id);
  localStorage.setItem("ads_favorites", JSON.stringify(favs));
}

// ==============================
// RESET FEED
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
async function loadCategories(){
  try {
    const res = await fetch("/app/api/get_categories.php");
    const data = await res.json();
    const select = document.getElementById("categoryFilter");
    select.innerHTML = `<option value="">All</option>`;
    (data.categories || []).forEach(cat => {
      let o = document.createElement("option");
      o.value = cat;
      o.textContent = cat;
      select.appendChild(o);
    });
  } catch(e){ console.warn("loadCategories error", e); }
}

// ==============================
// LOAD ADS
// ==============================
async function loadAds(reset=false){
  if(reset) resetFeed();
  if(loading || finished) return;
  loading = true;
  loadingEl.classList.remove("hidden");

  try {
    const res = await fetch(`/app/api/get_ads.php?page=${page}&q=${encodeURIComponent(q)}&category=${encodeURIComponent(category)}&sort=${encodeURIComponent(sort)}`);
    const data = await res.json();
    if(!data.ads?.length){
      finished = true;
      if(page===1) noResultsEl.classList.remove("hidden");
    } else {
      renderAds(data.ads);
      page++;
    }
  } catch(e){ finished = true; console.warn("loadAds error", e); }

  loading = false;
  loadingEl.classList.add("hidden");
}

// ==============================
// RENDER ADS
// ==============================
function renderAds(ads){
  ads.forEach(ad=>{
    const id = String(ad.ad_id || ad.id || Math.random());
    const div = document.createElement("div");
    div.className = "break-inside-avoid bg-white/10 rounded-xl overflow-hidden shadow-lg hover:shadow-xl transition hover:-translate-y-1";
    div.dataset.contact = JSON.stringify(ad.contact || {});

    const isVideo = ad.media && /\.(mp4|mov|webm)$/i.test(ad.media);
    const media = isVideo
      ? `<video autoplay muted loop playsinline class="w-full h-full object-cover"><source src="${ad.media}"></video>`
      : `<img src="${ad.media}" class="w-full h-full object-cover">`;

    div.innerHTML = `
      <div class="relative h-64 overflow-hidden">
        <button data-fav="${id}" class="absolute top-2 right-2 w-9 h-9 rounded-full flex items-center justify-center text-white text-xl ${favs.includes(id)?'bg-red-600':'bg-black/60'}">❤️</button>
        ${media}
        <div class="absolute bottom-2 left-2 bg-black/60 px-2 rounded text-xs">${ad.category}</div>
      </div>
      <div class="p-3">
        <div class="font-bold truncate">${ad.title} - ${ad.description}</div>
        <div class="mt-3 flex gap-2">
          <button class="contact-dealer flex-1 bg-blue-600 hover:bg-blue-700 py-2 rounded text-sm">Contact Dealer</button>
          <button class="more-dealer flex-1 bg-gray-700 hover:bg-gray-800 py-2 rounded text-sm">More from them</button>
        </div>
      </div>
    `;
    grid.appendChild(div);
  });
}

// ==============================
// GRID EVENT DELEGATION
// ==============================
grid.addEventListener('click', e => {
  const favBtn = e.target.closest("[data-fav]");
  if(favBtn){
    toggleFav(favBtn.dataset.fav);
    favBtn.classList.toggle("bg-red-600");
    favBtn.classList.toggle("bg-black/60");
    return;
  }

  const contactBtn = e.target.closest(".contact-dealer");
  if(contactBtn){
    const card = contactBtn.closest(".break-inside-avoid");
    const contact = JSON.parse(card.dataset.contact || "{}");
    openContactModal(contact);
    return;
  }

  const moreBtn = e.target.closest(".more-dealer");
  if(moreBtn){
    const card = moreBtn.closest(".break-inside-avoid");
    console.log("TODO: load more ads from same dealer:", card.dataset.contact);
    return;
  }
});

// ==============================
// SEARCH & FILTERS
// ==============================
document.getElementById("btnSearch").onclick = () => { q = document.getElementById("search").value.trim(); loadAds(true); };
document.getElementById("categoryFilter").onchange = e => { category = e.target.value; loadAds(true); };
document.getElementById("sortFilter").onchange = e => { sort = e.target.value; loadAds(true); };
let debounce;
document.getElementById("search").oninput = e => { clearTimeout(debounce); debounce = setTimeout(()=>{q=e.target.value.trim(); loadAds(true);}, 350); };

// ==============================
// INFINITE SCROLL
// ==============================
window.addEventListener("scroll", ()=>{
  if(window.innerHeight + window.scrollY >= document.body.offsetHeight - 450) loadAds();
});

// ==============================
// INIT
// ==============================
loadCategories();
loadAds();
</script>
