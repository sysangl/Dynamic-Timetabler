
/**
 * Applies settings
 * @param {Object} settings 
 */
async function applySettings(settings) {
    console.log('setting option values')
    console.log(settings);
    populateSettings(settings);
}

/**
 * Fills the settings form with the current user's settings
 * @param {Object} settings 
 */
function populateSettings(settings) {
    const formElements = $('#settings-form input:not(:disabled)');
    formElements.each(function(index, element) {
        // const $element = $(element);
        if (element.id == 'settings-save-button') return;
        if (element.type == 'radio') {
            if (element.value == settings[element.name]) {
                element.checked = true;
            }
        } else {
            element.value = settings[element.name]
        }
    })
}

/**
 * Initialise settings (run on fragment load.)
 */
async function initSettings() {
    console.log("initialising settings")
    await applySettings(await fetchSettings());

    const form = document.getElementById('settings-form');
    form.addEventListener('submit', (e)=>{
        e.preventDefault();
        console.log((new FormData(form)).get('timetable_view'))
        form.submit()
    })
}

initSettings();
