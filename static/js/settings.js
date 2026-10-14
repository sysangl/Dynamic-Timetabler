// takes the settings from the settings page and sends the values to the server to update
// TODO: need to only send values that have been altered
async function saveSettings() {
    try {
        console.log("Attempting to update settings")

        const settings_options = document.getElementsByClassName("settings-option");
        var options_data = {};
        for (let option of settings_options) {
            options_data[option.getAttribute("data-optionName")] = option.value;
        }

        console.log(options_data);

        const response = await fetch(settingsUrl+"/update", {
            method: 'POST',
            headers: {
                'Content-Type' : 'application/json',
                'Accept' : 'application/json'
            },
            body: JSON.stringify(options_data)
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status} - ${response.statusText}`);
        }


        const data = await response.json();

        applySettings(data["settings"]);
        
        persistentSettings = null;
    } catch (err) {
        console.error('Failed to update settings: ', err);
        throw err;
    }
}

// apply settings to timetable. need to automatically parse and apply these settings
async function applySettings(settings = null) {
    if (!settings) settings = await fetchSettings();
    console.log(settings)
    document.getElementById('starting-day-input').value = settings['starting_day'];
    document.getElementById('starting-hour-input').value = settings['starting_hour'];
}

async function initSettings() {
    console.log("initialising settings")
    await applySettings();
}
initSettings();

// window.pageInits = window.pageInits || {};
// window.pageInits.settings = initSettings;