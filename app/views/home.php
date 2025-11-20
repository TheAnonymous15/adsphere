<div class="text-center">
    <h1 class="text-5xl font-bold text-white"><?= htmlspecialchars($data['welcomeMessage'] ?? 'Hello!') ?></h1>
    <ul class="mt-6 text-white/80">
        <?php foreach ($data['featuredProducts'] ?? [] as $product): ?>
            <li class="mt-2"><?= htmlspecialchars($product) ?></li>
        <?php endforeach; ?>
    </ul>
</div>
