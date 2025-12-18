<?php
session_start();

// block unauthorized
if(!isset($_SESSION['company'])) {
    header("Location: login.php");
    exit();
}

$company = $_SESSION['company'];
?>

<!DOCTYPE html>
<html>
<head>
<title>Dashboard – AdSphere</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@3.4.1/dist/tailwind.min.css" rel="stylesheet">
</head>

<body class="bg-gray-900 text-white">

<!-- NAVBAR -->
<nav class="bg-gray-800 p-4 flex justify-between">
    <div class="font-bold text-xl">AdSphere Dashboard</div>

    <div class="flex gap-4">
        <a class="hover:text-yellow-400" href="#">Profile</a>
        <a class="hover:text-yellow-400" href="logout.php">Logout</a>
    </div>
</nav>


<div class="max-w-7xl mx-auto p-4">

    <!-- HEADER -->
    <h1 class="text-3xl font-bold">Welcome, <?= htmlspecialchars($company) ?></h1>
    <p class="text-gray-400">Manage and track performance of your ads.</p>


    <!-- ACTION BUTTONS -->
    <div class="mt-6 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">

        <a href="upload_ad.php"
           class="bg-blue-600 hover:bg-blue-700 p-4 text-center rounded-xl">
            ➕ Post New Ad
        </a>

        <a href="my_ads.php"
           class="bg-green-600 hover:bg-green-700 p-4 text-center rounded-xl">
            📌 My Ads
        </a>

        <a href="#liked"
           class="bg-purple-600 hover:bg-purple-700 p-4 text-center rounded-xl">
            ❤️ Most Liked Ads
        </a>

        <a href="#stats"
           class="bg-yellow-600 hover:bg-yellow-700 p-4 text-center rounded-xl">
            📊 Analytics
        </a>

        <a href="#settings"
           class="bg-gray-700 hover:bg-gray-800 p-4 text-center rounded-xl">
            ⚙ Settings
        </a>

    </div>



    <!-- MY ADS SECTION -->
    <section class="mt-10" id="myAds">
        <h2 class="text-2xl font-bold border-b border-gray-700 pb-2">Your Ads</h2>

        <div id="myAdsContainer" class="mt-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-black">
            <!-- JS will load ads here via API -->
        </div>
    </section>



    <!-- MOST LIKED SECTION -->
    <section class="mt-12" id="liked">
        <h2 class="text-2xl font-bold border-b border-gray-700 pb-2">Most Liked Ads</h2>

        <div id="likedAdsContainer" class="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-black">
        </div>
    </section>



    <!-- ANALYTICS -->
    <section class="mt-12" id="stats">
        <h2 class="text-2xl font-bold border-b border-gray-700 pb-2">Analytics</h2>

        <p class="text-gray-400 mt-4">Charts and stats coming soon…</p>
    </section>


</div>



<script>
//
// Fetch and render ads from backend
//
async function loadMyAds() {
    const res = await fetch("/app/includes/ads.php"); // returns all ads JSON
    const ads = await res.json();

    const mine = ads.filter(a => a.company === "<?= $company ?>");

    let html = "";
    mine.forEach(ad => {
        html += `
            <div class="bg-white rounded-xl overflow-hidden shadow-md">
                <img src="${ad.media}" class="w-full h-40 object-cover">

                <div class="p-3">
                    <h3 class="font-bold text-lg">${ad.title}</h3>
                    <p class="text-sm text-gray-700">${ad.description}</p>

                    <div class="mt-3 text-xs text-gray-500">
                        ${new Date(ad.timestamp * 1000).toLocaleString()}
                    </div>
                </div>
            </div>
        `;
    });

    document.getElementById("myAdsContainer").innerHTML = html;
}

loadMyAds();
</script>


</body>
</html>
