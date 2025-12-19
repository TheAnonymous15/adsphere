<?php
/********************************************
 * ad_upload.php - secure new version
 ********************************************/
session_start();

if (!isset($_SESSION["logged_in"])) {
    header("Location: login.php");
    exit;
}

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
    <script src="/app/assets/css/tailwind.js"></script>
    <link rel="stylesheet" href="/app/assets/css/all.min.css">
</head>

<body class="bg-slate-900 text-white p-6">

<div class="max-w-xl mx-auto bg-white/10 p-6 rounded-xl shadow-xl backdrop-blur">

    <h1 class="text-xl font-bold mb-4">Upload New Ad</h1>

    <p class="mb-3 text-green-300">Logged in as: <strong><?= $loggedCompany ?></strong> 
        | <a href="logout.php" class="underline text-indigo-400">Logout</a>
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

        <label class="flex items-center justify-between">
            <span>Ad Title</span>
            <button type="button" onclick="generateAIContent('title')" class="text-xs px-3 py-1 bg-purple-600 hover:bg-purple-700 rounded-full transition flex items-center gap-1">
                <i class="fas fa-magic"></i>
                AI Generate
            </button>
        </label>
        <input id="titleInput" name="title" class="text-black p-2 rounded" required>

        <label class="flex items-center justify-between">
            <span>Description</span>
            <button type="button" onclick="generateAIContent('description')" class="text-xs px-3 py-1 bg-purple-600 hover:bg-purple-700 rounded-full transition flex items-center gap-1">
                <i class="fas fa-magic"></i>
                AI Generate
            </button>
        </label>
        <textarea id="descriptionInput" name="description" class="text-black p-2 rounded" rows="3" required></textarea>

        <!-- AI Generation Status -->
        <div id="aiStatus" class="hidden p-3 rounded-lg bg-purple-600/20 border border-purple-600 text-sm flex items-center gap-2">
            <i class="fas fa-spinner fa-spin"></i>
            <span id="aiStatusText">Generating with AI...</span>
        </div>

        <label>Select Media</label>
        <input type="file" name="media" accept="image/*,video/*,audio/*" required>

        <button class="p-2 mt-2 bg-indigo-500 rounded hover:bg-indigo-600 transition">
            Upload
        </button>
    
    </form>

<?php endif; ?>

</div>

<script>
// AI Content Generator
async function generateAIContent(type) {
    const category = document.querySelector('select[name="category"]').value;
    const titleInput = document.getElementById('titleInput');
    const descriptionInput = document.getElementById('descriptionInput');
    const aiStatus = document.getElementById('aiStatus');
    const aiStatusText = document.getElementById('aiStatusText');

    if (!category) {
        alert('Please select a category first');
        return;
    }

    // Show loading status
    aiStatus.classList.remove('hidden');
    aiStatusText.textContent = 'AI is generating content...';

    try {
        // For demo purposes, generate content locally
        // In production, call OpenAI API or your AI service

        const templates = {
            title: {
                food: [
                    'Fresh {item} - Best Quality Available!',
                    'Delicious {item} Delivered Fresh Daily',
                    'Premium {item} at Unbeatable Prices',
                    'Authentic {item} - Order Now!'
                ],
                electronics: [
                    'Latest {item} - Brand New in Box',
                    '{item} - Warranty Included, Free Delivery',
                    'High-Quality {item} - Limited Stock',
                    'Premium {item} at Best Price'
                ],
                housing: [
                    'Beautiful {item} - Prime Location',
                    'Spacious {item} - Move-In Ready',
                    'Luxury {item} - Excellent Amenities',
                    'Affordable {item} - Don\'t Miss Out!'
                ]
            },
            description: {
                food: [
                    'Experience the finest quality {category} products. Sourced fresh daily from trusted suppliers. Perfect for your family meals. Order now and enjoy fast delivery to your doorstep. Limited stock available!',
                    'Premium {category} at affordable prices. We guarantee freshness and quality. Same-day delivery available in selected areas. Contact us now to place your order!',
                    'Fresh, organic {category} delivered straight to your home. Supporting local farmers. Eco-friendly packaging. Order today and taste the difference!'
                ],
                electronics: [
                    'Brand new {category} with full warranty and accessories. Genuine products only. Fast shipping available. Contact us for more details and special offers. Limited stock!',
                    'Latest {category} at competitive prices. Warranty included. Free technical support. Nationwide delivery available. Order now while stocks last!',
                    'High-quality {category} from trusted brands. Excellent condition. All accessories included. Flexible payment options available. Contact us today!'
                ],
                housing: [
                    'Prime {category} in excellent location. Close to amenities, schools, and transport. Modern facilities. Well-maintained. Schedule viewing today!',
                    'Beautiful {category} ready for immediate occupancy. Spacious rooms, ample parking. Secure neighborhood. Don\'t miss this opportunity!',
                    'Luxurious {category} with stunning features. Recently renovated. Prime location. Excellent value. Contact us for viewing!'
                ]
            }
        };

        // Get random template
        const categoryTemplates = templates[type][category] || templates[type]['food'];
        const template = categoryTemplates[Math.floor(Math.random() * categoryTemplates.length)];

        // Replace placeholders
        const content = template
            .replace('{item}', category.charAt(0).toUpperCase() + category.slice(1))
            .replace('{category}', category);

        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Set content
        if (type === 'title') {
            titleInput.value = content;
            aiStatusText.textContent = '✨ Title generated successfully!';
        } else {
            descriptionInput.value = content;
            aiStatusText.textContent = '✨ Description generated successfully!';
        }

        // Hide status after 3 seconds
        setTimeout(() => {
            aiStatus.classList.add('hidden');
        }, 3000);

    } catch (error) {
        console.error('AI generation error:', error);
        aiStatusText.textContent = '❌ Failed to generate content. Try again.';
        setTimeout(() => {
            aiStatus.classList.add('hidden');
        }, 3000);
    }
}

// Add shimmer animation
const style = document.createElement('style');
style.textContent = `
    @keyframes shimmer {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    .fa-spinner {
        animation: shimmer 1.5s infinite;
    }
`;
document.head.appendChild(style);
</script>

</body>
</html>
