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

    if (tab == 'All') {
        document.getElementById("tab-search").style.display = "block";
        document.getElementById("delete").style.display = "none";


        checkboxes = document.getElementsByName('check');

        for (var i = 0; i < checkboxes.length; i++) {
            checkboxes[i].checked = false;
        }
    }
    else {
        document.getElementById("toggle-all").checked = false;
        document.getElementById("tab-search").style.display = "none";
        document.getElementById("delete").style.display = "none";
    }
}

//set default tab to "All" Tab by activating it on page load
document.getElementById("tab-all").click();

function toggle(src) {
    checkboxes = document.getElementsByName('check');
    if (src.checked) {
        for (var i = 0; i < checkboxes.length; i++) {
            checkboxes[i].checked = true;
            document.getElementById("tab-search").style.display = "none";
            document.getElementById("delete").style.display = "flex";
        }
    }
    else {
        for (var i = 0; i < checkboxes.length; i++) {
            checkboxes[i].checked = false;
            document.getElementById("tab-search").style.display = "block";
            document.getElementById("delete").style.display = "none";
        }
    }

}

function selected(src) {
    if (src.checked) {
        document.getElementById("tab-search").style.display = "none";
        document.getElementById("delete").style.display = "flex";
    }
    else {
        document.getElementById("toggle-all").checked = false;

        checkboxes = document.getElementsByName('check');
        var flag = true;
        for (var i = 0; i < checkboxes.length; i++) {
            if (checkboxes[i].checked == true) {
                flag = false;
            }
        }
        if (flag) {
            document.getElementById("tab-search").style.display = "block";
            document.getElementById("delete").style.display = "none";
        }
    }
}

function edit_voter(src, voter, page) {
    document.getElementById("toggle-all").checked = false;
    document.getElementById("tab-search").style.display = "none";
    document.getElementById("delete").style.display = "none";

    checkboxes = document.getElementsByName('check');

    for (var i = 0; i < checkboxes.length; i++) {
        checkboxes[i].checked = false;
    }

    document.getElementById("All").style.display = "none";
    document.getElementById("Edit").style.display = "block";

    //alert( document.getElementById(("row-data-"+src.getAttribute('data-value'))).innerHTML.getElementsByClassName("name")[0].innerHTML );

    voter = JSON.parse(voter)

    extras = voter[0];
    voter_details = voter[1];

    document.getElementsByName("edit-id")[0].value = voter_details["id"];
    document.getElementById("edit-firstnames").value = extras["first_name"];
    document.getElementById("edit-lastname").value = extras["last_name"];
    document.getElementById("edit-college").options[0].innerHTML = extras["college"];
    document.getElementById("edit-voting-status").options[0].innerText = voter_details["voting_status"] ? "Has already voted" : "Hasn't voted yet";

    if (voter_details["eligibility_status"]) {
        document.getElementById("eligible").selected = true;
    } else {
        document.getElementById("not-eligible").selected = true;
    }

}

function delete_voters() {
    // Collect all checked checkboxes
    var array = [];
    var checkboxes = document.querySelectorAll("input[type=checkbox][name=check]:checked");

    for (var i = 0; i < checkboxes.length; i++) {
        array.push(checkboxes[i].value);
    }

    // Delete all of them by adding them to a form
    delete_form = document.getElementById("delete-voters");

    for (var i = 0; i < array.length; i++) {
        hidden = document.createElement("input");

        hidden.setAttribute("type", "hidden");
        hidden.setAttribute("name", "voters");
        hidden.setAttribute("value", array[i]);

        delete_form.appendChild(hidden);
    }

    // Then activate that form
    delete_form.submit();
}

function delete_candidates() {
    // Collect all checked checkboxes
    var array = [];
    var checkboxes = document.querySelectorAll("input[type=checkbox][name=check]:checked");

    for (var i = 0; i < checkboxes.length; i++) {
        array.push(checkboxes[i].value);
    }

    // Delete all of them by adding them to a form
    delete_form = document.getElementById("delete-candidates");

    for (var i = 0; i < array.length; i++) {
        hidden = document.createElement("input");

        hidden.setAttribute("type", "hidden");
        hidden.setAttribute("name", "candidates");
        hidden.setAttribute("value", array[i]);

        delete_form.appendChild(hidden);
    }

    // Then activate that form
    delete_form.submit();
}

function set_take(csrf_token) {
    // Get the candidate dropdown
    var candidateDropdown = document.getElementById("candidate-dropdown");

    // Get the selected candidate
    var user = candidateDropdown.options[candidateDropdown.selectedIndex];

    // Get the username of the candidate
    var username = user.innerText.split(":")[0];

    // Get the issue dropdown
    var issueDropdown = document.getElementById("issue-dropdown");

    // Get the selected issue
    var issue = issueDropdown.options[issueDropdown.selectedIndex];
    issue = issue.text;

    // Get the take form
    var takeForm = document.getElementById("take");

    // Retrieve the response using AJAX
    ajaxTake(csrf_token, username, issue, takeForm);
}

function ajaxTake(csrf_token, candidate, issue, takeForm) {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState === XMLHttpRequest.DONE) {   // XMLHttpRequest.DONE == 4
            if (xmlhttp.status === 200) {
                callback(takeForm, xmlhttp.responseText);
            }
            else if (xmlhttp.status === 400) {
                callback(takeForm, "(Unable to retrieve this candidate's take from the server)")
            }
            else {
                callback(takeForm, "(Unable to retrieve this candidate's take from the server)")
            }
        }
    };

    xmlhttp.open("POST", "/sysadmin/candidates/takes/" + candidate + "/" + issue, true);
    xmlhttp.setRequestHeader("X-CSRFToken", csrf_token);
    xmlhttp.send();
}

function callback(takeForm, response) {
    // Parse into JSON
    raw_response = JSON.parse(response)

    // Change the take form text
    takeForm.value = raw_response['response']
}
