<?php
/********************************************
 * categories.php - Professional Category Manager
 * Hybrid Database System Integration
 * Create, edit, delete, and manage categories
 ********************************************/

// Load database system
require_once __DIR__ . '/../database/Database.php';

$db = Database::getInstance();
$adsBase = __DIR__ . "/../companies/data/";

// Ensure directory exists
if (!is_dir($adsBase)) {
    mkdir($adsBase, 0775, true);
}

$message = "";
$messageType = ""; // success, error, warning

// Handle category creation
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action'])) {

    $action = $_POST['action'];

    try {
        $lock = $db->acquireLock('category_manage');
        if (!$lock) {
            throw new Exception('Could not acquire lock. Please try again.');
        }

        if ($action === 'create') {
            // Create new categories
            $input = trim($_POST['categories'] ?? '');

            if (empty($input)) {
                throw new Exception('Please enter at least one category');
            }

            // Parse input (comma, space, or newline separated)
            $categories = preg_split('/[\s,\n\r]+/', $input);
            $created = [];
            $skipped = [];

            $db->beginTransaction();

            foreach ($categories as $category) {
                $category = trim($category);
                if (empty($category)) continue;

                // Generate slug
                $slug = strtolower(preg_replace('/[^a-z0-9]+/i', '-', $category));
                $slug = trim($slug, '-');

                // Check if exists
                $exists = $db->queryOne("SELECT category_slug FROM categories WHERE category_slug = ?", [$slug]);

                if (!$exists) {
                    // Insert into database
                    $sql = "INSERT INTO categories (category_slug, category_name, created_at)
                            VALUES (?, ?, ?)";
                    $db->execute($sql, [$slug, $category, time()]);

                    // Create directory
                    $dir = $adsBase . $slug;
                    if (!is_dir($dir)) {
                        mkdir($dir, 0755, true);
                    }

                    $created[] = $category;
                } else {
                    $skipped[] = $category;
                }
            }

            $db->commit();

            if (!empty($created)) {
                $message = "✅ Created " . count($created) . " categor" . (count($created) > 1 ? "ies" : "y") . ": " . implode(", ", $created);
                $messageType = "success";
            }

            if (!empty($skipped)) {
                $message .= (!empty($message) ? " | " : "") . "⚠️ Skipped " . count($skipped) . " (already exist): " . implode(", ", $skipped);
                $messageType = empty($created) ? "warning" : "success";
            }

        } elseif ($action === 'delete') {
            // Delete category
            $slug = $_POST['slug'] ?? '';

            if (empty($slug)) {
                throw new Exception('Invalid category');
            }

            // Check if any companies use this category
            $usage = $db->queryOne("SELECT COUNT(*) as count FROM company_categories WHERE category_slug = ?", [$slug]);

            if ($usage['count'] > 0) {
                throw new Exception("Cannot delete. {$usage['count']} compan" . ($usage['count'] > 1 ? "ies use" : "y uses") . " this category.");
            }

            $db->beginTransaction();

            // Delete from database
            $db->execute("DELETE FROM categories WHERE category_slug = ?", [$slug]);

            // Remove directory (if empty)
            $dir = $adsBase . $slug;
            if (is_dir($dir) && count(scandir($dir)) <= 2) {
                rmdir($dir);
            }

            $db->commit();

            $message = "✅ Category deleted successfully";
            $messageType = "success";

        } elseif ($action === 'edit') {
            // Edit category name
            $slug = $_POST['slug'] ?? '';
            $newName = trim($_POST['new_name'] ?? '');

            if (empty($slug) || empty($newName)) {
                throw new Exception('Invalid input');
            }

            $db->execute("UPDATE categories SET category_name = ? WHERE category_slug = ?", [$newName, $slug]);

            $message = "✅ Category updated successfully";
            $messageType = "success";
        }

        $db->releaseLock($lock);

        // Clear cache
        $db->cacheDelete('all_categories');

    } catch (Exception $e) {
        if (isset($db)) $db->rollback();
        if (isset($lock)) $db->releaseLock($lock);

        $message = "❌ " . $e->getMessage();
        $messageType = "error";
    }
}

