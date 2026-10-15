
async function createBlock() {
    try {
        console.log("Attempting to create a block")

        const sdate = document.getElementById('block-sdate-input').value.split('-');
        const stime = document.getElementById('block-stime-input').value.split(':');
        const edate = document.getElementById('block-edate-input').value.split('-');
        const etime = document.getElementById('block-etime-input').value.split(':');
        var options_data = {};
        options_data.title = $('#block-title-input').value;
        options_data.description = $('#block-description-input').value;
        options_data.start_dattime = {
            'year' : sdate[0],
            'month' : sdate[1],
            'day' : sdate[2],
            'hour' : stime[0],
            'minutes' : stime[1]
        };
        options_data.end_datetime = {
            'year' : edate[0],
            'month' : edate[1],
            'day' : edate[2],
            'hour' : etime[0],
            'minutes' : etime[1]
        };
        options_data.colour = $('#block-colour-input').value;

        console.log('sending data')
        console.log(options_data);

        const response = await fetch('/server/timetable/blocks/create', {
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
    } catch (err) {
        console.error('Failed to create block: ', err);
        throw err;
    }
}

function initManagement() {
    $("#block-sdate-input")
    $("management-save-button").addEventListener('onclick', () => {
        createBlock();
    })
}