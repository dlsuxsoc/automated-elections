

var input = document.getElementById("pass-gen");

input.addEventListener("keyup", function(event) {
    event.preventDefault();
    if (event.keyCode === 13) {
        var input_value = parseInt(input.value);

        if (!isNaN(input_value)){
            document.getElementById('result').innerHTML = 'your passcode: <b>'+ generatePassword() +'</b>';
        }else {
            document.getElementById('result').innerHTML = '<b>Oops!</b> There is no password for that.';
        }
    }
});

function generatePassword() {
    var length = 8,
        charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        retVal = "";
    for (var i = 0, n = charset.length; i < length; ++i) {
        retVal += charset.charAt(Math.floor(Math.random() * n));
    }
    return retVal;
}