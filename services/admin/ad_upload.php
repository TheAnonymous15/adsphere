<?php
/********************************************
 * ad_upload.php - secure new version
 ********************************************/
session_start();

// if (!isset($_SESSION["logged_in"])) {
//     header("Location: login.php");
//     exit;
// }

$loggedCompany = $_SESSION["company"]; // slug of company

$adsBase = __DIR__ . "/../data/";
$metaBase = __DIR__ . "/../metadata/";

// load company metadata with contact info
$metaFile = "$metaBase/$loggedCompany.json";
$contactInfo = [];

if (file_exists($metaFile)) {
    $rawMeta = file_get_contents($metaFile);
    $meta = json_decode($rawMeta, true);
    $contactInfo = $meta["contact"] ?? [];
}

// discover only assigned categories
$categories = [];
foreach (scandir($adsBase) as $cat) {
    if ($cat === "." || $cat === "..") continue;
    if (is_dir("$adsBase/$cat/$loggedCompany")) {
        $categories[] = $cat;
    }
}

// generate UUID
function generate_ad_id(){
    $micro = microtime(true);

    $d = new DateTime();
    $d->setTimestamp((int)$micro);

    $Y = $d->format("Y");
    $m = $d->format("m");

    $time = $d->format("His") . substr((string)$micro, -4);

    $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
    $rand = "";

    for($i=0;$i<5;$i++){
        $rand .= $chars[random_int(0, strlen($chars)-1)];
    }

    return "AD-$Y$m-$time-$rand";
}

$msg = "";

/******************************
 * HANDLE FORM POST
 ******************************/
if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    $category = $_POST['category'] ?? null;
    $title = trim($_POST['title']);
    $description = trim($_POST['description']);

    if (!$category || !$title) {
        $msg = "Missing required fields.";
    } else if (!empty($_FILES["media"]["name"])) {

        $adId = generate_ad_id();

        $ext = pathinfo($_FILES["media"]["name"], PATHINFO_EXTENSION);
        $mediaName = $adId . "." . $ext;

        $adDir = "$adsBase/$category/$loggedCompany/$adId";

        if (!is_dir($adDir)) mkdir($adDir, 0775, true);

        $destPath = "$adDir/$mediaName";

        if (move_uploaded_file($_FILES["media"]["tmp_name"], $destPath)) {

            $jsonData = [
                "ad_id" => $adId,
                "title" => $title,
                "description" => $description,
                "category" => $category,
                "company" => $loggedCompany,
                "media" => $mediaName,
                "timestamp" => microtime(true),
                "contact" => [
                    "phone" => $contactInfo["phone"] ?? null,
                    "sms" => $contactInfo["sms"] ?? null,
                    "email" => $contactInfo["email"] ?? null,
                    "whatsapp" => $contactInfo["whatsapp"] ?? null
                ]
            ];

            file_put_contents("$adDir/meta.json", json_encode($jsonData, JSON_PRETTY_PRINT));

            $msg = "Ad uploaded successfully!";
        } else {
            $msg = "Upload failed!";
        }
    }
}

?>
<!DOCTYPE html>
<html>
<head>
    <title>Upload Ad</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="/services/assets/css/all.min.css">
</head>

<body class="bg-slate-900 text-white p-6">

<div class="max-w-xl mx-auto bg-white/10 p-6 rounded-xl shadow-xl backdrop-blur">

    <h1 class="text-xl font-bold mb-4">Upload New Ad</h1>

    <p class="mb-3 text-green-300">Logged in as: <strong><?= $loggedCompany ?></strong> 
        | <a href="/logout" class="underline text-indigo-400">Logout</a>
    </p>

    <?php if ($msg): ?>
        <div class="p-3 bg-green-500/30 mb-3 rounded"><?= $msg ?></div>
    <?php endif; ?>


<?php if (empty($categories)): ?>
    <p class="text-yellow-300">
        You have no assigned categories. Contact admin.
    </p>

<?php else: ?>

    <form method="POST" enctype="multipart/form-data" class="flex flex-col gap-3">

        <label>Select Category</label>
        <select name="category" class="text-black p-2 rounded" required>
            <?php foreach ($categories as $cat): ?>
                <option value="<?= htmlspecialchars($cat) ?>"><?= htmlspecialchars($cat) ?></option>
            <?php endforeach; ?>
        </select>

        <label>Ad Title</label>
        <input name="title" class="text-black p-2 rounded" required>

        <label>Description</label>
        <textarea name="description" class="text-black p-2 rounded" rows="3" required></textarea>

        <label>Select Media</label>
        <input type="file" name="media" accept="image/*,video/*,audio/*" required>

        <button class="p-2 mt-2 bg-indigo-500 rounded hover:bg-indigo-600 transition">
            Upload
        </button>
    
    </form>

<?php endif; ?>

</div>

</body>
</html>
