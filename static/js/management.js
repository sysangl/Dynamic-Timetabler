itemFormContainer = document.getElementById('item-forms');
filters = {dateRangeFrom:null, dateRangeTo:null};
currentItemClass = document.getElementById('item-select').value.toLowerCase();
filterForm =document.getElementById('filter-form');
itemForms = itemFormContainer.getElementsByClassName('item-form');
// for (const form of itemForms) {
//     form.addEventListener('submit',async (e) => {
//         e.preventDefault();
//         form.submit();
//     })
// }
editFormOpen = false


filterForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(filterForm);
    const drf = formData.get('filter_date_from');
    const drt = formData.get('filter_date_to');

    filters.dateRangeFrom = drf;
    filters.dateRangeTo = drt;

    const ti = await fetchTimetableItems();
    generateItemTable(currentItemClass, timetableItems=ti);
});

filterForm.addEventListener('reset', async (e) => {
    filters.dateRangeFrom = null;
    filters.dateRangeTo = null;

    const ti = await fetchTimetableItems();
    generateItemTable(currentItemClass, timetableItems=ti);
});



function toggleForms(editMode=false) {
    document.getElementById('backdrop').classList.toggle('hidden')
    document.getElementById('item-forms').classList.toggle('hidden')
    for (const container of document.getElementById('item-forms').children)  {
        if (container.id != `${currentItemClass}-form-container`){
            container.classList.add('hidden')
        } else {
            container.classList.remove('hidden')
        }
    }
    setupItemForm(editMode);
}

async function fetchTimetableItems() {
    dateRangeFrom = filters.dateRangeFrom;
    dateRangeTo = filters.dateRangeTo;
    var url = '/api/timetable'
    if (dateRangeFrom || dateRangeTo) {
        url += '/range/?'
        if (dateRangeFrom) {
            url+=`from=${dateRangeFrom}&`
        } 
        if (dateRangeTo) {
            url+=`until=${dateRangeTo}`
        }
    }

    const response = await fetch(url, {
        method : 'GET'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }
    return await response.json()
}

async function generateItemTable(selectedItem='all', timetableItems = null) {
    timetableItems = timetableItems || await fetchTimetableItems()
    const itemTable = document.getElementById('item-table-body')
    itemTable.innerHTML = "";
    const tableTitle = document.getElementById('item-table-title')
    tableTitle.textContent = toUpper(selectedItem)
    let itemCount = 0

    for (const [itemType, items] of Object.entries(timetableItems)) {
        if ((selectedItem != itemType) && (selectedItem != 'all')) {
            continue
        }
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
            itemTypeText.textContent = itemType.slice(0,-1).toLocaleUpperCase()
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
    document.getElementById('item-counter').textContent = itemCount;
}

/**
 * 
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


function changeTable(selectedItem) {
    if (selectedItem == 'all') {
        document.getElementById('create-new-btn').disabled = true
    } else {
        document.getElementById('create-new-btn').disabled = false
    }
    currentItemClass = selectedItem
    generateItemTable(selectedItem = selectedItem)
}

async function setupManagement () {
    let settings = await fetchSettings()
    const now = new Date();
    const future = new Date(now.getTime() + settings.default_block_length * 60 * 1000);

    const sDate = now.toISOString().split('T')[0];
    const eDate = future.toISOString().split('T')[0];

    const sHours   = String(now.getHours()).padStart(2, '0');
    const sMinutes = String(now.getMinutes()).padStart(2, '0');
    const sTime = `${sHours}:${sMinutes}`;  

    const eHours   = String(future.getHours()).padStart(2, '0');
    const eMinutes = String(future.getMinutes()).padStart(2, '0');
    const eTime = `${eHours}:${eMinutes}`;  

    document.getElementById('sdate').value = sDate;
    document.getElementById('edate').value = eDate;

    document.getElementById('stime').value = sTime;
    document.getElementById('etime').value = eTime;

    document.getElementById('filter-date-from').value = sDate;
    document.getElementById('filter-date-to').value = sDate;

    generateItemTable();
}

async function setupItemForm(editMode) {
    let settings = await fetchSettings()
    const now = new Date();
    const future = new Date(now.getTime() + settings.default_block_length * 60 * 1000);

    const sDate = now.toISOString().split('T')[0];
    const eDate = future.toISOString().split('T')[0];

    const sHours   = String(now.getHours()).padStart(2, '0');
    const sMinutes = String(now.getMinutes()).padStart(2, '0');
    const sTime = `${sHours}:${sMinutes}`;  

    const eHours   = String(future.getHours()).padStart(2, '0');
    const eMinutes = String(future.getMinutes()).padStart(2, '0');
    const eTime = `${eHours}:${eMinutes}`;  
    if (editMode) {
        document.getElementById(`${currentItemClass}-form`).getElementsByClassName('submit-button')[0].textContent = 'Update'
    } else {
        document.getElementById(`${currentItemClass}-form`).getElementsByClassName('submit-button')[0].textContent = 'Create'
    }
    switch (currentItemClass.toLowerCase()) {
        case 'blocks':
            $(`#${currentItemClass.toLowerCase()}-form #title`)[0].value = '';
            $(`#${currentItemClass.toLowerCase()}-form #description`)[0].value = '';
            $(`#${currentItemClass.toLowerCase()}-form #sdate`)[0].value = sDate;
            $(`#${currentItemClass.toLowerCase()}-form #edate`)[0].value = eDate;
            $(`#${currentItemClass.toLowerCase()}-form #stime`)[0].value = sTime;
            $(`#${currentItemClass.toLowerCase()}-form #etime`)[0].value = eTime;
            $(`#${currentItemClass.toLowerCase()}-form #colour`)[0].value = settings.default_block_colour;
            break;
    
        default:
            break;
    }


}

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

setupManagement();
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !itemFormContainer.classList.contains('hidden')) {
        toggleForms();
    }
});