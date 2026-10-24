itemForms = document.getElementById('item-forms');
filters = {dateRangeFrom:null, dateRangeTo:null};
currentItemClass = 'all';
filterForm =document.getElementById('filter-form');

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



function toggleForms() {
    document.getElementById('backdrop').classList.toggle('hidden')
    itemForms.classList.toggle('hidden')
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

            row.append(itemTypeText, itemTitleText, itemStart, itemEnd, itemStatus)
            itemTable.append(row)
            itemCount += 1
        }
    }
    document.getElementById('item-counter').textContent = itemCount;
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

    generateItemTable();
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
    if (e.key === 'Escape' && !itemForms.classList.contains('hidden')) {
        toggleForms();
    }
});