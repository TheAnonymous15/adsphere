<?php
/********************************************
 * categories.php
 * Creates ad categories as folders inside
 * /app/includes/ads/
 ********************************************/

// path where categories are stored
$adsBase = __DIR__ . "/../companies/data/";

// ensure ads directory exists
if (!is_dir($adsBase)) {
    mkdir($adsBase, 0775, true);
}

$created = [];
$skipped = [];

// if submitted
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['categories'])) {

    // get input text
    $input = $_POST['categories'];

    // break by comma OR space OR newline
    $categories = preg_split('/[\s,]+/', $input);

    foreach ($categories as $category) {

        $category = strtolower(trim($category));

        if ($category === "") continue;

        // clean/sanitize folder names
        $category = preg_replace("/[^a-z0-9\-]/", "", str_replace(" ", "-", $category));

        $dir = $adsBase . $category;

        if (!is_dir($dir)) {
            mkdir($dir, 0775, true);
            $created[] = $category;
        } else {
            $skipped[] = $category;
        }
    }
}

// get existing categories
$existingCategories = array_filter(scandir($adsBase), function($item) use ($adsBase) {
    return $item !== "." && $item !== ".." && is_dir($adsBase . $item);
});

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Ad Categories Manager</title>

    <script src="/app/assets/css/tailwind.js"></script>
    <link rel="stylesheet" href="/app/assets/css/all.min.css">
</head>

<body class="bg-slate-900 text-white p-6">

    <div class="max-w-2xl mx-auto bg-white/10 p-6 rounded-xl shadow-xl backdrop-blur">

        <h1 class="text-2xl font-bold mb-4">Create Ad Categories</h1>

        <?php if (!empty($created)) : ?>
            <div class="mb-4 p-3 rounded bg-green-600/30 text-green-200">
                Created: <?= implode(", ", $created) ?>
            </div>
        <?php endif; ?>

        <?php if (!empty($skipped)) : ?>
            <div class="mb-4 p-3 rounded bg-yellow-500/30 text-yellow-200">
                Already existed: <?= implode(", ", $skipped) ?>
            </div>
        <?php endif; ?>

        <form method="post" class="flex flex-col gap-3 mb-6">

            <label class="font-semibold">Enter categories</label>

            <textarea name="categories"
                      required
                      rows="4"
                      class="px-4 py-2 text-black rounded"
                      placeholder="Example: food, tech, travel, sports"></textarea>

            <button class="px-4 py-2 bg-indigo-500 rounded hover:bg-indigo-600 transition">
                Add Categories
            </button>
        </form>

        <h2 class="text-xl font-semibold mt-4 mb-2">Existing Categories</h2>

        <?php if (empty($existingCategories)) : ?>
            <p class="text-white/50">No categories yet.</p>
        <?php else : ?>
            <ul class="list-disc ml-5 text-white/90">
                <?php foreach ($existingCategories as $cat) : ?>
                    <li><?= htmlspecialchars($cat) ?></li>
                <?php endforeach; ?>
            </ul>
        <?php endif; ?>

    </div>

</body>
</html>
