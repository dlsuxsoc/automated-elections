// To do:
// Started to lag after adding content inside.
var modal;

window.onload = function () {
    modal = document.getElementById('modal-read');
}

function hintBrowser(csrf_token, candidate_id) {
    // The optimizable properties that are going to change
    // in the animation's keyframes block

    //insert response here
    modal = document.getElementById('modal-read');

    modal.style.willChange = 'clip-path';
    console.log('add will-change');

    modal.style.cssText = '-webkit-clip-path: polygon(0 0, 100% 0%, 100% 100%, 0% 100%);clip-path: polygon(0 0, 100% 0%, 100% 100%, 0% 100%);'
    document.getElementById('modal__content-read').style.cssText = 'opacity: 1;-webkit-transform: translate3D(0, 1em, 0);transform: translate3D(0, 1em, 0);transition: opacity 0.3s 0.2s, -webkit-transform 0.6s 0.2s cubic-bezier(0, 0.65, 0.06, 0.98);transition: opacity 0.3s 0.2s, transform 0.6s 0.2s cubic-bezier(0, 0.65, 0.06, 0.98);transition: opacity 0.3s 0.2s, transform 0.6s 0.2s cubic-bezier(0, 0.65, 0.06, 0.98), -webkit-transform 0.6s 0.2s cubic-bezier(0, 0.65, 0.06, 0.98);'

    document.getElementById('overlay').style.cssText = 'display: block';

    // Set the take of this modal
    set_take(csrf_token, candidate_id)
}

function removeHint() {
    modal = document.getElementById('modal-read');

    modal.style.willChange = 'auto';
    console.log('remove will-change');

    modal.style.cssText = '-webkit-clip-path: polygon(calc(50% - 0em) calc(50% - 0em), calc(50% + 0em) calc(50% - 0em), calc(50% + 0em) calc(50% + 0em), calc(50% - 0em) calc( 50% + 0em));clip-path: polygon(calc(50% - 0em) calc(50% - 0em), calc(50% + 0em) calc(50% - 0em), calc(50% + 0em) calc(50% + 0em), calc(50% - 0em) calc( 50% + 0em));'
    document.getElementById('modal__content-read').style.cssText = 'opacity: 0;-webkit-transform: translate3D(0, -1em, 0);transform: translate3D(0, -1em, 0);transition: opacity 0.1s 0s, -webkit-transform 0.3s 0s;transition: opacity 0.1s 0s, transform 0.3s 0s;transition: opacity 0.1s 0s, transform 0.3s 0s, -webkit-transform 0.3s 0s;'

    document.getElementById('overlay').style.cssText = 'display: none';
}

function set_take(csrf_token, candidate_id) {
    // Get the issue dropdown
    var issueDropdown = document.getElementById("issue-dropdown");

    // Get the selected issue
    var issue = issueDropdown.options[issueDropdown.selectedIndex];
    issue = issue.text;

    // Get the response container
    var responseContainer = document.getElementById("response-modal");

    // Set the associated candidate of this modal
    document.getElementById('associated-candidate').value = candidate_id;

    // Retrieve the response using AJAX
    ajaxTake(csrf_token, candidate_id, issue, responseContainer);
}

function ajaxTake(csrf_token, candidate, issue, responseContainer) {
    var xmlhttp = new XMLHttpRequest();

    xmlhttp.onreadystatechange = function () {
        if (xmlhttp.readyState === XMLHttpRequest.DONE) {   // XMLHttpRequest.DONE == 4
            if (xmlhttp.status === 200) {
                callbackTake(responseContainer, xmlhttp.responseText);
            }
            else if (xmlhttp.status === 400) {
                callbackTake(responseContainer, "(Unable to retrieve this candidate's take from the server)")
            }
            else {
                callbackTake(responseContainer, "(Unable to retrieve this candidate's take from the server)")
            }
        }
    };

    xmlhttp.open("POST", "/takes/" + candidate + "/" + issue + "/", true);
    xmlhttp.setRequestHeader("X-CSRFToken", csrf_token);
    xmlhttp.send();
}

function callbackTake(responseContainer, response) {
    // Parse from JSON
    raw_response = JSON.parse(response);

    console.log(responseContainer);

    // Change the take form text
    responseContainer.innerText = "\n\n" + raw_response['response'] + "\n\n\n";
}

function change_take(csrf_token) {
    // Get the candidate associated
    candidate = document.getElementById("associated-candidate").value;

    set_take(csrf_token, candidate);
}

