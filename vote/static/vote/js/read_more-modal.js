// To do:
// Started to lag after adding content inside.
var modal;

window.onload = function() {
   	modal = document.getElementById('modal-read');
}

function hintBrowser(choice) {
    // The optimizable properties that are going to change
    // in the animation's keyframes block

    //insert response here
    modal = document.getElementById('modal-read');

    modal.style.willChange = 'clip-path';
    console.log('add will-change');

    modal.style.cssText='-webkit-clip-path: polygon(0 0, 100% 0%, 100% 100%, 0% 100%);clip-path: polygon(0 0, 100% 0%, 100% 100%, 0% 100%);'
    document.getElementById('modal__content-read').style.cssText='opacity: 1;-webkit-transform: translate3D(0, 1em, 0);transform: translate3D(0, 1em, 0);transition: opacity 0.3s 0.2s, -webkit-transform 0.6s 0.2s cubic-bezier(0, 0.65, 0.06, 0.98);transition: opacity 0.3s 0.2s, transform 0.6s 0.2s cubic-bezier(0, 0.65, 0.06, 0.98);transition: opacity 0.3s 0.2s, transform 0.6s 0.2s cubic-bezier(0, 0.65, 0.06, 0.98), -webkit-transform 0.6s 0.2s cubic-bezier(0, 0.65, 0.06, 0.98);'

    document.getElementById('overlay').style.cssText='display: block';
}

function removeHint() {
	modal = document.getElementById('modal-read');

    modal.style.willChange = 'auto';
    console.log('remove will-change');

    modal.style.cssText='-webkit-clip-path: polygon(calc(50% - 0em) calc(50% - 0em), calc(50% + 0em) calc(50% - 0em), calc(50% + 0em) calc(50% + 0em), calc(50% - 0em) calc( 50% + 0em));clip-path: polygon(calc(50% - 0em) calc(50% - 0em), calc(50% + 0em) calc(50% - 0em), calc(50% + 0em) calc(50% + 0em), calc(50% - 0em) calc( 50% + 0em));'
    document.getElementById('modal__content-read').style.cssText='opacity: 0;-webkit-transform: translate3D(0, -1em, 0);transform: translate3D(0, -1em, 0);transition: opacity 0.1s 0s, -webkit-transform 0.3s 0s;transition: opacity 0.1s 0s, transform 0.3s 0s;transition: opacity 0.1s 0s, transform 0.3s 0s, -webkit-transform 0.3s 0s;'

    document.getElementById('overlay').style.cssText='display: none';
}

