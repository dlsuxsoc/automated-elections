// TODO: Revise once voting is avaialble
function showVote() {
    document.getElementById('vote-modal').style.display = "block";

    let batchPresident = document.querySelector('input[name="batch-president"]:checked');
    let batchVicePresident = document.querySelector('input[name="batch-vice-president"]:checked');
    let laRepresentative = document.querySelector('input[name="legislative-assembly-representative"]:checked');
    let collegePresident = document.querySelector('input[name="college-president"]:checked');
    let president = document.querySelector('input[name="president"]:checked');
    let vicePresidentInternal = document.querySelector('input[name="vice-president-internal"]:checked');
    let vicePresidentExternal = document.querySelector('input[name="vice-president-external"]:checked');
    let secretary = document.querySelector('input[name="secretary"]:checked');
    let treasurer = document.querySelector('input[name="treasurer"]:checked');

    let batchPresidentText = document.getElementById("batch-president-summary");
    let batchVicePresidentText = document.getElementById("batch-vice-president-summary");
    let laRepresentativeText = document.getElementById("legislative-assembly-representative-summary");
    let collegePresidentText = document.getElementById("college-president-summary");
    let presidentText = document.getElementById("president-summary");
    let vicePresidentInternalText = document.getElementById("vice-president-internal-summary");
    let vicePresidentExternalText = document.getElementById("vice-president-external-summary");
    let secretaryText = document.getElementById("secretary-summary");
    let treasurerText = document.getElementById("treasurer-summary");

    if (batchPresidentText != null) {
        batchPresidentText.innerHTML = batchPresident == null ? 'Abstained' : batchPresident.value.split(":")[1];
    }

    if (batchVicePresidentText != null) {
        batchVicePresidentText.innerHTML = batchVicePresident == null ? 'Abstained' : batchVicePresident.value.split(":")[1];
    }

    if (laRepresentativeText != null) {
        laRepresentativeText.laRepresentativeTextinnerHTML = laRepresentative == null ? 'Abstained' : laRepresentative.value.split(":")[1];
    }

    if (collegePresidentText != null) {
        collegePresidentText.innerHTML = collegePresident == null ? 'Abstained' : collegePresident.value.split(":")[1];
    }

    if (presidentText != null) {
        presidentText.innerHTML = president == null ? 'Abstained' : president.value.split(":")[1];
    }

    if (vicePresidentInternalText != null) {
        vicePresidentInternalText.innerHTML = vicePresidentInternal == null ? 'Abstained' : vicePresidentInternal.value.split(":")[1];
    }

    if (vicePresidentExternalText != null) {
        vicePresidentExternalText.innerHTML = vicePresidentExternal == null ? 'Abstained' : vicePresidentExternal.value.split(":")[1];
    }

    if (secretaryText != null) {
        secretaryText.innerHTML = secretary == null ? 'Abstained' : secretary.value.split(":")[1];
    }

    if (treasurerText != null) {
        treasurerText.innerHTML = treasurer == null ? 'Abstained' : treasurer.value.split(":")[1];
    }
}

function closeModal() {
    document.getElementById('vote-modal').style.display = "none";
}

window.onclick = function (event) {
    if (event.target === document.getElementById('vote-modal')) {
        closeModal();
    }
};