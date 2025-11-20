<?php
$navLinks = [
    ['title' => 'Home', 'href' => '/index.php', 'slug' => 'home'],
    ['title' => 'About', 'href' => '/includes/about.php', 'slug' => 'about'],
    ['title' => 'Gallery', 'href' => '/gallery.php', 'slug' => 'gallery'],
    ['title' => 'Contact', 'href' => '/includes/contact.php', 'slug' => 'contact']
];

$products = [
    ['title' => 'R290 All-in-one heat pump', 'href' => '/r290-all-in-one-heat-pump.php', 'slug' => 'r290'],
    ['title' => 'R410a residential hot water heat pump', 'href' => '/r410a-residential-hot-water-heat-pump.php', 'slug' => 'r410a-res'],
    ['title' => 'R410a commercial hot water heat pump', 'href' => '/r410a-commercial-hot-water-heat-pump.php', 'slug' => 'r410a-com'],
    ['title' => 'R32 DC Inverter pool heat pump', 'href' => '/r32-dc-inverter-pool-heat-pump.php', 'slug' => 'r32'],
    ['title' => 'R410a commercial pool heat pump', 'href' => '/r410a-commercial-pool-heat-pump.php', 'slug' => 'r410a-com-pool']
];
?>

<footer class="bg-emerald-950 text-gray-300 py-12 relative overflow-hidden">
  <div class="absolute inset-0 bg-gradient-to-t from-emerald-900 via-emerald-950 to-emerald-900 opacity-20"></div>

  <!-- Desktop: 4 columns -->
  <div class="hidden md:flex relative max-w-7xl mx-auto px-6 justify-between items-start gap-8">

    <!-- Column 1: About -->
    <div class="flex-1 space-y-4 text-left">
      <img src="../resources/images/logo.png" alt="Ecotherm Africa Logo" class="h-14 drop-shadow-lg">
      <p class="text-gray-200 text-sm leading-relaxed font-medium">
        At <span class="text-emerald-400 font-bold">Ecotherm Africa</span>, we deliver
        <span class="text-emerald-400">cutting-edge</span> and
        <span class="text-emerald-400">high-efficiency</span> hot water solutions across Africa — combining
        <span class="text-emerald-400">innovation</span> and
        <span class="text-emerald-400">sustainability</span>.
      </p>
    </div>

    <!-- Column 2: Quick Links -->
    <div class="flex-1 space-y-4 text-left">
      <h3 class="text-white font-semibold text-lg">Quick Links</h3>
      <ul class="mt-2 space-y-2">
        <?php foreach ($navLinks as $link): ?>
          <li>
            <a href="<?= $link['href'] ?>" class="hover:text-emerald-400 transition-colors duration-300 block">
              <?= $link['title'] ?>
            </a>
          </li>
        <?php endforeach; ?>
      </ul>
    </div>

    <!-- Column 3: Our Products -->
    <div class="flex-1 space-y-4 text-left">
      <h3 class="text-white font-semibold text-lg">Our Products</h3>
      <ul class="mt-2 space-y-2">
        <?php foreach ($products as $item): ?>
          <li>
            <a href="<?= $item['href'] ?>" class="hover:text-emerald-400 transition-colors duration-300 block">
              <?= $item['title'] ?>
            </a>
          </li>
        <?php endforeach; ?>
      </ul>
    </div>

    <!-- Column 4: Contact -->
    <div class="flex-1 space-y-4 text-left">
      <h3 class="text-white font-semibold text-lg">Contact Us</h3>
      <p class="flex items-center space-x-2 text-gray-200">
        <i class="fas fa-phone-alt text-emerald-400"></i> <span>+254 728 512 780</span>
      </p>
      <p class="flex items-center space-x-2 text-gray-200">
        <i class="fas fa-envelope text-emerald-400"></i> <span>info@ecothermafrica.com</span>
      </p>
      <p class="flex items-center space-x-2 text-gray-200">
        <i class="fas fa-map-marker-alt text-emerald-400"></i> <span>Nairobi, Kenya</span>
      </p>
      <div class="flex space-x-4 pt-3 text-xl">
        <a href="https://linkedin.com/company/ecothermafrica" target="_blank" class="hover:text-emerald-400"><i class="fab fa-linkedin"></i></a>
        <a href="https://facebook.com/ecothermafrica" target="_blank" class="hover:text-emerald-400"><i class="fab fa-facebook"></i></a>
        <a href="https://instagram.com/ecothermafrica" target="_blank" class="hover:text-emerald-400"><i class="fab fa-instagram"></i></a>
      </div>
    </div>

  </div>

  <!-- Mobile: Accordion -->
  <div class="md:hidden relative max-w-7xl mx-auto px-6 flex flex-col gap-4">
    <?php
      $mobileSections = [
          'About' => '<p class="text-gray-200 text-sm leading-relaxed font-medium">At <span class="text-emerald-400 font-bold">Ecotherm Africa</span>, we deliver <span class="text-emerald-400">cutting-edge</span> and <span class="text-emerald-400">high-efficiency</span> hot water solutions across Africa — combining <span class="text-emerald-400">innovation</span> and <span class="text-emerald-400">sustainability</span>.</p>',
          'Quick Links' => function() use($navLinks) {
              $html = '<ul class="space-y-2 mt-2">';
              foreach($navLinks as $link) {
                  $html .= '<li><a href="'.$link['href'].'" class="hover:text-emerald-400 block transition-colors duration-300">'.$link['title'].'</a></li>';
              }
              $html .= '</ul>';
              return $html;
          },
          'Our Products' => function() use($products) {
              $html = '<ul class="space-y-2 mt-2">';
              foreach($products as $item) {
                  $html .= '<li><a href="'.$item['href'].'" class="hover:text-emerald-400 block transition-colors duration-300">'.$item['title'].'</a></li>';
              }
              $html .= '</ul>';
              return $html;
          },
          'Contact Us' => '<p class="flex items-center space-x-2 text-gray-200"><i class="fas fa-phone-alt text-emerald-400"></i> +254 728 512 780</p>
                          <p class="flex items-center space-x-2 text-gray-200"><i class="fas fa-envelope text-emerald-400"></i> info@ecothermafrica.com</p>
                          <p class="flex items-center space-x-2 text-gray-200"><i class="fas fa-map-marker-alt text-emerald-400"></i> Nairobi, Kenya</p>
                          <div class="flex space-x-4 pt-3 text-xl">
                            <a href="https://linkedin.com/company/ecothermafrica" target="_blank" class="hover:text-emerald-400"><i class="fab fa-linkedin"></i></a>
                            <a href="https://facebook.com/ecothermafrica" target="_blank" class="hover:text-emerald-400"><i class="fab fa-facebook"></i></a>
                            <a href="https://instagram.com/ecothermafrica" target="_blank" class="hover:text-emerald-400"><i class="fab fa-instagram"></i></a>
                          </div>'
      ];
    ?>

    <?php foreach($mobileSections as $title => $content): ?>
      <div class="border-t border-emerald-700">
        <button class="w-full text-left py-3 flex justify-between items-center text-white font-semibold text-lg accordion-btn">
          <?= $title ?>
          <span class="transition-transform duration-300">+</span>
        </button>
        <div class="accordion-content max-h-0 overflow-hidden transition-all duration-500">
          <div class="pt-2">
            <?= is_callable($content) ? $content() : $content ?>
          </div>
        </div>
      </div>
    <?php endforeach; ?>
  </div>

  <div class="border-t border-emerald-700 mt-8 pt-4 text-center text-gray-500 text-sm">
    &copy; <span id="footerYear"></span> Ecotherm Africa. All rights reserved.
  </div>

  <script>
    document.getElementById('footerYear').textContent = new Date().getFullYear();

    // Accordion functionality
    const accordions = document.querySelectorAll('.accordion-btn');
    accordions.forEach(btn => {
      btn.addEventListener('click', () => {
        const content = btn.nextElementSibling;
        const open = content.style.maxHeight && content.style.maxHeight !== "0px";
        // Close all other accordions
        document.querySelectorAll('.accordion-content').forEach(c => c.style.maxHeight = null);
        if(!open){
          content.style.maxHeight = content.scrollHeight + "px";
        }
      });
    });
  </script>
</footer>
