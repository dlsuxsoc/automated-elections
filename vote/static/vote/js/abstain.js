function abstain_candidate(choice) {
    // Get all relevant inputs to be unchecked with the given name
    let inputs = document.getElementsByName(choice);
    let button = event.srcElement

    // Then uncheck them all
    for (let index = 0; index < inputs.length; index++) {
        inputs[index].checked = false;
    }

    button.classList.add("abstain-active")
}

function candidate_select(abstainBtn) {
    let button = document.getElementById(abstainBtn)
    button.classList.remove("abstain-active")

}