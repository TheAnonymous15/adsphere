<?php
/********************************************
 * ad_upload.php
 * Upload ads for companies
 * Creates ad folder + JSON description
 ********************************************/

$adsBase = __DIR__ . "/../companies/data/";

// load categories
$categories = array_filter(scandir($adsBase), function($item) use ($adsBase){
    return $item !== "." && $item !== ".." && is_dir($adsBase . $item);
});


$msg = "";

if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    $category = $_POST['category'];
    $company = $_POST['company'];
    $title = trim($_POST['title']);
    $description = trim($_POST['description']);

    if (!empty($_FILES['media']['name'])) {

        $mediaName = basename($_FILES['media']['name']);
        $adName = strtolower(str_replace(" ","-", $title));

        $adDir = "$adsBase/$category/$company/$adName";

        if (!is_dir($adDir)) mkdir($adDir, 0775, true);

        $destPath = "$adDir/" . $mediaName;

        if (move_uploaded_file($_FILES['media']['tmp_name'], $destPath)) {

            $jsonData = [
                "title" => $title,
                "description" => $description,
                "category" => $category,
                "company" => $company,
                "media" => $mediaName,
                "timestamp" => time()
            ];

            file_put_contents("$adDir/meta.json", json_encode($jsonData, JSON_PRETTY_PRINT));

            $msg = "Ad uploaded successfully.";
        } else {
            $msg = "Upload failed!";
        }
    }
}


// when category selected: fetch company folders
$companies = [];
if (!empty($_GET['cat'])) {
    $catDir = $adsBase . $_GET['cat'];
    $companies = array_filter(scandir($catDir), function($item) use ($catDir){
        return $item !== "." && $item !== ".." && is_dir($catDir . "/" . $item);
    });
}

?>

<!DOCTYPE html>
<html>
<head>
    <title>Upload Ad</title>
    <script src="/app/assets/css/tailwind.js"></script>
    <link rel="stylesheet" href="/app/assets/css/all.min.css">
</head>

<body class="bg-slate-900 text-white p-6">

<div class="max-w-xl mx-auto bg-white/10 p-6 rounded-xl shadow-xl backdrop-blur">

    <h1 class="text-xl font-bold mb-4">Upload New Ad</h1>

    <?php if ($msg): ?>
        <div class="p-3 bg-green-500/30 mb-3 rounded"><?= $msg ?></div>
    <?php endif; ?>


    <form method="GET" class="mb-4">
        <label>Select Category</label>
        <select name="cat" class="text-black p-2 rounded" onchange="this.form.submit()">
            <option disabled selected>Choose...</option>
            <?php foreach ($categories as $cat): ?>
                <option value="<?= $cat ?>"><?= $cat ?></option>
            <?php endforeach; ?>
        </select>
    </form>


<?php if (!empty($_GET['cat'])): ?>

    <form method="POST" enctype="multipart/form-data" class="flex flex-col gap-3">

        <input type="hidden" name="category" value="<?= $_GET['cat'] ?>">

        <label>Select Company</label>
        <select name="company" class="p-2 text-black rounded">
            <?php foreach ($companies as $comp): ?>
                <option value="<?= $comp ?>"><?= $comp ?></option>
            <?php endforeach; ?>
        </select>

        <label>Ad Title</label>
        <input name="title" class="text-black p-2 rounded" required>

        <label>Description</label>
        <textarea name="description" class="text-black p-2 rounded" rows="3" required></textarea>

        <label>Upload Media</label>
        <input type="file" name="media" accept="image/*,video/*,audio/*" required>

        <button class="p-2 mt-2 bg-indigo-500 rounded hover:bg-indigo-600 transition">
            Upload Ad
        </button>
    
    </form>

<?php endif; ?>

</div>

</body>
</html>
