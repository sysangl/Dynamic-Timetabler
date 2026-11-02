itemFormContainer = document.getElementById('item-forms');
itemForms = itemFormContainer.getElementsByClassName('item-form');
editFormOpen = false
currentScheduleId = null

function plural_to_single(item) {
    words = {
        'activities':'activity'
    }

    if (!words[item]){
        return item.slice(0,-1)
    }
    return words[item]
}

/**
 * Stop the default behaviour of forms of reloading the page
 */
sform = document.getElementById('schedules-form')
sform.addEventListener('submit',async (e) => {
    e.preventDefault();

    const formData = new FormData(sform)
    var object = {};
    formData.forEach((value, key) => {
            object[key] = value}
    );
    fetch(`/api/schedules/create`, {
        method: 'POST',
        headers: {
        'Content-Type': 'application/json',
        },
        body: JSON.stringify(object)
    })
    .then(response => {
        if (!response.ok) {
        throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Success:', data);
        sform.reset();
        generateActivityTable(data.id);
        generateBlockTable(data.id)
        currentScheduleId = data.id
        toggleForms();
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('form-error-messages').textContent = 'Item creation failed. Please try again.';
    });
})



aform = document.getElementById('activities-form')
aform.addEventListener('submit',async (e) => {
    e.preventDefault();

    const formData = new FormData(aform)
    var object = {};
    formData.forEach((value, key) => {
        if (key=='even_frequency_spacing') {
            object[key] = document.getElementById(key).checked
        } else {
            object[key] = value}
        }
    );
    fetch(`/api/schedules/${currentScheduleId}/activites/create`, {
        method: 'POST',
        headers: {
        'Content-Type': 'application/json',
        },
        body: JSON.stringify(object)
    })
    .then(response => {
        if (!response.ok) {
        throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Success:', data);
        aform.reset();
        generateActivityTable();
        toggleForms();
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('form-error-messages').textContent = 'Item creation failed. Please try again.';
    });
})

function setActiveSchedule(id) {
    enableTables()
    generateBlockTable(id)
    generateActivityTable(id)
}

/**
 * Toggle the item form containers.
 * If editMode is set to true, the 'Create' button is changed to 'Update'
 * @param {Boolean} editMode 
 */
function toggleForms(item='activities') {
    document.getElementById('backdrop').classList.toggle('hidden')
    document.getElementById('item-forms').classList.toggle('hidden')
    for (const container of document.getElementById('item-forms').children)  {
        if (container.id != `${item}-form-container`){
            container.classList.add('hidden')
        } else {
            container.classList.remove('hidden')
        }
    }
    document.getElementById('form-error-messages').textContent=''
}

async function fetchScheduleBlocks(id) {
    var url = `/api/schedules/${id}/blocks`
    const response = await fetch(url, {
        method : 'GET'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }
    blocks = await response.json()
    return blocks
}


/**
 * Generates and populates the schedule table
 */
async function generateScheduleTable() {
    var url = `/api/schedules`
    const response = await fetch(url, {
        method : 'GET'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }
    schedules = await response.json()

    const itemTable = document.getElementById('schedule-table-body')
    itemTable.innerHTML = "";
    let itemCount = 0

    for (const [itemType, items] of Object.entries(schedules)) {
        if ('schedules' != itemType) {
            continue
        }
        if (itemType == 'status') continue;
        for (const item of items) {
            const row = document.createElement('tr');

            row.onclick = (e) => {
                setActiveSchedule(item.id)
            }

            row.id = `${itemType}-${item.id}`
            const nameText = document.createElement('td')
            nameText.textContent = item.title
            const groupText = document.createElement('td')
            groupText.textContent = item.group_name


            const startDateText = document.createElement('td')
            startDateText.textContent = item.start_date
            
            const sizeText = document.createElement('td')
            sizeText.textContent = item.length

            const slotSizeText = document.createElement('td')
            slotSizeText.textContent = item.slot_size


            
            row.ondblclick = ()=>{editItem(row.id)}
            row.append(nameText, groupText, startDateText, sizeText, slotSizeText)
            itemTable.append(row)
            itemCount += 1
        }
    }
    document.getElementById('schedule-counter').textContent = itemCount;
}


/**
 * Generates and populates the activity table
 */
async function generateActivityTable(id) {
    var url = `/api/schedules/${id}/activities`
    const response = await fetch(url, {
        method : 'GET'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }
    activities = await response.json()

    const itemTable = document.getElementById('activity-table-body')
    itemTable.innerHTML = "";
    let itemCount = 0

    for (const [itemType, items] of Object.entries(activities)) {
        if ('activities' != itemType) {
            continue
        }
        if (itemType == 'status') continue;
        for (const item of items) {
            const row = document.createElement('tr');
            row.id = `${itemType}-${item.id}`
            const nameText = document.createElement('td')
            nameText.textContent = item.title
            const priorityText = document.createElement('td')
            priorityText.textContent = item.priority
            
            const frequencyText = document.createElement('td')
            frequencyText.textContent = item.frequency

            const minTimeText = document.createElement('td')
            minTimeText.textContent = item.min_time
            const maxLengthText = document.createElement('td')
            maxLengthText.textContent = item.max_length
            
            row.ondblclick = ()=>{editItem(row.id)}
            row.append(nameText, priorityText, frequencyText, minTimeText, maxLengthText)
            itemTable.append(row)
            itemCount += 1
        }
    }
    document.getElementById('activity-counter').textContent = itemCount;
}



/**
 * Generates and populates the blocks table
 */
async function generateBlockTable() {
    var url = `/api/schedules/${id}/blocks`
    const response = await fetch(url, {
        method : 'GET'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }
    blocks = await response.json()

    const itemTable = document.getElementById('block-table-body')
    itemTable.innerHTML = "";
    let itemCount = 0

    for (const [itemType, items] of Object.entries(blocks)) {
        if (itemType == 'status') continue;
        for (const item of items) {
            const row = document.createElement('tr');
            row.id = `${itemType}-${item.id}`
            const itemTypeText = document.createElement('td')
            itemTypeText.textContent = plural_to_single(itemType).toLocaleUpperCase()
            const itemTitleText = document.createElement('td')
            const itemColour = document.createElement('span')
            itemColour.classList.add('fa-solid', 'fa-circle')
            itemColour.style.color = item.colour
            itemColour.style.marginRight = '5px';
            itemTitleText.append(itemColour)

            itemTitleText.innerHTML += item.title
            const itemStart = document.createElement('td')
            const startDateTime = new Date(item.start_datetime)
            const sDate = document.createElement('p')
            sDate.textContent = startDateTime.toLocaleDateString()
            const sTime = document.createElement('p')
            sTime.textContent = startDateTime.toLocaleTimeString().replace(':00 ',' ')
            itemStart.append(sDate,sTime)

            const itemEnd = document.createElement('td')
            const endDateTime = new Date(item.end_datetime)
            const eDate = document.createElement('p')
            eDate.textContent = endDateTime.toLocaleDateString()
            const eTime = document.createElement('p')
            eTime.textContent = endDateTime.toLocaleTimeString().replace(':00 ',' ')
            itemEnd.append(eDate,eTime)

            const itemStatus = document.createElement('td')
            itemStatus.textContent = 'Uncompleted'
            
            row.ondblclick = ()=>{editItem(row.id)}
            row.append(itemTypeText, itemTitleText, itemStart, itemEnd, itemStatus)
            itemTable.append(row)
            itemCount += 1
        }
    }
    document.getElementById('block-counter').textContent = itemCount;
}



async function setupScheduler () {
    let settings = await fetchSettings()
    if (currentScheduleId) {
        generateActivityTable();
        var url = `/api/schedules/${currentScheduleId}/blocks`
        const response = await fetch(url, {
            method : 'GET'
        });

        if (!response.ok) {
            throw new Error(`${response.status} ${response.statusText}`)
        }
        blocks = await response.json()
        generateBlockTable(blocks);
    }

    disableTables();
}

function enableTables() {
    document.getElementById('activity-container').classList.remove('disabled')
    document.getElementById('block-container').classList.remove('disabled')
}

function disableTables() {
    document.getElementById('activity-container').classList.add('disabled')
    document.getElementById('block-container').classList.add('disabled')
}
async function deleteScheduleBlocks(id) {
    var url = `/api/schedules/${id}/blocks`
    const response = await fetch(url, {
        method : 'DELETE'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }

    generateBlockTable(fetchScheduleBlocks());
}


/**
 * Uses bubble-sort to sort the table by the selected column
 * @param {Number} column 
 */
function sortTable(column, item='block') {
    const table = document.getElementById(`${item}-table`)
    var switching = true;
    var shouldSwitch = false;
    var switchCount = 0;
    var sortDirection = 'asc';
    while (switching) {
        switching = false;
        const rows = table.rows;
        for (var i=1; i < (rows.length -1); i++) {
            shouldSwitch = false;
            current = rows[i].getElementsByTagName('td')[column];
            next = rows[i+1].getElementsByTagName('td')[column]
            if (sortDirection == 'asc'){
                if (current.textContent.toLowerCase() > next.textContent.toLowerCase()) {
                    shouldSwitch = true;
                    break;
                }
            } else if (sortDirection == 'desc') {
                if (current.textContent.toLowerCase() < next.textContent.toLowerCase()) {
                    shouldSwitch = true;
                    break;
                }
            }
        }
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i+1], rows[i]);
            switching = true;
            switchCount ++;
        } else {
            if (switchCount==0 && sortDirection == 'asc') {
                sortDirection = 'desc';
                switching = true;
            }
        }
    }
    const tableArrows = document.getElementsByClassName('table-sort-arrows');
    for (let index = 0; index < tableArrows.length; index++) {
        const element = tableArrows[index];
        element.classList.remove('fa-sort');
        element.classList.remove('fa-sort-asc');
        element.classList.remove('fa-sort-desc');
        if (index != column) {
            element.classList.add('fa-sort');
        }
        document.getElementsByClassName('table-sort-arrows')[column].classList.add(`fa-sort-${sortDirection}`)   
    }
}

async function generateSchedule() {
    var url = '/api/engine/generate/default'
    const response = await fetch(url, {
        method : 'POST'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }

    blocks = await response.json()

    generateBlockTable()

    return blocks
}

async function annealTimetable() {
    const backdrop = document.getElementById('loading-backdrop')

    backdrop.classList.remove('hidden')
    var url = '/api/engine/anneal/default'
    const response = await fetch(url, {
        method : 'POST'
    });

    if (!response.ok) {
        backdrop.innerHTML += "SOMETHING WENT WRONG, PLEASE CHECK CANOPY CONSOLE"
        throw new Error(`${response.status} ${response.statusText}`)
    }

    blocks = await response.json()
    backdrop.classList.add('hidden')
    generateBlockTable(blocks)

    return blocks
}


setupScheduler();
// close forms when Esc is pressed
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !itemFormContainer.classList.contains('hidden')) {
        toggleForms();
    }
});