<?php
/********************************************
 * company_register.php - Hybrid Database System
 * Register new companies with database integration
 ********************************************/

// Load database system
require_once __DIR__ . '/../database/Database.php';

$db = Database::getInstance();
$adsBase = __DIR__ . "/../companies/data/";

// Load categories from database (with caching)
$categoriesCache = $db->cacheGet('all_categories');
if ($categoriesCache) {
    $categories = $categoriesCache;
} else {
    $categories = $db->query("SELECT * FROM categories ORDER BY category_name");
    $db->cacheSet('all_categories', $categories, 3600); // Cache for 1 hour
}

// If no categories in database, scan filesystem as fallback
if (empty($categories)) {
    $categoryDirs = array_filter(scandir($adsBase), function($item) use ($adsBase){
        return $item !== "." && $item !== ".." && is_dir($adsBase.$item);
    });

    $categories = [];
    foreach ($categoryDirs as $dir) {
        $categories[] = [
            'category_slug' => $dir,
            'category_name' => ucfirst(str_replace(['-', '_'], ' ', $dir))
        ];
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Register Company - AdSphere</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .animate-slide-in {
            animation: slideIn 0.5s ease-out;
        }

        .glass-effect {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: all 0.3s ease;
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }

        .category-checkbox:checked + label {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
        }

        /* Custom Scrollbar */
        .scrollbar-thin::-webkit-scrollbar {
            width: 8px;
        }

        .scrollbar-thin::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }

        .scrollbar-thin::-webkit-scrollbar-thumb {
            background: #a855f7;
            border-radius: 10px;
        }

        .scrollbar-thin::-webkit-scrollbar-thumb:hover {
            background: #9333ea;
        }

        /* Firefox Scrollbar */
        .scrollbar-thin {
            scrollbar-width: thin;
            scrollbar-color: #a855f7 rgba(255, 255, 255, 0.1);
        }

        /* Category Item Transitions */
        .category-item {
            transition: opacity 0.2s ease, transform 0.2s ease;
        }

        .category-item.hidden {
            display: none;
        }

        .category-item label {
            transition: all 0.2s ease;
        }

        .category-item label:hover {
            transform: scale(1.05);
            box-shadow: 0 4px 12px rgba(168, 85, 247, 0.3);
        }
    </style>
</head>

<body class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen p-6">

<div class="container mx-auto max-w-5xl">

    <!-- Header -->
    <div class="glass-effect rounded-2xl p-6 mb-6 animate-slide-in">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-4xl font-bold text-white flex items-center gap-3">
                    <i class="fas fa-building text-purple-400"></i>
                    Register New Company
                </h1>
                <p class="text-gray-400 mt-2">Create a new advertiser account with category assignments</p>
            </div>
            <div>
                <a href="/dashboard" class="text-purple-400 hover:text-purple-300 transition">
                    <i class="fas fa-arrow-left mr-2"></i>Back to Dashboard
                </a>
            </div>
        </div>
    </div>

    <form id="companyForm" class="space-y-6">

        <!-- COMPANY DETAILS -->
        <section class="glass-effect rounded-2xl p-6 animate-slide-in">
            <h2 class="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                <i class="fas fa-info-circle text-blue-400"></i>
                Company Details
            </h2>

            <div class="grid md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">
                        <i class="fas fa-building mr-2 text-purple-400"></i>Company Name *
                    </label>
                    <input name="company_name" required placeholder="e.g., Acme Corporation"
                        class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 transition">
                </div>

                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">
                        <i class="fas fa-globe mr-2 text-purple-400"></i>Website
                    </label>
                    <input name="website" type="url" placeholder="https://example.com"
                        class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 transition">
                </div>
            </div>

            <div class="mt-4">
                <label class="block text-sm font-semibold text-gray-300 mb-2">
                    <i class="fas fa-align-left mr-2 text-purple-400"></i>Description
                </label>
                <textarea name="description" rows="4" placeholder="Brief description of the company..."
                    class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 transition resize-none"></textarea>
            </div>
        </section>

        <!-- CONTACT DETAILS -->
        <section class="glass-effect rounded-2xl p-6">
            <h2 class="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                <i class="fas fa-address-book text-green-400"></i>
                Contact Information
            </h2>

            <div class="grid md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">
                        <i class="fas fa-phone mr-2 text-green-400"></i>Phone Number
                    </label>
                    <input name="phone" type="tel" placeholder="e.g., 0712345678"
                        class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 transition">
                </div>

                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">
                        <i class="fas fa-sms mr-2 text-green-400"></i>SMS Number
                    </label>
                    <input name="sms" type="tel" placeholder="e.g., 0712345678"
                        class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 transition">
                </div>

                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">
                        <i class="fas fa-envelope mr-2 text-green-400"></i>Email Address
                    </label>
                    <input name="email" type="email" placeholder="e.g., contact@company.com"
                        class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 transition">
                </div>

                <div>
                    <label class="block text-sm font-semibold text-gray-300 mb-2">
                        <i class="fab fa-whatsapp mr-2 text-green-400"></i>WhatsApp Number
                    </label>
                    <input name="whatsapp" type="tel" placeholder="e.g., 0712345678"
                        class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 transition">
                </div>
            </div>
        </section>

        <!-- CATEGORIES -->
        <section class="glass-effect rounded-2xl p-6">
            <div class="flex items-center justify-between mb-4">
                <div>
                    <h2 class="text-2xl font-bold text-white flex items-center gap-2">
                        <i class="fas fa-folder-open text-yellow-400"></i>
                        Select Category *
                    </h2>
                    <p class="text-gray-400 text-sm mt-1">Choose ONE category for this company to advertise in</p>
                </div>
                <div class="text-right">
                    <p class="text-sm text-gray-400">Selected: <span id="selectedCount" class="text-yellow-400 font-bold">None</span></p>
                </div>
            </div>

            <?php if (empty($categories)): ?>
                <div class="bg-yellow-500/20 border border-yellow-500/50 rounded-xl p-4 text-center">
                    <i class="fas fa-exclamation-triangle text-yellow-400 text-2xl mb-2"></i>
                    <p class="text-yellow-300">No categories available. Please create categories first.</p>
                </div>
            <?php else: ?>

                <!-- Search Bar -->
                <div class="mb-4">
                    <div class="relative">
                        <input type="text"
                               id="categorySearch"
                               placeholder="Search categories..."
                               class="w-full bg-white/10 border border-white/20 rounded-xl pl-12 pr-4 py-3 text-white placeholder-gray-500 focus:border-yellow-500 focus:ring-2 focus:ring-yellow-500/50 transition">
                        <i class="fas fa-search absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
                        <span id="searchCount" class="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-gray-400"></span>
                    </div>
                </div>

                <!-- Scrollable Category Grid -->
                <div class="relative">
                    <div id="categoryContainer" class="max-h-96 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-purple-500 scrollbar-track-white/10">
                        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
                            <?php foreach ($categories as $cat): ?>
                                <div class="category-item relative" data-category-name="<?= htmlspecialchars(strtolower($cat['category_name'])) ?>">
                                    <input type="radio"
                                           name="category"
                                           value="<?= htmlspecialchars($cat['category_slug']) ?>"
                                           id="cat_<?= htmlspecialchars($cat['category_slug']) ?>"
                                           class="category-radio hidden peer"
                                           onchange="updateCategorySelection()"
                                           required>
                                    <label for="cat_<?= htmlspecialchars($cat['category_slug']) ?>"
                                           class="block p-3 bg-white/5 border-2 border-white/20 rounded-lg cursor-pointer hover:border-yellow-500 peer-checked:border-yellow-500 peer-checked:bg-yellow-500/20 transition">
                                        <div class="flex items-center gap-2">
                                            <i class="fas fa-tag text-yellow-400 text-sm"></i>
                                            <p class="text-white font-medium text-xs truncate" title="<?= htmlspecialchars($cat['category_name']) ?>">
                                                <?= htmlspecialchars($cat['category_name']) ?>
                                            </p>
                                        </div>
                                    </label>
                                </div>
                            <?php endforeach; ?>
                        </div>
                    </div>

                    <!-- No Results Message -->
                    <div id="noResults" class="hidden text-center py-8 text-gray-400">
                        <i class="fas fa-search text-4xl mb-3 opacity-50"></i>
                        <p>No categories found matching your search</p>
                    </div>

                    <!-- Scroll Indicator -->
                    <div class="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-slate-900 to-transparent pointer-events-none"></div>
                </div>

                <!-- Info -->
                <div class="mt-4 p-3 bg-blue-500/20 border border-blue-500/50 rounded-lg">
                    <p class="text-blue-300 text-xs flex items-start gap-2">
                        <i class="fas fa-info-circle mt-0.5"></i>
                        <span>Search and select ONE category. The company will only be able to upload ads in the selected category. You can change this later if needed.</span>
                    </p>
                </div>
            <?php endif; ?>
        </section>

        <!-- PROMOTIONS -->
        <section class="glass-effect rounded-2xl p-6">
            <h2 class="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                <i class="fas fa-bullhorn text-pink-400"></i>
                Promotion Options
            </h2>

            <div class="space-y-3">
                <label class="flex items-center gap-3 p-4 bg-white/5 border border-white/20 rounded-xl cursor-pointer hover:border-pink-500 transition">
                    <input type="checkbox" name="promo_social" class="w-5 h-5 text-pink-600 bg-white/10 border-white/30 rounded focus:ring-pink-500">
                    <div class="flex-1">
                        <p class="text-white font-semibold">Promote on Social Media</p>
                        <p class="text-gray-400 text-sm">Allow sharing company ads on our social media channels</p>
                    </div>
                    <i class="fas fa-share-alt text-pink-400"></i>
                </label>

                <label class="flex items-center gap-3 p-4 bg-white/5 border border-white/20 rounded-xl cursor-pointer hover:border-pink-500 transition">
                    <input type="checkbox" name="promo_featured" class="w-5 h-5 text-pink-600 bg-white/10 border-white/30 rounded focus:ring-pink-500">
                    <div class="flex-1">
                        <p class="text-white font-semibold">Featured Ads</p>
                        <p class="text-gray-400 text-sm">Allow this company to create featured/promoted ads</p>
                    </div>
                    <i class="fas fa-star text-pink-400"></i>
                </label>
            </div>
        </section>

        <!-- SUBMIT BUTTON -->
        <div class="glass-effect rounded-2xl p-6 flex items-center justify-between">
            <div class="text-gray-400 text-sm">
                <i class="fas fa-shield-alt text-green-400 mr-2"></i>
                All data is securely stored and encrypted
            </div>
            <button type="submit" id="submitBtn"
                    class="btn-primary px-8 py-4 rounded-xl text-white font-bold text-lg shadow-lg hover:shadow-2xl transition flex items-center gap-3">
                <i class="fas fa-check-circle"></i>
                <span>Register Company</span>
            </button>
        </div>

    </form>

    <!-- FEEDBACK MESSAGE -->
    <div id="responseBox" class="hidden mt-6 p-6 rounded-2xl text-white font-bold text-center animate-slide-in">
        <div class="flex items-center justify-center gap-3">
            <i class="fas fa-spinner fa-spin text-2xl" id="loadingIcon"></i>
            <i class="fas fa-check-circle text-2xl hidden" id="successIcon"></i>
            <i class="fas fa-times-circle text-2xl hidden" id="errorIcon"></i>
            <span id="responseText"></span>
        </div>
    </div>

</div>

<script>
// Category Selection Functions (Single Selection)
function updateCategorySelection() {
    const selectedRadio = document.querySelector('input[name="category"]:checked');
    const countSpan = document.getElementById('selectedCount');

    if (selectedRadio) {
        const categoryLabel = document.querySelector(`label[for="${selectedRadio.id}"]`);
        const categoryName = categoryLabel.querySelector('p').textContent.trim();
        countSpan.textContent = categoryName;
        countSpan.classList.add('text-green-400');
        countSpan.classList.remove('text-yellow-400');
    } else {
        countSpan.textContent = 'None';
        countSpan.classList.remove('text-green-400');
        countSpan.classList.add('text-yellow-400');
    }
}

// Category Search Functionality
document.getElementById('categorySearch').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase().trim();
    const categoryItems = document.querySelectorAll('.category-item');
    const noResults = document.getElementById('noResults');
    const searchCount = document.getElementById('searchCount');
    let visibleCount = 0;

    categoryItems.forEach(item => {
        const categoryName = item.dataset.categoryName;

        if (categoryName.includes(searchTerm)) {
            item.classList.remove('hidden');
            visibleCount++;
        } else {
            item.classList.add('hidden');
        }
    });

    // Show/hide no results message
    if (visibleCount === 0) {
        noResults.classList.remove('hidden');
        document.getElementById('categoryContainer').classList.add('hidden');
    } else {
        noResults.classList.add('hidden');
        document.getElementById('categoryContainer').classList.remove('hidden');
    }

    // Update search count
    if (searchTerm) {
        searchCount.textContent = `${visibleCount} found`;
    } else {
        searchCount.textContent = '';
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    updateCategorySelection();
});

