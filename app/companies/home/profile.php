<?php
session_start();
if(!isset($_SESSION['company'])) exit("login first");

$company = $_SESSION['company'];
$profileFile = __DIR__."/companies/$company/profile.json";

$profile = file_exists($profileFile)
    ? json_decode(file_get_contents($profileFile),true)
    : ["email"=>"","phone"=>"","website"=>""];

?>

<!DOCTYPE html>
<html>
<head>
<title>Company Profile</title>
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@3.4.1/dist/tailwind.min.css" rel="stylesheet">
</head>

<body class="text-white bg-gray-900">

<div class="max-w-xl bg-gray-800 mx-auto mt-10 p-6 rounded-xl">

<h2 class="text-2xl font-bold mb-4">Company Profile</h2>

<form method="POST" action="save_profile.php">

<label>Email</label>
<input class="text-black p-2 w-full" name="email"
       value="<?= htmlspecialchars($profile['email']) ?>">

<label class="mt-3">Phone</label>
<input class="text-black p-2 w-full" name="phone"
       value="<?= htmlspecialchars($profile['phone']) ?>">

<label class="mt-3">Website</label>
<input class="text-black p-2 w-full" name="website"
       value="<?= htmlspecialchars($profile['website']) ?>">

<button class="bg-blue-600 hover:bg-blue-700 w-full p-2 mt-6 rounded">
Save Changes
</button>

</form>
</div>
</body>
</html>
