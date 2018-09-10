function abstain_candidate(choice) {
    // Get all relevant inputs to be unchecked with the given name
    let inputs = document.getElementsByName(choice);

    // Then uncheck them all
    for (let index = 0; index < inputs.length; index++) {
        inputs[index].checked = false;
    }
}