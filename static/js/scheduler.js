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
            generateItemTable();
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
async function generateItemTable(timetableItems = null) {
    timetableItems = await fetchTimetableItems()
    const itemTable = document.getElementById('item-table-body')
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
    document.getElementById('item-counter').textContent = itemCount;
}

/**
 * Edits an item.
 * item is a string of the form, 'itemType-id'
 * eg. 'block-5', 'routine-9'
 * @param {string} item
 */
async function editItem(item) {
    const itemInfo = item.split('-')
    const itemType = itemInfo[0]
    const itemId = itemInfo[1]

    const form = document.getElementById(`${itemType}-form`);
    toggleForms(editMode=true);
    populateItemForm(itemType, itemId)
    form.addEventListener('submit', async function editFormSubmit(e) {
        e.preventDefault();
        console.log(e)
        const formData = new FormData(form);
        var object = {};
        formData.forEach((value, key) => object[key] = value);
        const response = await fetch(`/api/timetable/${itemType}/${itemId}`, {
            method: 'PUT',
            headers: {
                'Content-Type' : 'application/json'
            },
            body: JSON.stringify(object)
        })
        if (!response.ok) {
            console.log(`Failed to update ${itemType} with id: ${itemId}`)
        }
        form.removeEventListener('submit', editFormSubmit)
        editFormOpen = false
        toggleForms();
        generateItemTable();
    })
    editFormOpen = true;
}

/**
 * Populates the item creation/update form
 * @param {string} itemType 
 * @param {Number|string} id 
 */
async function populateItemForm(itemType,id) {
    const formElements = $(`#${itemType}-form input:not(:disabled)`);

    const response = await fetch(`/api/timetable/${itemType}/${id}`, {
        method : 'GET'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }

    const itemData = await response.json()

    formElements.each(function(index, element) {
        // const $element = $(element);
        if (element.classList.contains('form-btn')) return;
        if (element.type == 'radio') {
            if (element.value == itemData[element.name]) {
                element.checked = true;
            }
        } else {
            element.value = itemData[element.name]
        }
    })
}



async function setupManagement () {
    let settings = await fetchSettings()
    generateItemTable();
}

/**
 * Uses bubble-sort to sort the table by the selected column
 * @param {Number} column 
 */
function sortTable(column) {
    const table = document.getElementById('item-table')
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
    var url = '/api/engine/generate/0'
    const response = await fetch(url, {
        method : 'POST'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }
    return await response.json()
}

setupManagement();
// close forms when Esc is pressed
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !itemFormContainer.classList.contains('hidden')) {
        toggleForms();
    }
});