/**
 * Capitalises the first letter of every word
 * 
 * @param {string} str 
 * @returns 
 */
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

/**
 * Clamps a number
 * @param {number} value 
 * @param {number} min 
 * @param {number} max 
 * @returns {number}
 */
function clamp(value, min, max) {
    return Math.max(Math.min(value,max), min)
}