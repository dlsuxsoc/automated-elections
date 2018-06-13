function abstain(choice) {
    options = [
        ["batch-president-1", "batch-president-2", "batch-president-3"],
        ["batch-vice-president-1", "batch-vice-president-2", "batch-vice-president-3"],
        ["legislative-assembly-representative-1", "legislative-assembly-representative-2", "legislative-assembly-representative-3"],
        ["college-president-1", "college-president-2", "college-president-3"],
        ["president-1", "president-2", "president-3"],
        ["vice-president-internal-1", "vice-president-internal-2", "vice-president-internal-3"],
        ["vice-president-external-1", "vice-president-external-2", "vice-president-external-3"],
        ["secretary-1", "secretary-2", "secretary-3"],
        ["treasurer-1", "treasurer-2", "treasurer-3"],
    ];

    options[choice - 1].forEach(function (id) {
        document.getElementById(id).checked = false;
    });

    console.log(options[choice]);
}