// Load categories from database
$categories = $db->query("SELECT * FROM categories ORDER BY category_name");

// Get category statistics
$stats = [];
foreach ($categories as $cat) {
    $companyCount = $db->queryOne(
        "SELECT COUNT(*) as count FROM company_categories WHERE category_slug = ?",
        [$cat['category_slug']]
    )['count'] ?? 0;

    $adCount = $db->queryOne(
        "SELECT COUNT(*) as count FROM ads WHERE category_slug = ?",
        [$cat['category_slug']]
    )['count'] ?? 0;

    $stats[$cat['category_slug']] = [
        'companies' => $companyCount,
        'ads' => $adCount
    ];
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Category Manager - AdSphere</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
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

        .category-card {
            transition: all 0.2s ease;
        }

        .category-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(168, 85, 247, 0.25);
        }

        .pulse-animation {
            animation: pulse 2s infinite;
        }
    </style>
</head>

<body class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen p-6">

<div class="container mx-auto max-w-7xl">

    <!-- Header -->
    <div class="glass-effect rounded-2xl p-6 mb-6 animate-slide-in">
        <div class="flex items-center justify-between flex-wrap gap-4">
            <div>
                <h1 class="text-4xl font-bold text-white flex items-center gap-3">
                    <i class="fas fa-layer-group text-purple-400"></i>
                    Category Manager
                </h1>
                <p class="text-gray-400 mt-2">Create and manage advertisement categories</p>
            </div>
            <div class="flex items-center gap-4">
                <div class="text-right">
                    <p class="text-sm text-gray-400">Total Categories</p>
                    <p class="text-3xl font-bold text-purple-400"><?= count($categories) ?></p>
                </div>
                <div class="h-12 w-px bg-white/20"></div>
                <a href="admin_dashboard.php" class="px-6 py-3 bg-blue-600/20 border border-blue-600/50 rounded-xl text-blue-300 hover:bg-blue-600/30 transition">
                    <i class="fas fa-arrow-left mr-2"></i>Dashboard
                </a>
            </div>
        </div>
    </div>

    <!-- Message -->
    <?php if ($message): ?>
        <div class="glass-effect rounded-2xl p-4 mb-6 animate-slide-in border-l-4 <?= $messageType === 'success' ? 'border-green-500 bg-green-500/10' : ($messageType === 'warning' ? 'border-yellow-500 bg-yellow-500/10' : 'border-red-500 bg-red-500/10') ?>">
            <div class="flex items-center gap-3">
                <i class="fas <?= $messageType === 'success' ? 'fa-check-circle text-green-400' : ($messageType === 'warning' ? 'fa-exclamation-triangle text-yellow-400' : 'fa-times-circle text-red-400') ?> text-xl"></i>
                <p class="text-white"><?= $message ?></p>
            </div>
        </div>
    <?php endif; ?>

    <div class="grid lg:grid-cols-3 gap-6">

        <!-- Create Categories Form -->
        <div class="lg:col-span-1">
            <div class="glass-effect rounded-2xl p-6 sticky top-6">
                <h2 class="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                    <i class="fas fa-plus-circle text-green-400"></i>
                    Create New
                </h2>

                <form method="POST" class="space-y-4">
                    <input type="hidden" name="action" value="create">

                    <div>
                        <label class="block text-sm font-semibold text-gray-300 mb-2">
                            <i class="fas fa-tags mr-2 text-purple-400"></i>Categories
                        </label>
                        <textarea name="categories"
                                  required
                                  rows="6"
                                  placeholder="Enter categories (comma or line separated)&#10;&#10;Examples:&#10;Electronics&#10;Fashion, Beauty&#10;Automotive"
                                  class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/50 transition resize-none"></textarea>
                    </div>

                    <button type="submit"
                            class="w-full btn-primary px-6 py-4 rounded-xl text-white font-bold shadow-lg flex items-center justify-center gap-2">
                        <i class="fas fa-magic"></i>
                        <span>Create Categories</span>
                    </button>
                </form>

                <div class="mt-6 p-4 bg-blue-500/20 border border-blue-500/50 rounded-xl">
                    <p class="text-blue-300 text-xs flex items-start gap-2">
                        <i class="fas fa-info-circle mt-0.5"></i>
                        <span>Categories will be created in both database and file system. Use commas, spaces, or new lines to separate multiple categories.</span>
                    </p>
                </div>
            </div>
        </div>

        <!-- Categories List -->
        <div class="lg:col-span-2">
            <div class="glass-effect rounded-2xl p-6">
                <div class="flex items-center justify-between mb-6">
                    <h2 class="text-2xl font-bold text-white flex items-center gap-2">
                        <i class="fas fa-list text-yellow-400"></i>
                        Existing Categories
                    </h2>
                    <div class="text-sm text-gray-400">
                        <?= count($categories) ?> categor<?= count($categories) === 1 ? 'y' : 'ies' ?>
                    </div>
                </div>

                <?php if (empty($categories)): ?>
                    <div class="text-center py-12">
                        <i class="fas fa-inbox text-6xl text-gray-600 mb-4"></i>
                        <p class="text-gray-400 text-lg">No categories yet</p>
                        <p class="text-gray-500 text-sm">Create your first category using the form on the left</p>
                    </div>
                <?php else: ?>

                    <!-- Search Bar -->
                    <div class="mb-6">
                        <div class="relative">
                            <input type="text"
                                   id="searchInput"
                                   placeholder="Search categories..."
                                   class="w-full bg-white/10 border border-white/20 rounded-xl pl-12 pr-4 py-3 text-white placeholder-gray-500 focus:border-yellow-500 focus:ring-2 focus:ring-yellow-500/50 transition">
                            <i class="fas fa-search absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"></i>
                        </div>
                    </div>

                    <!-- Categories Grid - Compact for 100+ categories -->
                    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3" id="categoriesGrid">
                        <?php foreach ($categories as $cat):
                            $stat = $stats[$cat['category_slug']];
                        ?>
                            <div class="category-card glass-effect rounded-lg p-3 border border-white/10" data-category="<?= htmlspecialchars(strtolower($cat['category_name'])) ?>">
                                <div class="flex items-start justify-between mb-2">
                                    <div class="flex-1 min-w-0">
                                        <h3 class="text-sm font-bold text-white truncate category-name" title="<?= htmlspecialchars($cat['category_name']) ?>">
                                            <?= htmlspecialchars($cat['category_name']) ?>
                                        </h3>
                                        <p class="text-[10px] text-gray-400 font-mono truncate"><?= htmlspecialchars($cat['category_slug']) ?></p>
                                    </div>
                                    <div class="flex gap-1 ml-2">
                                        <button onclick="editCategory('<?= htmlspecialchars($cat['category_slug']) ?>', '<?= htmlspecialchars($cat['category_name']) ?>')"
                                                class="p-1.5 bg-blue-600/20 border border-blue-600/50 rounded text-blue-300 hover:bg-blue-600/30 transition text-xs"
                                                title="Edit">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button onclick="deleteCategory('<?= htmlspecialchars($cat['category_slug']) ?>', '<?= htmlspecialchars($cat['category_name']) ?>')"
                                                class="p-1.5 bg-red-600/20 border border-red-600/50 rounded text-red-300 hover:bg-red-600/30 transition text-xs"
                                                title="Delete">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </div>
                                </div>

                                <div class="flex items-center gap-2 text-[10px]">
                                    <div class="flex items-center gap-1 text-gray-400">
                                        <i class="fas fa-building text-purple-400"></i>
                                        <span class="font-bold text-white"><?= $stat['companies'] ?></span>
                                    </div>
                                    <div class="w-px h-3 bg-white/20"></div>
                                    <div class="flex items-center gap-1 text-gray-400">
                                        <i class="fas fa-ad text-green-400"></i>
                                        <span class="font-bold text-white"><?= $stat['ads'] ?></span>
                                    </div>
                                </div>
                            </div>
                        <?php endforeach; ?>
                    </div>
                <?php endif; ?>
            </div>
        </div>
    </div>
