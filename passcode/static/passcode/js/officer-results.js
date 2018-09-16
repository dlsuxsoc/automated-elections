function viewVotesForPosition() {
    // Get the selected position identifier
    let dropdown = document.getElementById('position-results');
    let identifier = dropdown.options[dropdown.selectedIndex].value;

    // Reload page with query
    window.location.search = 'query=' + identifier;
}

function selectCollege(evt, col) {
    var i, tabcontent, tabButtons;
    tabcontent = document.getElementsByClassName("college-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tabButtons = document.getElementsByClassName("college-buttons");
    for (i = 0; i < tabButtons.length; i++) {
        tabButtons[i].className = tabButtons[i].className.replace(" active", "");
    }
    document.getElementById(col).style.display = "block";
    evt.currentTarget.className += " active";
}

function openTab(evt, tab) {
    var i, tabcontent, tabButtons;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tabButtons = document.getElementsByClassName("tab-buttons");
    for (i = 0; i < tabButtons.length; i++) {
        tabButtons[i].className = tabButtons[i].className.replace(" active", "");
    }
    document.getElementById(tab).style.display = "block";
    evt.currentTarget.className += " active";

    //document.getElementById("college-ccs").click();
}

function drawChart(results) {
    // Get the raw data from JSON, if possible
    console.log(results);

    let raw_votes = JSON.parse(results);

    let canvas = document.getElementById("piechart");

    if (Object.keys(raw_votes).length !== 0) {
        // Correctly form the labels and their data
        let labels = [];
        let votes = [];

        for (let candidate in raw_votes) {
            if (raw_votes.hasOwnProperty(candidate)) {
                labels.push(candidate);
                votes.push(raw_votes[candidate])
            }
        }

        let ctx = canvas.getContext('2d');

        // Draw the chart
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Votes',
                    data: votes,
                    backgroundColor: [
                        'rgba(255, 99, 132, 1.0)',
                        'rgba(54, 162, 235, 1.0)',
                        'rgba(255, 206, 86, 1.0)',
                        'rgba(75, 192, 192, 1.0)',
                        'rgba(153, 102, 255, 1.0)',
                        'rgba(255, 159, 64, 1.0)'
                    ],
                    borderColor: [
                        'rgba(255, 99, 132, 1.0)',
                        'rgba(54, 162, 235, 1.0)',
                        'rgba(255, 206, 86, 1.0)',
                        'rgba(75, 192, 192, 1.0)',
                        'rgba(153, 102, 255, 1.0)',
                        'rgba(255, 159, 64, 1.0)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {}
        });
    } else {
        // Forget about it
        canvas.parentElement.removeChild(canvas);
    }
}

document.getElementById("tab-controls").click();