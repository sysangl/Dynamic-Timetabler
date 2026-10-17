
async function createBlock() {
    console.log("Attempting to create a block")
    const sdate = document.getElementById('block-sdate-input').value.split('-');
    const stime = document.getElementById('block-stime-input').value.split(':');
    const edate = document.getElementById('block-edate-input').value.split('-');
    const etime = document.getElementById('block-etime-input').value.split(':');
    var options_data = {};
    options_data.title = document.getElementById('block-title-input').value;
    options_data.description = document.getElementById('block-description-input').value;
    options_data.start_datetime = {
        'year' : Number(sdate[0]),
        'month' : Number(sdate[1]),
        'day' : Number(sdate[2]),
        'hour' : Number(stime[0]),
        'minute' : Number(stime[1])
    };
    options_data.end_datetime = {
        'year' : Number(edate[0]),
        'month' : Number(edate[1]),
        'day' : Number(edate[2]),
        'hour' : Number(etime[0]),
        'minute' : Number(etime[1])
    };
    options_data.colour = document.getElementById('block-colour-input').value;

    console.log('sending data')
    console.log(options_data);

    const response = await fetch('/api/timetable/blocks/create', {
        method: 'POST',
        headers: {
            'Content-Type' : 'application/json'
        },
        body: JSON.stringify(options_data)
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status} - ${response.statusText}`);
    }

    const data = await response.json()
    console.log(data)
    // try {
    // } catch (err) {
    //     console.error('Failed to create block: ', err);
    //     throw err;
    // }
}

function initManagement() {

}