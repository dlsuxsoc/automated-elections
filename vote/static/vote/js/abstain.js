function abstain(choice) {
	options = [
		["president-1", "president-2", "president-3"],
		["vice-president-1", "vice-president-2", "vice-president-3"],
		["legislative-assembly-representative-1", "legislative-assembly-representative-2", "legislative-assembly-representative-3"]
	];
	options[choice-1].forEach(function(id) {
    	document.getElementById(id).checked = false;
    });

    console.log(options[choice]);
}