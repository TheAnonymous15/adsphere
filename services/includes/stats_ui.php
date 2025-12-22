async function loadStats() {
  let res = await fetch("/services/api/stats.php");
  let stats = await res.json();

  document.getElementById("totalAds").innerHTML = stats.total_ads;
  document.getElementById("totalLikes").innerHTML = stats.total_likes;
}
loadStats();
