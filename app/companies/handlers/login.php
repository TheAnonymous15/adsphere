<?php
/********************************************
 * login.php
 ********************************************/
session_start();

$metaBase = __DIR__ . "/../metadata/";

// If already logged in redirect
if (isset($_SESSION['logged_in']) && $_SESSION['logged_in'] === true) {
    header("Location: /app/companies/dashboard.php");
    exit;
}

$error = "";

if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    $email = trim($_POST["email"]);
    $password = trim($_POST["password"]);

    if ($email === "" || $password === "") {
        $error = "Missing credentials.";
    } else {

        $found = false;

        foreach (scandir($metaBase) as $file) {

            if ($file === "." || $file === "..") continue;

            if (!str_ends_with($file, ".json")) continue;

            $raw = file_get_contents("$metaBase/$file");
            $company = json_decode($raw, true);

            if (!$company) continue;

            $cEmail = $company["contact"]["email"] ?? null;

            if ($cEmail && strtolower($cEmail) === strtolower($email)) {

                $found = true;
                $slug = $company["slug"];

                // Static password for now
                if ($password === "1234") {

                    $_SESSION["logged_in"] = true;
                    $_SESSION["company"] = $slug;

                    header("Location: ad_upload.php");
                    exit;

                } else {
                    $error = "Invalid password.";
                }
            }
        }

        if (!$found) {
            $error = "Email not registered.";
        }
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>Company Login</title>
    <script src="/app/assets/css/tailwind.js"></script>
</head>
<body class="bg-slate-900 text-white p-6 flex justify-center">

<div class="max-w-md w-full bg-white/10 p-6 rounded-xl shadow-xl">

    <h2 class="text-2xl font-bold text-indigo-300 mb-4">Company Login</h2>

    <?php if ($error): ?>
        <div class="bg-red-600 p-3 rounded mb-3 text-white">
            <?= htmlspecialchars($error) ?>
        </div>
    <?php endif; ?>

    <form method="POST" class="flex flex-col gap-3">

        <input name="email" type="email"
               placeholder="Email"
               class="text-black p-2 rounded">

        <input name="password" type="password"
               placeholder="Password"
               class="text-black p-2 rounded">

        <button class="p-2 bg-indigo-500 rounded mt-2 hover:bg-indigo-600">
            Login
        </button>

    </form>

</div>

</body>
</html>
