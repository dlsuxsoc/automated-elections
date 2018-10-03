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
    
    document.querySelectorAll('*[id^="tab-college"]')[0].click();
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
        Chart.defaults.global.defaultFontFamily = "Opensans";

        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Votes',
                    data: votes,
                    backgroundColor: [
                        'rgba(54, 164, 114, 1.0)',
                        'rgba(53, 53, 53, 1.0)',
                        'rgba(60, 110, 113, 1.0)',
                        'rgba(164, 145, 211, 1.0)',
                        'rgba(197, 220, 160, 1.0)',
                        'rgba(162, 215, 41, 1.0)'
                    ],
                    borderColor: [
                        'rgba(54, 164, 114, 1.0)',
                        'rgba(53, 53, 53, 1.0)',
                        'rgba(60, 110, 113, 1.0)',
                        'rgba(164, 145, 211, 1.0)',
                        'rgba(197, 220, 160, 1.0)',
                        'rgba(162, 215, 41, 1.0)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                title: {
                    display: true,
                    text: 'Voting results',
                    fontSize: 20
                }
            }
        });
    } else {
        // Forget about it
        canvas.parentElement.removeChild(canvas);
    }
}

document.getElementById("tab-underview").click();