</div>

<!-- Edit Modal -->
<div id="editModal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="glass-effect rounded-2xl p-6 max-w-md w-full animate-slide-in">
        <h3 class="text-2xl font-bold text-white mb-4 flex items-center gap-2">
            <i class="fas fa-edit text-blue-400"></i>
            Edit Category
        </h3>

        <form method="POST" id="editForm">
            <input type="hidden" name="action" value="edit">
            <input type="hidden" name="slug" id="editSlug">

            <div class="mb-4">
                <label class="block text-sm font-semibold text-gray-300 mb-2">Category Name</label>
                <input type="text"
                       name="new_name"
                       id="editName"
                       required
                       class="w-full bg-white/10 border border-white/20 rounded-xl px-4 py-3 text-white focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50 transition">
            </div>

            <div class="flex gap-3">
                <button type="button"
                        onclick="closeEditModal()"
                        class="flex-1 px-6 py-3 bg-gray-600/20 border border-gray-600/50 rounded-xl text-gray-300 hover:bg-gray-600/30 transition">
                    Cancel
                </button>
                <button type="submit"
                        class="flex-1 btn-primary px-6 py-3 rounded-xl text-white font-bold">
                    Save Changes
                </button>
            </div>
        </form>
    </div>
</div>

<!-- Delete Confirmation Modal -->
<div id="deleteModal" class="hidden fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
    <div class="glass-effect rounded-2xl p-6 max-w-md w-full animate-slide-in border-2 border-red-500/50">
        <h3 class="text-2xl font-bold text-white mb-4 flex items-center gap-2">
            <i class="fas fa-exclamation-triangle text-red-400"></i>
            Confirm Deletion
        </h3>

        <p class="text-gray-300 mb-6">
            Are you sure you want to delete the category <strong id="deleteCategoryName" class="text-red-400"></strong>?
            This action cannot be undone.
        </p>

        <form method="POST" id="deleteForm">
            <input type="hidden" name="action" value="delete">
            <input type="hidden" name="slug" id="deleteSlug">

            <div class="flex gap-3">
                <button type="button"
                        onclick="closeDeleteModal()"
                        class="flex-1 px-6 py-3 bg-gray-600/20 border border-gray-600/50 rounded-xl text-gray-300 hover:bg-gray-600/30 transition">
                    Cancel
                </button>
                <button type="submit"
                        class="flex-1 px-6 py-3 bg-red-600 hover:bg-red-700 rounded-xl text-white font-bold transition">
                    <i class="fas fa-trash mr-2"></i>Delete
                </button>
            </div>
        </form>
    </div>
</div>

<script>
// Search functionality
document.getElementById('searchInput').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const cards = document.querySelectorAll('.category-card');

    cards.forEach(card => {
        const categoryName = card.dataset.category;
        if (categoryName.includes(searchTerm)) {
            card.classList.remove('hidden');
        } else {
            card.classList.add('hidden');
        }
    });
});

// Edit modal
function editCategory(slug, name) {
    document.getElementById('editSlug').value = slug;
    document.getElementById('editName').value = name;
    document.getElementById('editModal').classList.remove('hidden');
}

function closeEditModal() {
    document.getElementById('editModal').classList.add('hidden');
}

// Delete modal
function deleteCategory(slug, name) {
    document.getElementById('deleteSlug').value = slug;
    document.getElementById('deleteCategoryName').textContent = name;
    document.getElementById('deleteModal').classList.remove('hidden');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.add('hidden');
}

// Close modals on ESC key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeEditModal();
        closeDeleteModal();
    }
});

// Close modals on outside click
document.getElementById('editModal').addEventListener('click', function(e) {
    if (e.target === this) closeEditModal();
});

document.getElementById('deleteModal').addEventListener('click', function(e) {
    if (e.target === this) closeDeleteModal();
});
</script>

</body>
</html>
