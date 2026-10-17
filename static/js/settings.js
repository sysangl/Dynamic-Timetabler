
// apply settings to timetable. need to automatically parse and apply these settings
async function applySettings(settings) {
    console.log('setting option values')
    console.log(settings);
    populateSettings(settings);
}

function populateSettings(settings) {
    const formElements = $('#settings-form input:not(:disabled)');
    formElements.each(function(index, element) {
        // const $element = $(element);
        if (element.id == 'settings-save-button') return;
        element.value = settings[element.name]
    })
}

async function initSettings() {
    console.log("initialising settings")
    await applySettings(await fetchSettings());
}
initSettings();

// window.pageInits = window.pageInits || {};
// window.pageInits.settings = initSettings;