// Form Submission Handler
document.getElementById("companyForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const submitBtn = document.getElementById("submitBtn");
    const box = document.getElementById("responseBox");
    const responseText = document.getElementById("responseText");
    const loadingIcon = document.getElementById("loadingIcon");
    const successIcon = document.getElementById("successIcon");
    const errorIcon = document.getElementById("errorIcon");

    // Validate category is selected
    const selectedCategory = document.querySelector('input[name="category"]:checked');
    if (!selectedCategory) {
        box.classList.remove("hidden", "bg-green-600", "bg-blue-600");
        box.classList.add("bg-red-600");
        loadingIcon.classList.add("hidden");
        errorIcon.classList.remove("hidden");
        responseText.innerHTML = "❌ Please select a category";
        return;
    }

    // Disable button and show loading
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i><span>Registering...</span>';

    // Show loading box
    box.classList.remove("hidden", "bg-green-600", "bg-red-600");
    box.classList.add("bg-blue-600");
    loadingIcon.classList.remove("hidden");
    successIcon.classList.add("hidden");
    errorIcon.classList.add("hidden");
    responseText.innerText = "Creating company account...";

    const formData = new FormData(e.target);

    try {
        const res = await fetch("/company/handlers/register_company.php", {
            method: "POST",
            body: formData
        });

        const json = await res.json();

        // Hide loading icon
        loadingIcon.classList.add("hidden");

        box.classList.remove("bg-blue-600");

        if (json.success) {
            box.classList.add("bg-green-600");
            successIcon.classList.remove("hidden");
            responseText.innerHTML = json.message ?? "Company registered successfully!";

            // Reset form after success
            setTimeout(() => {
                e.target.reset();
                updateCategorySelection();
                box.classList.add("hidden");
            }, 3000);
        } else {
            box.classList.add("bg-red-600");
            errorIcon.classList.remove("hidden");
            responseText.innerHTML = json.message ?? "Registration failed. Please try again.";
        }

    } catch (err) {
        loadingIcon.classList.add("hidden");
        errorIcon.classList.remove("hidden");
        box.classList.remove("hidden", "bg-green-600", "bg-blue-600");
        box.classList.add("bg-red-600");
        responseText.innerHTML = "Network error. Please check your connection and try again.";
        console.error("Registration error:", err);
    }

    // Re-enable button
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i class="fas fa-check-circle"></i><span>Register Company</span>';
});
</script>

</body>
</html>
