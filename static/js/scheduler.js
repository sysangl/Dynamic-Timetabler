itemFormContainer = document.getElementById('item-forms');
itemForms = itemFormContainer.getElementsByClassName('item-form');
editFormOpen = false
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
for (const form of itemForms) {
    form.addEventListener('submit',async (e) => {
        e.preventDefault();

        const formData = new FormData(form)
        var object = {};
        formData.forEach((value, key) => object[key] = value);
        fetch(form.action, {
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
            form.reset();
            generateActivityTable();
            toggleForms();
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('form-error-messages').textContent = 'Item creation failed. Please try again.';
        });
    })
}

/**
 * Toggle the item form containers.
 * If editMode is set to true, the 'Create' button is changed to 'Update'
 * @param {Boolean} editMode 
 */
function toggleForms(editMode=false) {
    document.getElementById('backdrop').classList.toggle('hidden')
    document.getElementById('item-forms').classList.toggle('hidden')
    console.log(`activities-form-container`)
    for (const container of document.getElementById('item-forms').children)  {
        console.log(container.id)
        if (container.id != `activities-form-container`){
            container.classList.add('hidden')
        } else {
            container.classList.remove('hidden')
        }
    }
}

/**
 * Gets the timetable items, with filters applied (if any).
 * @returns {Promise<any>}
 */
async function fetchTimetableItems() {

    var url = '/api/timetable'
    const response = await fetch(url, {
        method : 'GET'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }
    return await response.json()
}

/**
 * Generates and populates the item table
 * timetableItems is what items to use, defaults to grabbing the item from the server
 * @param {JSON} timetableItems 
 */
async function generateActivityTable(timetableItems = null) {
    timetableItems = await fetchTimetableItems()
    const itemTable = document.getElementById('activity-table-body')
    itemTable.innerHTML = "";
    let itemCount = 0

    for (const [itemType, items] of Object.entries(timetableItems)) {
        if ('activities' != itemType) {
            continue
        }
        if (itemType == 'status') continue;
        for (const item of items) {
            const row = document.createElement('tr');
            row.onclick = (e) => {
                if (!getPressedKeys().includes('Control')) {
                    const selectedElements = document.getElementsByClassName('selected');
                    for (let index = 0; index < selectedElements.length; index++) {
                        const element = selectedElements[index];
                        if (element != row) {
                            element.classList.remove('selected')
                        }
                    }
                    
                }
                row.classList.toggle('selected')
            };
            row.id = `${itemType}-${item.id}`
            const nameText = document.createElement('td')
            nameText.textContent = item.name
            const priorityText = document.createElement('td')
            priorityText.textContent = item.title
            
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
 * Generates and populates the item table
 * selectedItem is the item class to generate, defaults to the selected item in the dropdown
 * timetableItems is what items to use, defaults to grabbing the item from the server
 * @param {string} selectedItem 
 * @param {JSON} timetableItems 
 */
async function generateBlockTable(timetableItems = null) {
    selectedItem = 'blocks'
    timetableItems = timetableItems || await fetchTimetableItems()
    const itemTable = document.getElementById('block-table-body')
    itemTable.innerHTML = "";
    let itemCount = 0

    for (const [itemType, items] of Object.entries(timetableItems)) {
        if ((selectedItem != itemType) && (selectedItem != 'all')) {
            continue
        }
        if (itemType == 'status') continue;
        for (const item of items) {
            const row = document.createElement('tr');
            row.onclick = (e) => {
                if (!getPressedKeys().includes('Control')) {
                    const selectedElements = document.getElementsByClassName('selected');
                    for (let index = 0; index < selectedElements.length; index++) {
                        const element = selectedElements[index];
                        if (element != row) {
                            element.classList.remove('selected')
                        }
                    }
                    
                }
                row.classList.toggle('selected')
            };
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
    generateActivityTable();
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

async function generateTimetable() {
    var url = '/api/engine/generate/default'
    const response = await fetch(url, {
        method : 'POST'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }

    blocks = await response.json()

    console.log(blocks)
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