<?php
$adsBase = __DIR__ . "/../companies/data/";

// load categories
$categories = array_filter(scandir($adsBase), function($item) use ($adsBase){
    return $item !== "." && $item !== ".." && is_dir($adsBase.$item);
});
?>

<!DOCTYPE html>
<html>
<head>
    <title>Register Company</title>
    <script src="/app/assets/css/tailwind.js"></script>
</head>

<body class="bg-slate-900 text-white min-h-screen p-6">

<div class="max-w-3xl mx-auto bg-white/10 p-8 rounded-xl shadow-xl">

    <h1 class="text-3xl font-bold mb-6 text-indigo-300">Register Advertiser</h1>



    <form id="companyForm" class="flex flex-col gap-6">

        <!-- COMPANY DETAILS -->
        <section class="border border-white/10 rounded-lg p-5 bg-black/20">
            <h2 class="text-xl font-bold mb-3 text-indigo-300">Company Details</h2>

            <input name="company_name" required placeholder="Company name"
                class="text-black px-3 py-2 rounded w-full mb-2">

            <input name="website" placeholder="Website URL"
                class="text-black px-3 py-2 rounded w-full mb-2">

            <textarea name="description" rows="3" placeholder="Description"
                class="text-black px-3 py-2 rounded w-full"></textarea>
        </section>

        <!-- CONTACT -->
        <section class="border border-white/10 rounded-lg p-5 bg-black/20">
            <h2 class="text-xl font-bold mb-3 text-indigo-300">Contact Details</h2>

            <input name="phone" placeholder="Phone"
                class="text-black px-3 py-2 rounded w-full mb-2">

            <input name="sms" placeholder="SMS"
                class="text-black px-3 py-2 rounded w-full mb-2">

            <input name="email" placeholder="Email"
                class="text-black px-3 py-2 rounded w-full mb-2">

            <input name="whatsapp" placeholder="Whatsapp"
                class="text-black px-3 py-2 rounded w-full">
        </section>

        <!-- PROMOTIONS -->
        <section class="border border-white/10 rounded-lg p-5 bg-black/20">
            <h2 class="text-xl font-bold mb-3 text-indigo-300">Promotion Options</h2>

            <label class="flex gap-2 items-center mb-2">
                <input type="checkbox" name="promo_social">
                Promote on our social media
            </label>

            <label class="flex gap-2 items-center">
                <input type="checkbox" name="promo_featured">
                Allow featured ads
            </label>
        </section>





        <section class="border border-white/10 rounded-lg p-5 bg-black/20">
            <h2 class="text-xl font-bold mb-3 text-indigo-300">Categories</h2>

            <div class="grid grid-cols-2 gap-2 text-black">
                <?php foreach ($categories as $cat): ?>
                <label class="flex gap-2 bg-white px-2 py-1 rounded">
                    <input type="checkbox" name="categories[]" value="<?= $cat ?>">
                    <?= htmlspecialchars($cat) ?>
                </label>
                <?php endforeach; ?>
            </div>
        </section>





        <button
            id="submitBtn"
            class="px-4 py-3 bg-indigo-600 hover:bg-indigo-700 rounded font-bold text-white">
            Register
        </button>

    </form>

    <!-- FEEDBACK MESSAGE -->
    <div id="responseBox"
         class="hidden mt-6 p-4 rounded text-white font-bold text-center">
    </div>

</div>

<script>
document.getElementById("companyForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const submitBtn = document.getElementById("submitBtn");
    const box = document.getElementById("responseBox");

    submitBtn.disabled = true;
    submitBtn.innerText = "Saving...";

    const formData = new FormData(e.target);

    try{
        const res = await fetch("/app/companies/handlers/register_company.php", {
            method:"POST",
            body: formData
        });

        const json = await res.json();

        box.classList.remove("hidden", "bg-green-600", "bg-red-600");

        if(json.success){
            box.classList.add("bg-green-600");
            box.innerHTML = json.message ?? "Success";
            e.target.reset();
        }else{
            box.classList.add("bg-red-600");
            box.innerHTML = json.message ?? "Failed";
        }

    }catch(err){
        box.classList.remove("hidden","bg-green-600");
        box.classList.add("bg-red-600");
        box.innerHTML = "Request failed.";
    }

    submitBtn.disabled = false;
    submitBtn.innerText = "Register";
});
</script>

</body>
</html>
