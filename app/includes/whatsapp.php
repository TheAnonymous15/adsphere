<div id="whatsappWidget" class="fixed bottom-6 right-6 z-50 flex flex-col items-end space-y-2">
  <!-- WhatsApp Floating Button -->
  <button id="whatsappBtn" 
    class="bg-gradient-to-br from-pink-400 to-indigo-500 hover:from-pink-500 hover:to-indigo-600 text-white p-4 rounded-full shadow-2xl transform transition-all duration-300 hover:scale-110 hover:shadow-[0_10px_20px_rgba(236,72,153,0.5)]">
    <i class="fab fa-whatsapp fa-lg"></i>
  </button>

  <!-- Chat Box -->
  <div id="whatsappChat" 
    class="hidden absolute w-80 bg-white/10 backdrop-blur-xl rounded-2xl shadow-[0_10px_25px_rgba(0,0,0,0.2),0_5px_10px_rgba(0,0,0,0.1)] overflow-hidden flex flex-col transform scale-95 opacity-0 transition-all duration-300">

    <!-- Header -->
    <div id="whatsappHeader" class="bg-gradient-to-r from-pink-400 to-indigo-500 text-white px-4 py-3 font-semibold flex justify-between items-center cursor-move shadow-md">
      <span>Send us a message</span>
      <button id="closeWhatsapp" class="text-white text-xl font-bold hover:text-gray-200">&times;</button>
    </div>

    <!-- Message Box -->
    <div class="p-4 flex-1 flex flex-col justify-between space-y-3">
      <textarea id="whatsappMessage" rows="4" placeholder="Type your message..."
        class="w-full p-3 border border-white/20 rounded-xl bg-white/10 backdrop-blur-md text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-pink-400 resize-none shadow-inner transition-all duration-300 hover:shadow-lg"></textarea>

        <!-- Send WhatsApp -->
        

         <button id="sendWhatsapp" 
        class="bg-gradient-to-r from-pink-400 to-indigo-500 hover:from-pink-500 hover:to-indigo-600 text-white px-5 py-3 rounded-xl font-semibold shadow-[0_5px_15px_rgba(236,72,153,0.5)] transition-all duration-300 transform hover:-translate-y-1 hover:shadow-[0_10px_25px_rgba(236,72,153,0.6)] flex items-center justify-center space-x-2">
        <i class="fas fa-paper-plane"></i>
        <span>Send whatsapp</span>

         <button id="sendSMS" 
        class="bg-gradient-to-r from-pink-400 to-indigo-500 hover:from-pink-500 hover:to-indigo-600 text-white px-5 py-3 rounded-xl font-semibold shadow-[0_5px_15px_rgba(236,72,153,0.5)] transition-all duration-300 transform hover:-translate-y-1 hover:shadow-[0_10px_25px_rgba(236,72,153,0.6)] flex items-center justify-center space-x-2">
        <i class="fas fa-paper-plane"></i>
        <span>Send SMS</span>


      </div>



  </div>
</div>

<script>
const whatsappBtn = document.getElementById('whatsappBtn');
const whatsappChat = document.getElementById('whatsappChat');
const closeWhatsapp = document.getElementById('closeWhatsapp');
const sendWhatsapp = document.getElementById('sendWhatsapp');
const sendSMS = document.getElementById('sendSMS');
const whatsappMessage = document.getElementById('whatsappMessage');
const whatsappWidget = document.getElementById('whatsappWidget');
const whatsappHeader = document.getElementById('whatsappHeader');

// Toggle chat box
whatsappBtn.addEventListener('click', () => {
  if (whatsappChat.classList.contains('hidden')) {
    whatsappChat.classList.remove('hidden');
    whatsappChat.style.bottom = '60px';
    whatsappChat.style.right = '0px';
    setTimeout(() => {
      whatsappChat.classList.remove('scale-95', 'opacity-0');
      whatsappMessage.focus();
    }, 20);
  } else {
    whatsappChat.classList.add('scale-95', 'opacity-0');
    setTimeout(() => whatsappChat.classList.add('hidden'), 300);
  }
});

closeWhatsapp.addEventListener('click', () => {
  whatsappChat.classList.add('scale-95', 'opacity-0');
  setTimeout(() => whatsappChat.classList.add('hidden'), 300);
});

// Send WhatsApp message
sendWhatsapp.addEventListener('click', () => {
  const message = encodeURIComponent(whatsappMessage.value.trim());
  if(message) {
    const number = "254728512780";
    const url = `https://wa.me/${number}?text=${message}`;
    window.open(url, '_blank');
    whatsappMessage.value = '';
    whatsappChat.classList.add('scale-95', 'opacity-0');
    setTimeout(() => whatsappChat.classList.add('hidden'), 300);
  } else {
    alert("Please type a message first!");
  }
});

// Send SMS with typed message
sendSMS.addEventListener('click', () => {
  const message = encodeURIComponent(whatsappMessage.value.trim());
  if(message) {
    const number = "+254726781724";
    const url = `sms:${number}?body=${message}`;
    window.open(url, '_blank');
    whatsappMessage.value = '';
    whatsappChat.classList.add('scale-95', 'opacity-0');
    setTimeout(() => whatsappChat.classList.add('hidden'), 300);
  } else {
    alert("Please type a message first!");
  }
});

// Click outside to close
document.addEventListener('click', (e) => {
  if (!whatsappWidget.contains(e.target) && !whatsappChat.classList.contains('hidden')) {
    whatsappChat.classList.add('scale-95', 'opacity-0');
    setTimeout(() => whatsappChat.classList.add('hidden'), 300);
  }
});

// Drag functionality
let isDragging = false, offsetX = 0, offsetY = 0;

whatsappHeader.addEventListener('mousedown', (e) => {
  isDragging = true;
  const rect = whatsappChat.getBoundingClientRect();
  offsetX = e.clientX - rect.left;
  offsetY = e.clientY - rect.top;
  whatsappChat.style.position = 'fixed';
  whatsappChat.style.margin = '0';
  whatsappChat.style.zIndex = '1000';
});
document.addEventListener('mousemove', (e) => {
  if (isDragging) {
    let x = e.clientX - offsetX;
    let y = e.clientY - offsetY;
    whatsappChat.style.left = `${x}px`;
    whatsappChat.style.top = `${y}px`;
  }
});
document.addEventListener('mouseup', () => { isDragging = false; });

// Touch support
whatsappHeader.addEventListener('touchstart', (e) => {
  isDragging = true;
  const rect = whatsappChat.getBoundingClientRect();
  offsetX = e.touches[0].clientX - rect.left;
  offsetY = e.touches[0].clientY - rect.top;
  whatsappChat.style.position = 'fixed';
  whatsappChat.style.margin = '0';
  whatsappChat.style.zIndex = '1000';
});
document.addEventListener('touchmove', (e) => {
  if (isDragging) {
    let x = e.touches[0].clientX - offsetX;
    let y = e.touches[0].clientY - offsetY;
    whatsappChat.style.left = `${x}px`;
    whatsappChat.style.top = `${y}px`;
  }
});
document.addEventListener('touchend', () => { isDragging = false; });
</script>
