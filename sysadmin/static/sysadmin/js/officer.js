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

    if(tab =='All'){
        document.getElementById("tab-search").style.display ="block";
        document.getElementById("delete").style.display ="none";
        
        
        checkboxes = document.getElementsByName('check');

         for(var i=0; i< checkboxes.length;i++) {
            checkboxes[i].checked = false;
        }
    }
    else{
        document.getElementById("toggle-all").checked = false;
        document.getElementById("tab-search").style.display ="none";
        document.getElementById("delete").style.display ="none";
    }
}

//set default tab to "All" Tab by activating it on page load
document.getElementById("tab-all").click();

function toggle(src){
    checkboxes = document.getElementsByName('check');
    if(src.checked){
        for(var i=0; i<checkboxes.length;i++) {
            checkboxes[i].checked = true;
            document.getElementById("tab-search").style.display ="none";
            document.getElementById("delete").style.display ="flex";
        }
    }
    else{
        for(var i=0; i< checkboxes.length;i++) {
            checkboxes[i].checked = false;
            document.getElementById("tab-search").style.display ="block";
            document.getElementById("delete").style.display ="none";
        }
    }
    
}

function selected(src){
    if(src.checked){
        document.getElementById("tab-search").style.display ="none";
        document.getElementById("delete").style.display ="flex";
    }
    else{
        document.getElementById("toggle-all").checked = false;

        checkboxes = document.getElementsByName('check');
        var flag = true;
        for(var i=0; i<checkboxes.length;i++) {
            if(checkboxes[i].checked == true){
                flag = false;
            }
        }
        if(flag){
            document.getElementById("tab-search").style.display ="block";
            document.getElementById("delete").style.display ="none";
        }
    }
}

function edit(src){

    document.getElementById("toggle-all").checked = false;
    document.getElementById("tab-search").style.display ="none";
    document.getElementById("delete").style.display ="none";
    
    checkboxes = document.getElementsByName('check');

     for(var i=0; i< checkboxes.length;i++) {
        checkboxes[i].checked = false;
    }

    document.getElementById("All").style.display ="none";
    document.getElementById("Edit").style.display ="block";

    //alert( document.getElementById(("row-data-"+src.getAttribute('data-value'))).innerHTML.getElementsByClassName("name")[0].innerHTML );
}