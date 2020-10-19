function showVote(positions, polls) {
    // Remember the "voteable" positions
    positions = JSON.parse(positions);

    // Remember the polls
    polls = JSON.parse(polls);

    // For each position, collect each vote, if any
    for (let index = 0; index < positions.length; index++) {
        // Check if the input with this position is checked
        // Get that input
        selector = 'input[name="' + positions[index] + '"]:checked';
        element = document.querySelector(selector);

        // If it is indeed checked, get the candidate name from the parent of that input
        candidateName = '';

        if (element != null) {
            inputParent = element.parentElement.getElementsByClassName('candidate-name')[0];
            candidateName = inputParent.innerHTML;
        } else {
            // If no input has been checked, it means the voter has abstained on that position
            candidateName = "(abstained)";
        }

        // Put the candidate name in the summary modal
        selector = positions[index] + '-summary';
        summary = document.getElementById(selector);

        summary.innerHTML = candidateName;
    }

    for (let index = 0; index < polls.length; index++) {
        // Check if the input with this position is checked
        // Get that input
        selector = 'input[name="' + polls[index] + '"]:checked';
        element = document.querySelector(selector);

        // If it is indeed checked, get the candidate name from the parent of that input
        vote = '';

        if (element != null) {
            inputParent = element.parentElement.getElementsByClassName('poll-choice')[0];
            vote = inputParent.innerHTML;
        } else {
            // If no input has been checked, it means the voter has abstained on that position
            vote = "(abstained)";
        }

        // Put the candidate name in the summary modal
        selector = polls[index] + '-summary';
        summary = document.getElementById(selector);

        summary.innerHTML = vote;
    }

    // Show the summary modal
    document.getElementById('vote-modal').style.display = "block";
}

function closeModal() {
    document.getElementById('vote-modal').style.display = "none";
}

window.onclick = function (event) {
    if (event.target === document.getElementById('vote-modal')) {
        closeModal();
    }
};