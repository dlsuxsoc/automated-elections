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

    document.getElementById("batch-president-summary").innerHTML = batchPresident == null ? 'Abstained' : batchPresident.value;
    document.getElementById("batch-vice-president-summary").innerHTML = batchVicePresident == null ? 'Abstained' : batchVicePresident.value;
    document.getElementById("legislative-assembly-representative-summary").innerHTML = laRepresentative == null ? 'Abstained' : laRepresentative.value;
    document.getElementById("college-president-summary").innerHTML = collegePresident == null ? 'Abstained' : collegePresident.value;
    document.getElementById("president-summary").innerHTML = president == null ? 'Abstained' : president.value;
    document.getElementById("vice-president-internal-summary").innerHTML = vicePresidentInternal == null ? 'Abstained' : vicePresidentInternal.value;
    document.getElementById("vice-president-external-summary").innerHTML = vicePresidentExternal == null ? 'Abstained' : vicePresidentExternal.value;
    document.getElementById("secretary-summary").innerHTML = secretary == null ? 'Abstained' : secretary.value;
    document.getElementById("treasurer-summary").innerHTML = treasurer == null ? 'Abstained' : treasurer.value;
}

function closeModal() {
    document.getElementById('vote-modal').style.display = "none";
}

window.onclick = function (event) {
    if (event.target === document.getElementById('vote-modal')) {
        closeModal();
    }
};