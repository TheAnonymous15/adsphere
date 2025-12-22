function like(adId) {
    fetch("/services/api/like.php", {
        method:"POST",
        headers:{ "Content-Type":"application/x-www-form-urlencoded" },
        body:"ad_id="+encodeURIComponent(adId)
    })
    .then(r=>r.json())
    .then(data=>{
        document.getElementById("likes_"+adId).innerText = data.likes;
    });
}
