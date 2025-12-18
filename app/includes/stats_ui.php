async function loadStats() {
  let res = await fetch("/app/includes/stats.php");
  let stats = await res.json();

  document.getElementById("totalAds").innerHTML = stats.total_ads;
  document.getElementById("totalLikes").innerHTML = stats.total_likes;
}
loadStats();
