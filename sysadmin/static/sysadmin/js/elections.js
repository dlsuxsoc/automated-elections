function selectAllCollege(choice) {
    // Get all relevant inputs to be unchecked with the given name
    let inputs = document.getElementsByName(choice);

    // Then uncheck them all
    for (let index = 0; index < inputs.length; index++) {
        inputs[index].checked = true;
    }
}

function selectAll() {
    // Get all relevant inputs to be unchecked with the given name
    let inputs = document.querySelectorAll('input[type="checkbox"]');

    // Then uncheck them all
    for (let index = 0; index < inputs.length; index++) {
        inputs[index].checked = true;
    }
}