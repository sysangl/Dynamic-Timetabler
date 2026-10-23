function toUpper(str) {
    return str
        .toLowerCase()
        .split(' ')
        .map(function(word) {
            return word[0].toUpperCase() + word.substr(1);
        })
        .join(' ');
}

const pressedKeys = {}
document.addEventListener('keydown', handleKeyDown);
document.addEventListener('keyup', handleKeyUp)
function handleKeyDown(event) {
    if (!event.repeat) {
        pressedKeys[event.key] = true; 
    }
}
function handleKeyUp(event) {
    delete pressedKeys[event.key];
}

function getPressedKeys() {
    return Object.keys(pressedKeys).filter(key => pressedKeys[key]);
}