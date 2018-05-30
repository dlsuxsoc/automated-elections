function showVote() {
	document.getElementById('vote-modal').style.display = "block";
}

window.onclick = function(event) {
    if (event.target == document.getElementById('vote-modal')) {
        document.getElementById('vote-modal').style.display = "none";
    }
}