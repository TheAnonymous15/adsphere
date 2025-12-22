<link rel="stylesheet" href="/services/assets/css/all.min.css">
<script src="https://cdn.tailwindcss.com"></script>

<!-- ===================== CONTACT MODAL ===================== -->
<div id="contactModals" class="fixed bottom-6 right-6 z-50 hidden">
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
      <button id="sendWhatsap" class="rounded bg-green-600 py-2 font-semibold hover:bg-green-700">WhatsApp</button>
      <button id="sendSMSs" class="rounded bg-blue-600 py-2 font-semibold hover:bg-blue-700">SMS</button>
      <button id="sendEmaill" class="rounded bg-indigo-600 py-2 font-semibold hover:bg-indigo-700">Email</button>
      <button id="callNoww" class="rounded bg-red-600 py-2 font-semibold hover:bg-red-700">Call</button>
    </div>

  </div>
</div>

<!-- ===================== TOGGLE BUTTON ===================== -->
<button id="contactBtn" 
  class="fixed bottom-6 right-6 z-50 bg-gradient-to-br from-pink-400 to-indigo-500
         hover:from-pink-500 hover:to-indigo-600 text-white p-4 rounded-full
         shadow-2xl transform transition-all duration-300 hover:scale-110">
  <i class="fas fa-comment fa-lg"></i>
</button>

<script>
const contactBtn = document.getElementById('contactBtn');
const contactModal = document.getElementById('contactModals');
const contactCard = document.getElementById('contactCard');
const closeModalBtn = document.getElementById('closeModalBtn');
const contactMessage = document.getElementById('contactMessage');
const sendWhatsapp = document.getElementById('sendWhatsap');
const sendSMS = document.getElementById('sendSMSs');
const sendEmail = document.getElementById('sendEmaill');
const callNow = document.getElementById('callNoww');

const phoneNumber = '+254726781724';
const emailAddress = 'ld@aplus.anonaddy.com';

// -------------------------
// Open/Close Modal
// -------------------------
contactBtn.addEventListener('click', () => {
  contactModal.classList.remove('hidden');
  requestAnimationFrame(() => {
    contactCard.classList.remove('scale-95', 'opacity-0');
    contactCard.classList.add('scale-100', 'opacity-100');
    contactMessage.focus();
  });
});

closeModalBtn.addEventListener('click', () => {
  contactCard.classList.add('scale-95', 'opacity-0');
  setTimeout(() => contactModal.classList.add('hidden'), 200);
});

// -------------------------
// Action Buttons
// -------------------------
sendWhatsapp.addEventListener('click', () => {
  const msg = encodeURIComponent(contactMessage.value.trim());
  if(msg) window.open(`https://wa.me/${phoneNumber.replace(/\D/g,'')}?text=${msg}`, '_blank');
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

// -------------------------
// Close when clicking outside modal
// -------------------------
document.addEventListener('click', (e) => {
  if (!contactCard.contains(e.target) && !contactBtn.contains(e.target) && !contactModal.classList.contains('hidden')) {
    contactCard.classList.add('scale-95', 'opacity-0');
    setTimeout(() => contactModal.classList.add('hidden'), 200);
  }
});
</script>
